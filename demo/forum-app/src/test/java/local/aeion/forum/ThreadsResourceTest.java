package local.aeion.forum;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;

import io.quarkus.test.common.WithTestResource;
import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;

/**
 * Feature 010 over HTTP: anyone reads, only a forum session writes.
 *
 * A worker's gateway session is not accepted here, and the test proves the refusal rather than
 * trusting the comment: no cookie means 401, and a made-up one means 401 too.
 */
@QuarkusTest
@WithTestResource(QuarkusTestDatabase.class)
class ThreadsResourceTest {

    private static final String PASSWORD = "correct-horse-battery";

    /** Log in through HTTP and keep both halves: the cookie and the CSRF token bound to it. */
    private String[] signIn(String name) {
        given().contentType(ContentType.JSON)
                .body("{\"username\":\"" + name + "\",\"password\":\"" + PASSWORD + "\"}")
                .when().post("/api/auth/register")
                .then().statusCode(201);
        var login = given().contentType(ContentType.JSON)
                .body("{\"username\":\"" + name + "\",\"password\":\"" + PASSWORD + "\"}")
                .when().post("/api/auth/login")
                .then().statusCode(200)
                .extract();
        return new String[] {login.cookie(AuthService.COOKIE), login.path("csrf")};
    }

    @Test
    void aMutationWithTheSessionButWithoutTheCsrfTokenIsRefused() {
        String[] session = signIn("no-token" + System.nanoTime());
        given().cookie(AuthService.COOKIE, session[0])
                .contentType(ContentType.JSON)
                .body("{\"title\":\"A real title\",\"body\":\"A cross-site form could send this\"}")
                .when().post("/api/threads")
                .then().statusCode(403)
                .body("error", equalTo("csrf_invalid"));

        given().cookie(AuthService.COOKIE, session[0])
                .header("X-CSRF-Token", "not-the-token")
                .contentType(ContentType.JSON)
                .body("{\"title\":\"A real title\",\"body\":\"nor this one\"}")
                .when().post("/api/threads")
                .then().statusCode(403);

        // Reading is never gated, and a GET with the cookie still works.
        given().cookie(AuthService.COOKIE, session[0])
                .when().get("/api/threads")
                .then().statusCode(200);
    }

    @Test
    void readingIsPublicCreatingIsNot() {
        given().when().get("/api/threads")
                .then().statusCode(200)
                .body("count", greaterThanOrEqualTo(0));

        given().contentType(ContentType.JSON)
                .body("{\"title\":\"Anonymous\",\"body\":\"should not work\"}")
                .when().post("/api/threads")
                .then().statusCode(401)
                .body("error", equalTo("unauthorized"));

        given().cookie(AuthService.COOKIE, "aeion_not_a_forum_cookie.aaaa")
                .contentType(ContentType.JSON)
                .body("{\"title\":\"Worker\",\"body\":\"a build session is not a person\"}")
                .when().post("/api/threads")
                .then().statusCode(401);
    }

    @Test
    void aMemberCreatesAThreadAndEveryoneCanReadIt() {
        String[] session = signIn("poster" + System.nanoTime());
        String cookie = session[0];
        String csrf = session[1];

        String id = given().cookie(AuthService.COOKIE, cookie)
                .header("X-CSRF-Token", csrf)
                .contentType(ContentType.JSON)
                .body("{\"title\":\"Kafka leaves the request path\",\"body\":\"The event is queued.\"}")
                .when().post("/api/threads")
                .then().statusCode(201)
                .body("title", equalTo("Kafka leaves the request path"))
                .extract().path("id");

        given().when().get("/api/threads/" + id)
                .then().statusCode(200)
                .body("id", equalTo(id));

        given().when().get("/api/threads/absent-thread")
                .then().statusCode(404)
                .body("error", equalTo("unknown_thread"));

        given().when().get("/api/threads?limit=5")
                .then().statusCode(200);
    }

    @Test
    void refusesAThreadWithoutTitleOrBody() {
        String[] session = signIn("vague" + System.nanoTime());
        String cookie = session[0];
        String csrf = session[1];

        given().cookie(AuthService.COOKIE, cookie)
                .header("X-CSRF-Token", csrf)
                .contentType(ContentType.JSON)
                .body("{\"title\":\"ab\",\"body\":\"too short a title\"}")
                .when().post("/api/threads")
                .then().statusCode(400)
                .body("error", equalTo("invalid_title"));

        given().cookie(AuthService.COOKIE, cookie)
                .header("X-CSRF-Token", csrf)
                .contentType(ContentType.JSON)
                .body("{\"title\":\"A fine title\",\"body\":\"   \"}")
                .when().post("/api/threads")
                .then().statusCode(400)
                .body("error", equalTo("invalid_body"));
    }
}
