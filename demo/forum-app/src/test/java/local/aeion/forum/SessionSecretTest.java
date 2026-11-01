package local.aeion.forum;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Optional;
import org.junit.jupiter.api.Test;

/**
 * Feature 001's fail-closed setting and feature 005's signed cookie, without a running application.
 *
 * A refusal must name the key and nothing else, and a cookie edited in place must never reach the
 * database lookup: both are asserted here, byte for byte.
 */
class SessionSecretTest {

    private static final String GOOD = "a-real-secret-with-32-bytes-at-least";

    @Test
    void refusesAMissingSecret() {
        IllegalStateException refusal = assertThrows(IllegalStateException.class, () -> SessionSecret.of(""));
        assertTrue(refusal.getMessage().startsWith("session_secret_missing"), refusal.getMessage());
        assertFalse(refusal.getMessage().contains("="), "the refusal must not look like a value");
    }

    @Test
    void refusesAShortSecretAndSaysHowShort() {
        IllegalStateException refusal = assertThrows(IllegalStateException.class, () -> SessionSecret.of("too-short"));
        assertTrue(refusal.getMessage().startsWith("session_secret_too_short"), refusal.getMessage());
        assertTrue(refusal.getMessage().contains("32"), refusal.getMessage());
    }

    @Test
    void refusesAPlaceholder() {
        for (String placeholder : new String[] {"changeme", "change-me-0123456789abcdefghijklmnop", "test-secret-0123456789abcdefghijklmn"}) {
            IllegalStateException refusal = assertThrows(IllegalStateException.class,
                    () -> SessionSecret.of(placeholder), placeholder);
            assertTrue(refusal.getMessage().startsWith("session_secret_placeholder"), refusal.getMessage());
        }
    }

    @Test
    void signsAndVerifiesACookie() {
        SessionSecret secret = SessionSecret.of(GOOD);
        String signed = secret.sign("token-value");
        assertTrue(signed.startsWith("token-value."), signed);
        assertEquals(Optional.of("token-value"), secret.verify(signed));
    }

    @Test
    void refusesACookieEditedInPlace() {
        SessionSecret secret = SessionSecret.of(GOOD);
        String signed = secret.sign("token-value");
        String tampered = "other-value." + signed.substring(signed.indexOf('.') + 1);
        assertTrue(secret.verify(tampered).isEmpty());
        assertTrue(secret.verify(signed + "x").isEmpty());
        assertTrue(secret.verify("no-dot-at-all").isEmpty());
        assertTrue(secret.verify(null).isEmpty());
        assertTrue(secret.verify("").isEmpty());
    }

    @Test
    void aDifferentSecretDoesNotVerifyTheSameCookie() {
        String signed = SessionSecret.of(GOOD).sign("token-value");
        assertTrue(SessionSecret.of("another-real-secret-with-32-bytes").verify(signed).isEmpty());
    }

    @Test
    void twoSignaturesOfTheSameTokenAreIdenticalAndStable() {
        SessionSecret secret = SessionSecret.of(GOOD);
        assertEquals(secret.sign("token-value"), secret.sign("token-value"));
        assertNotEquals(secret.sign("token-value"), secret.sign("other-value"));
    }
}
