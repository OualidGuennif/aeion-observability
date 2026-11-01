package local.aeion.forum;

import jakarta.enterprise.context.ApplicationScoped;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/**
 * Feature 001, the fail-closed setting: a deployment without a real session secret does not start.
 *
 * The value is read once, validated, and never logged, rendered or echoed: a refusal names the key
 * ({@code AGORA_SESSION_SECRET}) and nothing else. A placeholder is refused too, because a key
 * called "change-me" is the same accident as a missing one, only later.
 *
 * Feature 005 uses it to sign the session cookie: the cookie carries {@code <token>.<hmac>}, and a
 * value that was edited in place is refused before the database is asked anything.
 */
@ApplicationScoped
public class SessionSecret {

    static final String KEY = "AGORA_SESSION_SECRET";
    static final int MIN_BYTES = 32;

    private static final List<String> PLACEHOLDERS = List.of(
            "change-me", "changeme", "placeholder", "secret", "password", "test", "dev", "todo");

    private final byte[] material;

    @jakarta.inject.Inject
    public SessionSecret(@ConfigProperty(name = "agora.session.secret") java.util.Optional<String> value) {
        this.material = validate(value.orElse(null));
    }

    /** Build and validate a secret outside CDI, for a test that wants a known key. */
    public static SessionSecret of(String value) {
        return new SessionSecret(java.util.Optional.ofNullable(value));
    }

    /**
     * The CSRF token for a session (feature 006): derived from the cookie value with the same key,
     * so it needs no storage, and constant-time compared on the way in. A token nobody can forge
     * without the secret, and one that dies with the session it belongs to.
     */
    public String csrfFor(String token) {
        return java.util.Base64.getUrlEncoder().withoutPadding().encodeToString(hmac("csrf:" + token));
    }

    /** True only when {@code presented} is this session's token, compared in constant time. */
    public boolean csrfMatches(String token, String presented) {
        if (token == null || presented == null || presented.isEmpty()) {
            return false;
        }
        return java.security.MessageDigest.isEqual(
                csrfFor(token).getBytes(StandardCharsets.UTF_8),
                presented.getBytes(StandardCharsets.UTF_8));
    }

    /** Sign {@code token} and return {@code <token>.<mac>}, the value the cookie carries. */
    public String sign(String token) {
        String mac = java.util.Base64.getUrlEncoder().withoutPadding().encodeToString(hmac(token));
        return token + "." + mac;
    }

    /**
     * Return the token a signed cookie carries, or empty when the signature does not match.
     * An unsigned, over-long or malformed value is simply empty: the caller answers 401 either way.
     */
    public java.util.Optional<String> verify(String signed) {
        if (signed == null || signed.length() > 200) {
            return java.util.Optional.empty();
        }
        int lastDot = signed.lastIndexOf('.');
        if (lastDot <= 0 || lastDot == signed.length() - 1) {
            return java.util.Optional.empty();
        }
        String token = signed.substring(0, lastDot);
        String presented = signed.substring(lastDot + 1);
        String expected = java.util.Base64.getUrlEncoder().withoutPadding().encodeToString(hmac(token));
        return java.security.MessageDigest.isEqual(
                expected.getBytes(StandardCharsets.UTF_8), presented.getBytes(StandardCharsets.UTF_8))
                ? java.util.Optional.of(token)
                : java.util.Optional.empty();
    }

    private byte[] hmac(String token) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(material, "HmacSHA256"));
            return mac.doFinal(token.getBytes(StandardCharsets.UTF_8));
        } catch (java.security.GeneralSecurityException impossible) {
            throw new IllegalStateException("session_signature_unavailable", impossible);
        }
    }

    /**
     * Force the bean to be built now. A normal-scoped bean is a client proxy, so without this the
     * validation would run on the first request and the deployment would serve before refusing.
     */
    public void selfCheck() {
        if (material.length < MIN_BYTES) {
            throw new IllegalStateException("session_secret_unvalidated: " + KEY);
        }
    }

    private static byte[] validate(String value) {
        if (value == null || value.isBlank()) {
            throw new IllegalStateException(
                    "session_secret_missing: " + KEY + " is required and was not provided");
        }
        String trimmed = value.strip();
        String lower = trimmed.toLowerCase(Locale.ROOT);
        for (String placeholder : PLACEHOLDERS) {
            if (lower.equals(placeholder) || lower.startsWith(placeholder + "-") || lower.startsWith(placeholder + "_")) {
                throw new IllegalStateException(
                        "session_secret_placeholder: " + KEY + " must not be a placeholder value");
            }
        }
        byte[] bytes = trimmed.getBytes(StandardCharsets.UTF_8);
        if (bytes.length < MIN_BYTES) {
            throw new IllegalStateException("session_secret_too_short: " + KEY + " must be at least "
                    + MIN_BYTES + " bytes, got " + bytes.length);
        }
        return bytes;
    }
}
