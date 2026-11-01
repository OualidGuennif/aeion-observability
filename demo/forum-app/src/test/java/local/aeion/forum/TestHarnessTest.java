package local.aeion.forum;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import org.junit.jupiter.api.Test;

/**
 * Feature 003: the harness earns its place only if it meets the three acceptance checks in its
 * brief. Each check is one test here, and none of them touch a developer's database.
 */
class TestHarnessTest {

    @Test
    void twoDatabasesRunAtOnceWithoutInterfering() throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(2);
        try {
            List<Callable<String>> suites = List.of(
                    () -> writeAndRead("parallel-a", "alpha"),
                    () -> writeAndRead("parallel-b", "beta"));
            List<Future<String>> futures = pool.invokeAll(suites);
            List<String> results = new ArrayList<>();
            for (Future<String> future : futures) {
                results.add(future.get());
            }
            assertEquals(List.of("alpha", "beta"), results);
        } finally {
            pool.shutdownNow();
        }
    }

    @Test
    void aRowLeftByOneDatabaseIsAbsentFromTheNext() {
        try (EphemeralDatabase first = EphemeralDatabase.create()) {
            first.execute("INSERT INTO settings(name, value, updated_ns) VALUES ('left.over', 'yes', 1)");
            assertEquals(1, count(first, "settings"));
        }
        try (EphemeralDatabase second = EphemeralDatabase.create()) {
            assertEquals(0, count(second, "settings"));
        }
    }

    @Test
    void refusesAPathThatIsNotMarkedDisposable() {
        Path outsideBuild = Path.of(System.getProperty("java.io.tmpdir"), "agora-harness-probe.db");
        IllegalStateException refusal = assertThrows(IllegalStateException.class,
                () -> EphemeralDatabase.createAt(outsideBuild));
        assertTrue(refusal.getMessage().startsWith("test_db_not_disposable"), refusal.getMessage());
        assertFalse(Files.exists(outsideBuild), "the refusal must happen before any file is created");
    }

    @Test
    void refusesAProductionLookingNameInsideTheBuildDirectory() {
        Path production = Path.of("build", "test-db", "prod.db").toAbsolutePath();
        IllegalStateException refusal = assertThrows(IllegalStateException.class,
                () -> EphemeralDatabase.createAt(production));
        assertTrue(refusal.getMessage().startsWith("test_db_production_name"), refusal.getMessage());
        assertFalse(Files.exists(production), "the refusal must happen before any DDL");
    }

    @Test
    void refusesAnExistingFileItDidNotMark() throws Exception {
        Path unmarked = Path.of("build", "test-db", "unmarked-" + System.nanoTime() + ".db");
        Files.createDirectories(unmarked.getParent());
        Files.writeString(unmarked, "someone's data\n");
        try {
            IllegalStateException refusal = assertThrows(IllegalStateException.class,
                    () -> EphemeralDatabase.createAt(unmarked));
            assertTrue(refusal.getMessage().startsWith("test_db_existing_unmarked"), refusal.getMessage());
        } finally {
            Files.deleteIfExists(unmarked);
        }
    }

    @Test
    void marksTheDatabaseAndRemovesEverythingOnClose() {
        Path file;
        try (EphemeralDatabase database = EphemeralDatabase.create()) {
            file = database.file();
            assertEquals("disposable: created by EphemeralDatabase, delete at will", database.marker());
            assertTrue(Files.exists(file));
        }
        assertFalse(Files.exists(file), "closing must delete the database file");
        assertFalse(Files.exists(Path.of(file + ".disposable")), "closing must delete the marker");
    }

    private static String writeAndRead(String name, String value) {
        try (EphemeralDatabase database = EphemeralDatabase.create()) {
            database.execute("INSERT INTO settings(name, value, updated_ns) VALUES ('" + name + "', '" + value + "', 1)");
            try (var connection = database.dataSource().getConnection();
                 var statement = connection.createStatement();
                 var rows = statement.executeQuery("SELECT value FROM settings")) {
                return rows.next() ? rows.getString(1) : "no row";
            } catch (Exception error) {
                throw new IllegalStateException(error);
            }
        }
    }

    private static long count(EphemeralDatabase database, String table) {
        try (var connection = database.dataSource().getConnection();
             var statement = connection.createStatement();
             var rows = statement.executeQuery("SELECT COUNT(*) FROM " + table)) {
            return rows.next() ? rows.getLong(1) : -1;
        } catch (Exception error) {
            throw new IllegalStateException(error);
        }
    }
}
