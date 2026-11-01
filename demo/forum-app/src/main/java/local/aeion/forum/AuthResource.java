package local.aeion.forum;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.CookieParam;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.Cookie;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.NewCookie;
import jakarta.ws.rs.core.Response;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

/** Forum user endpoints: register, login, logout, and "who am I". Username and password only. */
@Path("/api/auth")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class AuthResource {

    @Inject
    AuthService auth;

    @POST
    @Path("register")
    public Response register(Map<String, String> body) {
        try {
            AuthService.Account account = auth.register(value(body, "username"), value(body, "password"));
            return Response.status(201).entity(view(account)).build();
        } catch (AuthService.AuthException refusal) {
            return Response.status(400).entity(Map.of("error", refusal.code())).build();
        }
    }

    @POST
    @Path("login")
    public Response login(Map<String, String> body) {
        try {
            AuthService.Issued issued = auth.login(value(body, "username"), value(body, "password"));
            NewCookie cookie = new NewCookie.Builder(AuthService.COOKIE)
                    .value(issued.token())
                    .path("/")
                    .httpOnly(true)
                    .sameSite(NewCookie.SameSite.STRICT)
                    .maxAge(AuthService.SESSION_SECONDS)
                    .build();
            Map<String, Object> payload = new LinkedHashMap<>(view(issued.account()));
            payload.put("expires_ns", issued.expiresNs());
            // The double-submit half: the client must send this back on every mutation.
            payload.put("csrf", issued.csrf());
            return Response.ok(payload).cookie(cookie).build();
        } catch (AuthService.AuthException refusal) {
            int status = "account_locked".equals(refusal.code()) ? 423 : 401;
            return Response.status(status).entity(Map.of("error", refusal.code())).build();
        }
    }

    @POST
    @Path("logout")
    @Consumes(MediaType.WILDCARD)
    public Response logout(@CookieParam(AuthService.COOKIE) Cookie cookie) {
        boolean revoked = cookie != null && auth.logout(cookie.getValue());
        NewCookie cleared = new NewCookie.Builder(AuthService.COOKIE).value("").path("/").maxAge(0).build();
        return Response.ok(Map.of("revoked", revoked)).cookie(cleared).build();
    }

    @GET
    @Path("me")
    public Response me(@CookieParam(AuthService.COOKIE) Cookie cookie) {
        Optional<AuthService.Account> account =
                cookie == null ? Optional.empty() : auth.authenticate(cookie.getValue());
        if (account.isEmpty()) {
            return Response.status(401).entity(Map.of("error", "unauthorized")).build();
        }
        return Response.ok(view(account.get())).build();
    }

    private static Map<String, Object> view(AuthService.Account account) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("id", account.id());
        payload.put("username", account.username());
        payload.put("role", account.role());
        return payload;
    }

    private static String value(Map<String, String> body, String name) {
        return body == null ? null : body.get(name);
    }
}
