package local.aeion.forum;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.equalTo;
import static org.junit.jupiter.api.Assertions.assertFalse;

import io.quarkus.test.common.WithTestResource;
import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;

/** External acceptance for feature 017: validate shape before handler side effects. */
@QuarkusTest
@WithTestResource(QuarkusTestDatabase.class)
class RequestValidationContractTest {
    @Test
    void anUnknownFieldIsRejectedWithoutCreatingAnAccount() {
        String name = "shape-" + System.nanoTime();
        given().contentType(ContentType.JSON)
                .body("{\"username\":\"" + name + "\",\"password\":\"contract-password-42\",\"extra\":\"PRIVATE_VALUE\"}")
                .post("/api/auth/register").then().statusCode(422)
                .body("error", equalTo("invalid_request"))
                .body("fields", org.hamcrest.Matchers.hasItem("extra"));
        given().contentType(ContentType.JSON)
                .body("{\"username\":\"" + name + "\",\"password\":\"contract-password-42\"}")
                .post("/api/auth/login").then().statusCode(401);
    }

    @Test
    void missingAndWrongTypeFieldsArePathsOnly() {
        String missing = given().contentType(ContentType.JSON)
                .body("{\"username\":\"PRIVATE_USERNAME\"}")
                .post("/api/auth/register").then().statusCode(422)
                .body("fields", org.hamcrest.Matchers.hasItem("password"))
                .extract().asString();
        assertFalse(missing.contains("PRIVATE_USERNAME"));
        String wrong = given().contentType(ContentType.JSON)
                .body("{\"username\":1234,\"password\":\"PRIVATE_PASSWORD\"}")
                .post("/api/auth/login").then().statusCode(422)
                .body("fields", org.hamcrest.Matchers.hasItem("username"))
                .extract().asString();
        assertFalse(wrong.contains("PRIVATE_PASSWORD"));
    }

    @Test
    void bodyCapAppliesBeforeSessionAndCsrfChecks() {
        given().contentType(ContentType.JSON)
                .body("{\"body\":\"" + "x".repeat(17000) + "\"}")
                .post("/api/threads").then().statusCode(413);
    }

    @Test
    void validJsonAndBusinessRefusalsKeepTheirExistingMeaning() {
        given().contentType(ContentType.JSON)
                .body("{\"username\":\"missing-" + System.nanoTime() + "\",\"password\":\"contract-password-42\"}")
                .post("/api/auth/login").then().statusCode(401)
                .body("error", equalTo("invalid_credentials"));
        given().get("/healthz").then().statusCode(200);
    }
}
