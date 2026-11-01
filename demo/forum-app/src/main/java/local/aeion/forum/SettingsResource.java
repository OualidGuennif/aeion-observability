package local.aeion.forum;

import jakarta.inject.Inject;
import jakarta.persistence.EntityManager;
import jakarta.transaction.Transactional;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Feature 001: the skeleton answers, and the settings it reads at boot are readable and writable.
 *
 * A missing setting is a 404, never an empty object with defaults invented on the way out: the
 * caller must know the difference between "not configured" and "configured to nothing". Values are
 * bounded so a single row cannot become a blob.
 */
@Path("/api/settings")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class SettingsResource {

    private static final int MAX_NAME = 120;
    private static final int MAX_VALUE = 4000;

    @Inject
    EntityManager entityManager;

    @Inject
    ForumClock clock;

    @GET
    public List<Map<String, Object>> list() {
        return entityManager.createQuery("select s from Setting s order by s.name", Setting.class)
                .getResultList()
                .stream()
                .map(SettingsResource::view)
                .toList();
    }

    @GET
    @Path("{name}")
    public Response read(@PathParam("name") String name) {
        Setting setting = entityManager.find(Setting.class, name);
        if (setting == null) {
            return Response.status(404).entity(Map.of("error", "unknown_setting")).build();
        }
        return Response.ok(view(setting)).build();
    }

    @PUT
    @Path("{name}")
    @Transactional
    public Response write(@PathParam("name") String name, Map<String, String> body) {
        String value = body == null ? null : body.get("value");
        if (name == null || name.isBlank() || name.length() > MAX_NAME) {
            return Response.status(400).entity(Map.of("error", "invalid_name")).build();
        }
        if (value == null || value.isBlank() || value.length() > MAX_VALUE) {
            return Response.status(400).entity(Map.of("error", "invalid_value")).build();
        }
        long now = clock.nowNs();
        Setting setting = entityManager.find(Setting.class, name);
        if (setting == null) {
            setting = new Setting(name, value, now);
            entityManager.persist(setting);
        } else {
            setting.value = value;
            setting.updatedNs = now;
        }
        Map<String, Object> payload = view(setting);
        return Response.ok(payload).build();
    }

    /** The one wire shape of a setting: GET and PUT must not disagree on a field name. */
    private static Map<String, Object> view(Setting setting) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("name", setting.name);
        payload.put("value", setting.value);
        payload.put("updated_ns", setting.updatedNs);
        return payload;
    }
}
