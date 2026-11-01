package local.aeion.forum;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.CookieParam;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.Cookie;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/**
 * Feature 010: reading is public, writing needs a forum session.
 *
 * A thread is created with the cookie of an authenticated account, never with a worker's
 * `aeion_...` session: that one describes a build, not a person. The event that leaves the request
 * path is written in the same transaction, so a client that got a 201 can rely on the event existing.
 */
@Path("/api/threads")
@Produces(MediaType.APPLICATION_JSON)
public class ThreadsResource {

    @Inject
    AuthService auth;

    @Inject
    ThreadService threads;

    @ConfigProperty(name = "agora.kafka.topic", defaultValue = "agora.threads")
    String topic;

    @GET
    public Map<String, Object> list(@QueryParam("limit") Integer limit) {
        List<Map<String, Object>> items = threads.recent(limit == null ? 20 : limit).stream()
                .map(ThreadsResource::view)
                .toList();
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("threads", items);
        body.put("count", items.size());
        return body;
    }

    @GET
    @Path("{id}")
    public Response read(@PathParam("id") String id) {
        Optional<ThreadService.ThreadView> thread = threads.find(id);
        if (thread.isEmpty()) {
            return Response.status(404).entity(Map.of("error", "unknown_thread")).build();
        }
        return Response.ok(view(thread.get())).build();
    }

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    public Response create(@CookieParam(AuthService.COOKIE) Cookie cookie, Map<String, String> body) {
        Optional<AuthService.Account> account =
                cookie == null ? Optional.empty() : auth.authenticate(cookie.getValue());
        if (account.isEmpty()) {
            return Response.status(401).entity(Map.of("error", "unauthorized")).build();
        }
        try {
            ThreadService.ThreadView thread = threads.create(account.get(), topic,
                    body == null ? null : body.get("title"),
                    body == null ? null : body.get("body"));
            return Response.status(201).entity(view(thread)).build();
        } catch (ThreadService.ThreadException refusal) {
            return Response.status(400).entity(Map.of("error", refusal.code())).build();
        }
    }

    private static Map<String, Object> view(ThreadService.ThreadView thread) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("id", thread.id());
        payload.put("title", thread.title());
        payload.put("body", thread.body());
        payload.put("author_id", thread.authorId());
        payload.put("created_ns", thread.createdNs());
        return payload;
    }
}
