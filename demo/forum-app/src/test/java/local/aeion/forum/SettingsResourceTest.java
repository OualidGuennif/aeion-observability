package local.aeion.forum;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;

import io.quarkus.test.common.WithTestResource;
import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

/**
 * Feature 001 over HTTP, on the application's own port, against a database created for this class.
 *
 * The point of running the real server is that the wire shape is part of the feature: a setting
 * that answers {@code updated_ns} when written and {@code updatedNs} when read is a trap for every
 * client, so the test pins both directions to one shape.
 */
@QuarkusTest
@WithTestResource(QuarkusTestDatabase.class)
class SettingsResourceTest {

    @Test
    void writesThenReadsTheSameShape() {
        given()
                .contentType("application/json")
                .body("{\"value\":\"Agora\"}")
                .when().put("/api/settings/forum.name")
                .then().statusCode(200)
                .body("name", equalTo("forum.name"))
                .body("value", equalTo("Agora"))
                .body("updated_ns", notNullValue())
                .body("updatedNs", nullValue());

        given()
                .when().get("/api/settings/forum.name")
                .then().statusCode(200)
                .body("name", equalTo("forum.name"))
                .body("value", equalTo("Agora"))
                .body("updated_ns", notNullValue());
    }

    @Test
    void answers404ForASettingThatWasNeverWritten() {
        given()
                .when().get("/api/settings/never.set")
                .then().statusCode(404)
                .body("error", equalTo("unknown_setting"));
    }

    @Test
    void refusesABlankValue() {
        given()
                .contentType("application/json")
                .body("{\"value\":\"   \"}")
                .when().put("/api/settings/blank.name")
                .then().statusCode(400)
                .body("error", equalTo("invalid_value"));
    }

    @Test
    void refusesAValueBeyondTheTextCap() {
        String tooLong = "x".repeat(4001);
        given()
                .contentType("application/json")
                .body("{\"value\":\"" + tooLong + "\"}")
                .when().put("/api/settings/long.name")
                .then().statusCode(400)
                .body("error", equalTo("invalid_value"));
    }
}
