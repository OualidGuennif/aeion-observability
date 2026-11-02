"""The execution a build actually gets: simulator, offline fixture or a held request.

The operator front must not silently fall back to the fake Markdown builder. ``resolve``
turns the configured mode into the components ``DispatchWorker`` needs, and fails closed
with a visible hold when the admitted target cannot be loaded. The offline builder is the
same deterministic fixture the forum qualification uses: real pinned base, real write
scopes and a real protected check, but model bytes are fixed and the attempt is simulated.
"""
from pathlib import Path

from .isolation import DockerCheckRunner
from .live import LiveBuilder, LiveReview
from .model_client import available as provider_available
from .target import TargetError, load_target
from .telemetry import FactoryTelemetry

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
    try:
        target = load_target(profile_path(repo_root), Path(repo_root))
    except (TargetError, OSError, ValueError) as exc:
        # The target profile or the pinned product checkout is unavailable on this host.
        return {"mode": mode, "hold_reason": "execution_unavailable",
                "detail": type(exc).__name__}
    if mode == "offline":
        return {"mode": "offline", "target": target, "builder": offline_builder,
                "check_sandbox": DockerCheckRunner(repo_root),
                "telemetry": FactoryTelemetry(readback=True)}
    if not provider_available():
        # The pinned target exists, but no provider credential is loaded: hold, never simulate.
        return {"mode": "live", "hold_reason": "provider_unconfigured"}
    return {"mode": "live", "target": target, "builder": LiveBuilder(),
            "review_complete": LiveReview(),
            "check_sandbox": DockerCheckRunner(repo_root),
            "telemetry": FactoryTelemetry(readback=True),
            # One attempt may reserve part of the shared purse; $15/day remains the hard cap.
            "cost_reservation_usd": "0.50"}
