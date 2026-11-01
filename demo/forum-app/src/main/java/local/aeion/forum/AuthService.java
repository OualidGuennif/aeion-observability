package local.aeion.forum;

import de.mkammerer.argon2.Argon2;
import de.mkammerer.argon2.Argon2Factory;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Base64;
import java.util.Optional;
import java.util.UUID;
import javax.sql.DataSource;

/**
 * Forum user authentication: username and password, nothing borrowed from the worker gateway.
 *
 * A worker's `aeion_…` session says "this build may read a repository". It says nothing about a
 * forum account, and it is never accepted here. The two planes share the audit habit, not a format.
 *
 * Properties, each enforced in this class:
 *  * passwords are stored only as Argon2id (3 iterations, 64 MiB, parallelism 1) and wiped from
 *    memory after use;
 *  * the session cookie value is random and stored only as its SHA-256, so a database dump does
 *    not hand out live sessions;
 *  * a session expires after 15 minutes and is revoked on logout;
 *  * five failed attempts lock the account until an operator clears it, and a locked account is
 *    checked before the password hash is even computed.
 */
@ApplicationScoped
public class AuthService {

    public static final String COOKIE = "agora_session";
    public static final int SESSION_SECONDS = 900;
    static final int MAX_FAILURES = 5;
    static final int MIN_PASSWORD = 12;
    static final int MAX_PASSWORD = 256;

    @Inject
    DataSource dataSource;

    @Inject
    ForumClock clock;

    @Inject
    SessionSecret secret;

    private final Argon2 argon2 = Argon2Factory.create(Argon2Factory.Argon2Types.ARGON2id);
    private final SecureRandom random = new SecureRandom();

    public record Account(String id, String username, String role) {
    }

    /** A signed cookie, and the CSRF token bound to it (feature 006). The raw token is not exposed. */
    public record Issued(Account account, String token, long expiresNs, String csrf) {
    }

    /** Register a member account; the first account of an empty forum is the owner. */
    public Account register(String username, String password) {
        String name = normalise(username);
        checkPassword(password);
        String role = "member";
        try (Connection connection = dataSource.getConnection()) {
            connection.setAutoCommit(false);
            try {
                if (count(connection) == 0) {
                    role = "owner";
                }
                String id = UUID.randomUUID().toString();
                String hash = argon2.hash(3, 65536, 1, password.toCharArray());
                try (PreparedStatement insert = connection.prepareStatement(
                        "INSERT INTO accounts(id, username, password, role, created_ns, failures) "
                                + "VALUES (?, ?, ?, ?, ?, 0)")) {
                    insert.setString(1, id);
                    insert.setString(2, name);
                    insert.setString(3, hash);
                    insert.setString(4, role);
                    insert.setLong(5, clock.nowNs());
                    insert.executeUpdate();
                }
                connection.commit();
                return new Account(id, name, role);
            } catch (SQLException failure) {
                connection.rollback();
                if (String.valueOf(failure.getMessage()).contains("UNIQUE")) {
                    throw new AuthException("username_taken");
                }
                throw failure;
            } finally {
                connection.setAutoCommit(true);
            }
        } catch (SQLException failure) {
            throw new IllegalStateException("register_failed", failure);
        }
    }

    /** Verify a password and mint a session; a wrong password is one failure, never a hint. */
    public Issued login(String username, String password) {
        String name = normalise(username);
        try (Connection connection = dataSource.getConnection()) {
            Account account;
            String hash;
            int failures;
            long locked;
            try (PreparedStatement read = connection.prepareStatement(
                    "SELECT id, username, role, password, failures, locked_ns FROM accounts WHERE username = ?")) {
                read.setString(1, name);
                try (ResultSet row = read.executeQuery()) {
                    if (!row.next()) {
                        throw new AuthException("invalid_credentials");
                    }
                    account = new Account(row.getString(1), row.getString(2), row.getString(3));
                    hash = row.getString(4);
                    failures = row.getInt(5);
                    locked = row.getLong(6);
                }
            }
            if (locked > 0) {
                throw new AuthException("account_locked");
            }
            if (password == null || !verify(hash, password)) {
                recordFailure(connection, account.id(), failures + 1);
                throw new AuthException("invalid_credentials");
            }
            clearFailures(connection, account.id());
            return issue(connection, account);
        } catch (SQLException failure) {
            throw new IllegalStateException("login_failed", failure);
        }
    }

    /** Resolve a cookie value to an account, or empty: expired, revoked and unknown all look alike. */
    public Optional<Account> authenticate(String signed) {
        Optional<String> token = secret.verify(signed);
        if (token.isEmpty()) {
            return Optional.empty();
        }
        try (Connection connection = dataSource.getConnection();
             PreparedStatement read = connection.prepareStatement(
                     "SELECT a.id, a.username, a.role, s.expires_ns, s.revoked_ns "
                             + "FROM sessions s JOIN accounts a ON a.id = s.account_id WHERE s.id = ?")) {
            read.setString(1, digest(token.get()));
            try (ResultSet row = read.executeQuery()) {
                if (!row.next()) {
                    return Optional.empty();
                }
                if (row.getLong(5) > 0 || row.getLong(4) <= clock.nowNs()) {
                    return Optional.empty();
                }
                return Optional.of(new Account(row.getString(1), row.getString(2), row.getString(3)));
            }
        } catch (SQLException failure) {
            throw new IllegalStateException("auth_failed", failure);
        }
    }

    public boolean logout(String signed) {
        Optional<String> token = secret.verify(signed);
        if (token.isEmpty()) {
            return false;
        }
        try (Connection connection = dataSource.getConnection();
             PreparedStatement revoke = connection.prepareStatement(
                     "UPDATE sessions SET revoked_ns = ? WHERE id = ? AND revoked_ns IS NULL")) {
            revoke.setLong(1, clock.nowNs());
            revoke.setString(2, digest(token.get()));
            return revoke.executeUpdate() == 1;
        } catch (SQLException failure) {
            throw new IllegalStateException("logout_failed", failure);
        }
    }

    private Issued issue(Connection connection, Account account) throws SQLException {
        byte[] material = new byte[32];
        random.nextBytes(material);
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(material);
        long issued = clock.nowNs();
        long expires = issued + SESSION_SECONDS * 1_000_000_000L;
        try (PreparedStatement insert = connection.prepareStatement(
                "INSERT INTO sessions(id, account_id, issued_ns, expires_ns) VALUES (?, ?, ?, ?)")) {
            insert.setString(1, digest(token));
            insert.setString(2, account.id());
            insert.setLong(3, issued);
            insert.setLong(4, expires);
            insert.executeUpdate();
        }
        return new Issued(account, secret.sign(token), expires, secret.csrfFor(token));
    }

    private void recordFailure(Connection connection, String accountId, int failures) throws SQLException {
        boolean lock = failures >= MAX_FAILURES;
        try (PreparedStatement update = connection.prepareStatement(
                "UPDATE accounts SET failures = ?, locked_ns = ? WHERE id = ?")) {
            update.setInt(1, failures);
            update.setLong(2, lock ? clock.nowNs() : 0L);
            update.setString(3, accountId);
            update.executeUpdate();
        }
    }

    private void clearFailures(Connection connection, String accountId) throws SQLException {
        try (PreparedStatement update = connection.prepareStatement(
                "UPDATE accounts SET failures = 0 WHERE id = ?")) {
            update.setString(1, accountId);
            update.executeUpdate();
        }
    }

    private long count(Connection connection) throws SQLException {
        try (PreparedStatement count = connection.prepareStatement("SELECT COUNT(*) FROM accounts");
             ResultSet row = count.executeQuery()) {
            return row.next() ? row.getLong(1) : 0;
        }
    }

    private boolean verify(String hash, String password) {
        char[] material = password.toCharArray();
        try {
            return argon2.verify(hash, material);
        } finally {
            argon2.wipeArray(material);
        }
    }

    private static String normalise(String username) {
        String name = username == null ? "" : username.strip();
        if (name.length() < 3 || name.length() > 64 || name.contains(" ")) {
            throw new AuthException("invalid_username");
        }
        return name;
    }

    private static void checkPassword(String password) {
        if (password == null || password.length() < MIN_PASSWORD || password.length() > MAX_PASSWORD) {
            throw new AuthException("weak_password");
        }
    }

    private static String digest(String token) {
        try {
            MessageDigest sha = MessageDigest.getInstance("SHA-256");
            return java.util.HexFormat.of().formatHex(sha.digest(token.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException impossible) {
            throw new IllegalStateException(impossible);
        }
    }

    /** A refusal with a code safe to return to the client. */
    public static class AuthException extends RuntimeException {
        private final String code;

        public AuthException(String code) {
            super(code);
            this.code = code;
        }

        public String code() {
            return code;
        }
    }
}
