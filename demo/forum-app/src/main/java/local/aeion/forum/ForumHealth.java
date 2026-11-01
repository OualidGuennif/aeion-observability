package local.aeion.forum;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import java.util.LinkedHashMap;
import java.util.Map;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/** Feature 001: the service answers, and it says which release is answering. */
@Path("/")
@Produces(MediaType.APPLICATION_JSON)
public class ForumHealth {

    @ConfigProperty(name = "aeion.release", defaultValue = "unreleased")
    String release;

    @GET
    @Path("healthz")
    public Map<String, Object> health() {
        return payload("ok");
    }

    @GET
    @Path("__release")
    public Map<String, Object> release() {
        return payload("serving");
    }

    private Map<String, Object> payload(String status) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("status", status);
        body.put("release", release);
        body.put("runtime", System.getProperty("java.version"));
        return body;
    }
}
