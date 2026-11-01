package local.aeion.forum;

import io.quarkus.test.common.QuarkusTestResourceLifecycleManager;
import java.util.Map;

/**
 * Feature 003 for a running application: every {@code @QuarkusTest} class reaches its own
 * ephemeral database instead of the developer's {@code /tmp/agora.db}.
 *
 * The URL is handed to Quarkus before the application starts, which is why this is a lifecycle
 * manager rather than a field: the datasource is built once, at boot. Nothing here is reachable
 * from the shipped jar; it only exists on the test classpath.
 */
public class QuarkusTestDatabase implements QuarkusTestResourceLifecycleManager {

    private EphemeralDatabase database;

    @Override
    public Map<String, String> start() {
        database = EphemeralDatabase.create();
        return Map.of(
                "AEION_SQLITE_PATH", database.file().toString(),
                "AEION_RELEASE", "test-ephemeral",
                // The application refuses to start without a real secret; a test gets a fixed one.
                "AGORA_SESSION_SECRET", "ephemeral-suite-secret-0123456789abcdef");
    }

    @Override
    public void stop() {
        if (database != null) {
            database.close();
            database = null;
        }
    }
}
