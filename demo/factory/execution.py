"""The execution a build actually gets: simulator, offline fixture or a held request.

The operator front must not silently fall back to the fake Markdown builder. ``resolve``
turns the configured mode into the components ``DispatchWorker`` needs, and fails closed
with a visible hold when the admitted target cannot be loaded. The offline builder is the
same deterministic fixture the forum qualification uses: real pinned base, real write
scopes and a real protected check, but model bytes are fixed and the attempt is simulated.
"""
from pathlib import Path

from .budget import BudgetError, settings as budget_settings
from .isolation import DockerCheckRunner
from .inference_config import available as provider_available
from .target import TargetError, load_target
from .telemetry import FactoryTelemetry
from .flue_qualification import ready as flue_factory_ready, protocol_hash
from .preparation import TaskPreparer
from .source import SourceSynchronizer

MODES = ("simulator", "offline", "live")
DEFAULT_FEATURE = "013"

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


def offline_builder(repo, frozen, feature, brief):
    """The injected offline model: deterministic Java, no network, no paid call.

    It refuses any feature other than 013 or a brief that does not name the security
    headers, so a mis-pointed target cannot produce a plausible but wrong artifact.
    """
    if feature["id"] != "013" or "security headers" not in brief.read_text().lower():
        raise RuntimeError("brief_does_not_name_this_feature")
    main = Path(repo) / frozen.write_scopes[0]
    test = Path(repo) / frozen.write_scopes[1]
    main.mkdir(parents=True, exist_ok=True)
    test.mkdir(parents=True, exist_ok=True)
    (main / "SecurityHeadersFilter.java").write_text(FILTER)
    (test / "SecurityHeadersTest.java").write_text(TEST)


def profile_path(repo_root, feature_id=DEFAULT_FEATURE):
    return Path(repo_root) / "demo/forum/targets" / f"forum-app-{feature_id}.json"


def resolve(repo_root, mode):
    """Return the execution components for a configured mode, never a silent fallback."""
    mode = str(mode or "simulator")
    if mode == "simulator":
        return {"mode": "simulator"}
    if mode not in MODES:
        return {"mode": mode, "hold_reason": "execution_mode_unknown"}
    targets = {}
    errors = {}
    directory = Path(repo_root) / "demo/forum/targets"
    for path in sorted(directory.glob("forum-app-[0-9][0-9][0-9].json")):
        feature_id = path.stem.removeprefix("forum-app-")
        try:
            candidate = load_target(path, Path(repo_root))
            if candidate.feature_id != feature_id:
                raise TargetError("profile_feature_mismatch")
            targets[feature_id] = candidate
        except (TargetError, OSError, ValueError) as exc:
            errors[feature_id] = type(exc).__name__
    if not targets and mode == 'offline':
        return {"mode": mode, "hold_reason": "execution_unavailable", "target_errors": errors}
    # Offline qualification is a fixed fixture, never a pretend implementation of another feature.
    if mode == "offline":
        targets = {fid: target for fid, target in targets.items() if fid == DEFAULT_FEATURE}
        if not targets:
            return {"mode": mode, "hold_reason": "execution_unavailable"}
    target = targets.get(DEFAULT_FEATURE) or next(iter(targets.values()), None)
    if mode == "offline":
        return {"mode": "offline", "target": target, "targets": targets, "target_errors": errors, "builder": offline_builder,
                "check_sandbox": DockerCheckRunner(repo_root),
                "telemetry": FactoryTelemetry(readback=True)}
    if not provider_available():
        # The pinned target exists, but no provider credential is loaded: hold, never simulate.
        return {"mode": "live", "hold_reason": "provider_unconfigured"}
    try:
        bounds = budget_settings()
    except BudgetError:
        return {"mode": "live", "hold_reason": "budget_config_invalid"}
    from .product_checks import ProductCheckRunner
    checker = ProductCheckRunner(repo_root)
    preparer = TaskPreparer(repo_root,
        Path(repo_root) / 'demo/.local/factory/agents/aeion-autonomous-forum', checker=checker,
        synchronize=SourceSynchronizer(repo_root), product=True)
    from .flue_builder import FlueBuilder
    from .flue_review import FlueReview
    reviews=FlueReview(cost_limit=str(bounds['REVIEW_MAX_USD']),max_output_tokens=65536)
    reviews.timeout_seconds=900
    loaded_protocol=protocol_hash(repo_root)
    execution = {"mode": "live", "preparer": preparer, "target_errors": errors,
            # A fresh disk proof must not authorize old Python objects after an edit.
            # Same-protocol expiry can recover; changed code requires a clean reload.
            "admission_check": lambda: protocol_hash(repo_root)==loaded_protocol and flue_factory_ready(repo_root),
            "builder": FlueBuilder(repo_root, {}, check_sandbox=checker),
            "review_complete": reviews, 'engine': 'flue-pi', 'runtime': 'flue-openshell', 'tier': 3,
            "publication": True,
            "check_sandbox": checker,
            "telemetry": FactoryTelemetry(readback=True),
            # One author execution reserves its whole cap before spending (demo/budget.conf);
            # the frozen value binds that build, and the relay stops the session at it.
            "cost_reservation_usd": str(bounds['AUTHOR_MAX_USD'])}
    if not flue_factory_ready(repo_root):
        execution['hold_reason'] = 'flue_factory_unqualified'
    return execution
