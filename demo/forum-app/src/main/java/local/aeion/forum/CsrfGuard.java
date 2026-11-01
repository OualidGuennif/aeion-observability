package local.aeion.forum;

import jakarta.inject.Inject;
import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerRequestFilter;
import jakarta.ws.rs.core.Cookie;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.Provider;
import java.util.Map;
import java.util.Optional;

/**
 * Feature 006: a mutation that carries a session cookie must also carry that session's CSRF token.
 *
 * The token is derived from the cookie value and the same key that signs it (`SessionSecret`), so it
 * is bound to the session, needs no table, dies with the session and cannot be forged without the
 * secret. It is read from the `X-CSRF-Token` header only: a token in a URL ends up in logs, referrers
 * and screenshots.
 *
 * Requests without a session cookie are let through, because `register` and `login` have no session
 * yet and are themselves the credential exchange. A cross-site form cannot read the token, so holding
 * the cookie is not enough to act for the user.
 */
@Provider
public class CsrfGuard implements ContainerRequestFilter {

    public static final String HEADER = "X-CSRF-Token";

    @Inject
    SessionSecret secret;

    @Override
    public void filter(ContainerRequestContext request) {
        String method = request.getMethod();
        if ("GET".equals(method) || "HEAD".equals(method) || "OPTIONS".equals(method)) {
            return;
        }
        if (!pathOf(request.getUriInfo().getPath()).startsWith("/api")) {
            return;
        }
        Cookie cookie = request.getCookies().get(AuthService.COOKIE);
        if (cookie == null) {
            return; // no session, nothing to protect: login and register are the credential exchange
        }
        Optional<String> token = secret.verify(cookie.getValue());
        if (token.isEmpty()) {
            return; // an unusable cookie is refused by the resource as 401, which says more
        }
        if (!secret.csrfMatches(token.get(), request.getHeaderString(HEADER))) {
            request.abortWith(Response.status(403)
                    .type(MediaType.APPLICATION_JSON)
                    .entity(Map.of("error", "csrf_invalid"))
                    .build());
        }
    }

    private static String pathOf(String path) {
        return path.startsWith("/") ? path : "/" + path;
    }
}
