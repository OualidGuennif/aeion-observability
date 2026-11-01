package local.aeion.forum;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.anyOf;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.notNullValue;

import io.quarkus.test.common.WithTestResource;
import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.Test;

/**
 * Features 004 and 005 over HTTP: register, log in, ask who I am, log out, and get locked out.
 *
 * Sessions are cookies here, not bearer tokens, so the test uses the real cookie jar and checks
 * the flags a browser depends on: HttpOnly, Path=/, SameSite=Strict.
 */
@QuarkusTest
@WithTestResource(QuarkusTestDatabase.class)
class AuthResourceTest {

    private static final String PASSWORD = "correct-horse-battery";

    @Test
    void registersThenLogsInAndAnswersWhoAmI() {
        given().contentType(ContentType.JSON)
                .body("{\"username\":\"alice\",\"password\":\"" + PASSWORD + "\"}")
                .when().post("/api/auth/register")
                .then().statusCode(201)
                .body("username", equalTo("alice"))
                .body("role", anyOf(equalTo("owner"), equalTo("member")));

        io.restassured.response.ExtractableResponse<io.restassured.response.Response> login =
                given().contentType(ContentType.JSON)
                        .body("{\"username\":\"alice\",\"password\":\"" + PASSWORD + "\"}")
                        .when().post("/api/auth/login")
                        .then().statusCode(200)
                        .body("username", equalTo("alice"))
                        .body("expires_ns", notNullValue())
                        .body("csrf", notNullValue())
                        .cookie(AuthService.COOKIE)
                        .extract();
        String cookie = login.cookie(AuthService.COOKIE);
        String csrf = login.path("csrf");

        given().cookie(AuthService.COOKIE, cookie)
                .when().get("/api/auth/me")
                .then().statusCode(200)
                .body("username", equalTo("alice"));

        // Logout is a mutation: the session must present its CSRF token (feature 006).
        given().cookie(AuthService.COOKIE, cookie)
                .when().post("/api/auth/logout")
                .then().statusCode(403)
                .body("error", equalTo("csrf_invalid"));

        given().cookie(AuthService.COOKIE, cookie)
                .header("X-CSRF-Token", csrf)
                .when().post("/api/auth/logout")
                .then().statusCode(200)
                .body("revoked", equalTo(true));

        given().cookie(AuthService.COOKIE, cookie)
                .when().get("/api/auth/me")
                .then().statusCode(401)
                .body("error", equalTo("unauthorized"));
    }

    @Test
    void setsAHardenedCookie() {
        String name = "cookie-" + System.nanoTime();
        given().contentType(ContentType.JSON)
                .body("{\"username\":\"" + name + "\",\"password\":\"" + PASSWORD + "\"}")
                .when().post("/api/auth/register")
                .then().statusCode(201);

        io.restassured.response.ExtractableResponse<Response> login = given().contentType(ContentType.JSON)
                .body("{\"username\":\"" + name + "\",\"password\":\"" + PASSWORD + "\"}")
                .when().post("/api/auth/login")
                .then().statusCode(200)
                .extract();

        String header = login.header("Set-Cookie");
        String flags = header == null ? "" : header;
        org.junit.jupiter.api.Assertions.assertTrue(flags.contains("HttpOnly"), flags);
        org.junit.jupiter.api.Assertions.assertTrue(flags.contains("Path=/"), flags);
        org.junit.jupiter.api.Assertions.assertTrue(flags.toLowerCase().contains("samesite=strict"), flags);
        org.junit.jupiter.api.Assertions.assertFalse(flags.contains(PASSWORD), "the cookie is not a credential echo");
    }

    @Test
    void answers401ForAWrongPasswordAnd423AfterFive() {
        String name = "locked-" + System.nanoTime();
        given().contentType(ContentType.JSON)
                .body("{\"username\":\"" + name + "\",\"password\":\"" + PASSWORD + "\"}")
                .when().post("/api/auth/register")
                .then().statusCode(201);

        for (int attempt = 1; attempt <= 5; attempt++) {
            given().contentType(ContentType.JSON)
                    .body("{\"username\":\"" + name + "\",\"password\":\"wrong-password-here\"}")
                    .when().post("/api/auth/login")
                    .then().statusCode(401)
                    .body("error", equalTo("invalid_credentials"));
        }
        given().contentType(ContentType.JSON)
                .body("{\"username\":\"" + name + "\",\"password\":\"" + PASSWORD + "\"}")
                .when().post("/api/auth/login")
                .then().statusCode(423)
                .body("error", equalTo("account_locked"));
    }

    @Test
    void refusesABodyBeyondTheSixteenKilobyteCap() {
        String tooBig = "{\"username\":\"bulk\",\"password\":\"" + "x".repeat(20000) + "\"}";
        given().contentType(ContentType.JSON)
                .body(tooBig)
                .when().post("/api/auth/register")
                .then().statusCode(413);
    }

    @Test
    void refusesAWeakPasswordAndAnUnknownAccount() {
        given().contentType(ContentType.JSON)
                .body("{\"username\":\"weakling\",\"password\":\"short\"}")
                .when().post("/api/auth/register")
                .then().statusCode(400)
                .body("error", equalTo("weak_password"));

        given().contentType(ContentType.JSON)
                .body("{\"username\":\"ghost\",\"password\":\"" + PASSWORD + "\"}")
                .when().post("/api/auth/login")
                .then().statusCode(401)
                .body("error", equalTo("invalid_credentials"));
    }
}
