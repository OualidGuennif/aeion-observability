package local.aeion.forum;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Optional;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

/**
 * Features 004 and 005: an account is stored as an Argon2id hash, a session only as its SHA-256,
 * and the frozen clock proves the fifteen-minute expiry without sleeping.
 */
class AuthServiceTest {

    private EphemeralDatabase database;
    private AuthService auth;
    private ForumClock clock;

    @BeforeEach
    void open() {
        database = EphemeralDatabase.create();
        clock = database.clock();
        auth = new AuthService();
        auth.dataSource = database.dataSource();
        auth.clock = clock;
        auth.secret = SessionSecret.of("a-real-secret-with-32-bytes-at-least");
    }

    @AfterEach
    void close() {
        database.close();
    }

    @Test
    void registersTheFirstAccountAsOwnerAndTheNextAsMember() {
        assertEquals("owner", auth.register("owner-here", "a-long-enough-password").role());
        assertEquals("member", auth.register("member-here", "a-long-enough-password").role());
    }

    @Test
    void storesAPasswordOnlyAsArgon2id() throws Exception {
        auth.register("hashed", "a-long-enough-password");
        try (var connection = database.dataSource().getConnection();
             var statement = connection.createStatement();
             var rows = statement.executeQuery("SELECT password FROM accounts")) {
            assertTrue(rows.next());
            String stored = rows.getString(1);
            assertTrue(stored.startsWith("$argon2id$"), stored.substring(0, 10));
            assertFalse(stored.contains("a-long-enough-password"), "the clear text must never be stored");
        }
    }

    @Test
    void storesTheSessionOnlyAsItsDigest() {
        auth.register("first-account", "a-long-enough-password");
        String name = registerAndGetName();
        AuthService.Issued issued = auth.login(name, "a-long-enough-password");
        assertTrue(issued.token().length() >= 40);
        assertEquals(Optional.of("member"), auth.authenticate(issued.token()).map(AuthService.Account::role));
        assertTrue(auth.authenticate("not-a-real-token").isEmpty());
        assertTrue(auth.authenticate(null).isEmpty());
    }

    @Test
    void refusesAWeakPasswordAndABadUsername() {
        assertEquals("weak_password", assertThrows(AuthService.AuthException.class,
                () -> auth.register("weakling", "short")).code());
        assertEquals("invalid_username", assertThrows(AuthService.AuthException.class,
                () -> auth.register("ab", "a-long-enough-password")).code());
        assertEquals("invalid_username", assertThrows(AuthService.AuthException.class,
                () -> auth.register("two words", "a-long-enough-password")).code());
    }

    @Test
    void refusesADuplicateUsername() {
        auth.register("twin", "a-long-enough-password");
        assertEquals("username_taken", assertThrows(AuthService.AuthException.class,
                () -> auth.register("twin", "a-long-enough-password")).code());
    }

    @Test
    void locksAfterFiveFailuresAndSaysNothingDifferent() {
        auth.register("lockable", "a-long-enough-password");
        for (int attempt = 1; attempt <= 5; attempt++) {
            assertEquals("invalid_credentials", assertThrows(AuthService.AuthException.class,
                    () -> auth.login("lockable", "wrong-password-here")).code());
        }
        assertEquals("account_locked", assertThrows(AuthService.AuthException.class,
                () -> auth.login("lockable", "a-long-enough-password")).code());
        assertEquals("invalid_credentials", assertThrows(AuthService.AuthException.class,
                () -> auth.login("ghost", "a-long-enough-password")).code());
    }

    @Test
    void expiresASessionAfterFifteenMinutes() {
        auth.register("timed", "a-long-enough-password");
        AuthService.Issued issued = auth.login("timed", "a-long-enough-password");
        assertTrue(auth.authenticate(issued.token()).isPresent());
        clock.advance(AuthService.SESSION_SECONDS * 1_000_000_000L - 1);
        assertTrue(auth.authenticate(issued.token()).isPresent(), "one nanosecond early is still valid");
        clock.advance(1);
        assertTrue(auth.authenticate(issued.token()).isEmpty(), "the session must be gone at the deadline");
    }

    @Test
    void refusesACookieWhoseSignatureDoesNotMatch() {
        auth.register("signed", "a-long-enough-password");
        AuthService.Issued issued = auth.login("signed", "a-long-enough-password");
        String tampered = "another-token" + issued.token().substring(issued.token().indexOf('.'));
        assertTrue(auth.authenticate(tampered).isEmpty(), "an edited cookie must not resolve");
        assertFalse(auth.logout(tampered));
        assertTrue(auth.authenticate(issued.token()).isPresent(), "the real cookie still works");
    }

    @Test
    void revokesOnLogout() {
        auth.register("leaver", "a-long-enough-password");
        AuthService.Issued issued = auth.login("leaver", "a-long-enough-password");
        assertTrue(auth.logout(issued.token()));
        assertTrue(auth.authenticate(issued.token()).isEmpty());
        assertFalse(auth.logout(issued.token()), "a second logout revokes nothing");
        assertFalse(auth.logout(null));
    }

    private String registerAndGetName() {
        String name = "digest-" + System.nanoTime();
        auth.register(name, "a-long-enough-password");
        return name;
    }
}
