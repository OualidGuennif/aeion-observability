#!/usr/bin/env python3
"""Qualify one pinned forum feature build offline, then read its trace back from Langfuse.

The base is the real forum tree at the commit named by the target profile. The builder
is an injected fake model, not a paid call: it writes the feature's Java filter and a
candidate test. The protected check is the real Gradle test command, with the contract
test copied in from outside the candidate tree. The two review votes are injected fake
answers as well; the fake forge records a PR shape and never contacts GitHub.

Nothing is published, deployed or paid for. Run it with the controller venv:

    demo/.local/venv/bin/python demo/tests/qualify_forum_build.py
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent
REPO = DEMO.parent
sys.path.insert(0, str(DEMO))
from factory.budget import DailyBudget
from factory.dispatch import DispatchWorker
from factory.manifest import load_manifest
from factory.publish import FakeForge
from factory.store import SIMULATED_COMPLETE, Store
from factory.target import load_target
from factory.telemetry import FactoryTelemetry

FILTER = """package local.aeion.forum;

import jakarta.annotation.Priority;
import jakarta.ws.rs.Priorities;
import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerResponseContext;
import jakarta.ws.rs.container.ContainerResponseFilter;
import jakarta.ws.rs.ext.Provider;

/** Feature 013: every forum response carries an enforcing, non-report-only policy. */
@Provider
@Priority(Priorities.HEADER_DECORATOR)
public class SecurityHeadersFilter implements ContainerResponseFilter {

    static final String CSP =
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";

    @Override
    public void filter(ContainerRequestContext request, ContainerResponseContext response) {
        var headers = response.getHeaders();
        headers.putSingle("Content-Security-Policy", CSP);
        headers.putSingle("X-Content-Type-Options", "nosniff");
        headers.putSingle("Referrer-Policy", "no-referrer");
        headers.putSingle("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
        headers.putSingle("X-Frame-Options", "DENY");
        headers.remove("Content-Security-Policy-Report-Only");
    }
}
"""

TEST = """package local.aeion.forum;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.nullValue;

import io.quarkus.test.common.WithTestResource;
import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

@QuarkusTest
@WithTestResource(QuarkusTestDatabase.class)
class SecurityHeadersTest {

    @Test
    void healthCarriesTheEnforcingPolicy() {
        given()
                .when().get("/healthz")
                .then().statusCode(200)
                .header("Content-Security-Policy", containsString("default-src 'none'"))
                .header("Content-Security-Policy-Report-Only", nullValue())
                .header("X-Content-Type-Options", "nosniff")
                .header("Referrer-Policy", "no-referrer");
    }
}
"""


def build_feature(repo, frozen, feature, brief):
    """The injected fake model: deterministic Java, no network, no paid call."""
    main = repo / frozen.write_scopes[0]
    test = repo / frozen.write_scopes[1]
    main.mkdir(parents=True, exist_ok=True)
    test.mkdir(parents=True, exist_ok=True)
    (main / "SecurityHeadersFilter.java").write_text(FILTER)
    (test / "SecurityHeadersTest.java").write_text(TEST)
    if feature["id"] != "013" or "security headers" not in brief.read_text().lower():
        raise RuntimeError("brief_does_not_name_this_feature")


def fake_reviewer(model, prompt):
    """Two independent fake votes; the receipt marks the whole attempt simulated."""
    return {"verdict": "approve", "reason": "offline injected reviewer"}


def readback(trace_id, expected, timeout_seconds=25):
    values = dict(line.split("=", 1) for line in
                  (DEMO / ".local/stack.env").read_text().splitlines() if "=" in line)
    auth = values.get("LANGFUSE_AUTH")
    if not auth:
        raise SystemExit("readback: LANGFUSE_AUTH is missing from the stack configuration")
    url = "http://127.0.0.1:3300/api/public/v2/observations?" + urllib.parse.urlencode(
        {"traceId": trace_id, "fields": "basic,metadata", "limit": 50})
    deadline = time.monotonic() + timeout_seconds
    while True:
        request = urllib.request.Request(url, headers={"Authorization": "Basic " + auth})
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.load(response)["data"]
        rows = [row for row in data if row.get("name") == "factory.build"]
        if rows:
            row = rows[0]
            metadata = row.get("metadata") or {}
            checks = {
                "build": metadata.get("attributes.aeion.build.id") == expected["build_id"],
                "feature": metadata.get("attributes.aeion.feature.id") == expected["feature_id"],
                "attempt": metadata.get("attributes.aeion.attempt.id") == expected["attempt_id"],
                "artifact": metadata.get("attributes.aeion.artifact.digest") == expected["artifact_digest"],
                "session": row.get("sessionId") == expected["session_id"],
            }
            if not all(checks.values()):
                raise SystemExit("readback: Langfuse metadata differs: " + json.dumps(checks))
            return {"status": "PASS", "trace_id": row["traceId"], "observation": row["id"],
                    "checks": checks}
        if time.monotonic() >= deadline:
            raise SystemExit("readback: factory.build did not arrive in Langfuse")
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=str(REPO / "demo/forum/targets/forum-app-013.json"))
    parser.add_argument("--state", default=str(DEMO / ".local/factory"))
    parser.add_argument("--no-telemetry", action="store_true")
    args = parser.parse_args()

    target = load_target(args.target, REPO)
    catalog = load_manifest(REPO / "demo/forum/features/MANIFEST.json")
    if catalog.by_id[target.feature_id]["title"] != "Security headers and CSP":
        raise SystemExit("target feature is not 013")
    state = Path(args.state)
    state.mkdir(parents=True, exist_ok=True)
    # The demo's 001 skeleton is already present in the runnable app. The qualification
    # store treats a completed simulated dependency as satisfied; the build itself is real.
    store = Store(state / "factory.db", simulated_dependencies=True)
    admitted = store.admit([target.feature_id], "forum-013-" + uuid.uuid4().hex, catalog)
    if admitted["status"] != "admitted":
        raise SystemExit("admit failed: " + json.dumps(admitted))
    telemetry = None if args.no_telemetry else FactoryTelemetry()
    worker = DispatchWorker(
        store, catalog, REPO / "demo/forum/features", state / "work",
        config={"profile": "offline-injected", "mode": "fake", "deadline_ns": 3_600_000_000_000,
                "step_cap": 200, "context_limit": 250_000, "cost_reservation_usd": "0.00"},
        target=target, builder=build_feature, telemetry=telemetry, forge=FakeForge(),
        review_complete=fake_reviewer, require_circuit=True,
        author_model="deepseek-4.1-flash",
        budget=DailyBudget(state / "budget" / "ledger.jsonl"),
    )
    result = worker.run_once()
    if result is None:
        raise SystemExit("no build was claimed")
    build = next(row for row in store.board() if row["build_id"] == result["build_id"])
    receipt = json.loads(build["receipt"] or "{}")
    if build["status"] != SIMULATED_COMPLETE:
        raise SystemExit("build did not complete: " + json.dumps(
            {"status": build["status"], "hold": build.get("hold_reason"),
             "receipt": receipt}, indent=2)[:4000])
    check = receipt["gate"]["results"]["gradle_test"]
    if check["status"] != "passed":
        raise SystemExit("protected Gradle check failed: " + json.dumps(check)[:2000])
    if receipt["circuit"]["status"] != "approved":
        raise SystemExit("review circuit did not approve")
    if receipt["publisher"]["decision"] != "published":
        raise SystemExit("fake publisher did not publish: " + json.dumps(receipt["publisher"])[:1000])

    evidence = {
        "status": "completed",
        "build_id": receipt["build_id"],
        "feature_id": receipt["feature_id"],
        "attempt_id": receipt["attempt_id"],
        "artifact_digest": receipt["artifact_digest"],
        "base_sha": receipt["base_sha"],
        "gate": receipt["gate"]["status"],
        "check": {"id": check["detail"]["check"], "returncode": check["detail"]["returncode"],
                  "duration_ms": check["detail"]["duration_ms"],
                  "contract_sha256": check["detail"]["contract_sha256"]},
        "review": receipt["circuit"]["status"],
        "publisher": receipt["publisher"]["decision"],
        "telemetry": receipt["telemetry"].get("status"),
        "trace_id": receipt["telemetry"].get("trace_id"),
        "session_id": receipt["telemetry"].get("session_id"),
    }
    if evidence["trace_id"]:
        evidence["langfuse"] = readback(evidence["trace_id"], {
            "build_id": evidence["build_id"], "feature_id": evidence["feature_id"],
            "attempt_id": evidence["attempt_id"],
            "artifact_digest": evidence["artifact_digest"],
            "session_id": evidence["session_id"]})
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
