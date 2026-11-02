package local.aeion.forum;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.allOf;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
import static org.hamcrest.Matchers.nullValue;

import io.quarkus.test.common.WithTestResource;
import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

/**
 * Protected contract for feature 013, copied in from outside the candidate tree.
 *
 * The candidate cannot weaken this test: the factory restores or removes this file after the
 * check, and the class lives in a directory no build is allowed to write.
 */
@QuarkusTest
@WithTestResource(QuarkusTestDatabase.class)
class SecurityHeadersContractTest {

    private static final String CSP = "default-src 'none'";

    @Test
    void successfulResponsesEnforceThePolicy() {
        given()
                .when().get("/healthz")
                .then().statusCode(200)
                .header("Content-Security-Policy", allOf(
                        containsString(CSP),
                        containsString("frame-ancestors 'none'"),
                        not(containsString("unsafe-inline"))))
                .header("Content-Security-Policy-Report-Only", nullValue())
                .header("X-Content-Type-Options", "nosniff")
                .header("Referrer-Policy", "no-referrer")
                .header("Strict-Transport-Security", containsString("max-age=31536000"));
    }

    @Test
    void refusalsCarryTheSameHeaders() {
        given()
                .when().get("/api/threads/not-a-number")
                .then().statusCode(404)
                .header("Content-Security-Policy", containsString(CSP))
                .header("Content-Security-Policy-Report-Only", nullValue())
                .header("X-Content-Type-Options", "nosniff");
    }
}
