package local.aeion.forum;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

/**
 * Feature 002 and 003: the migration engine, exercised against the real migration files.
 *
 * These tests exist because a file that opened with a {@code --} header used to lose its first
 * statement: the ledger said V1 was applied while {@code settings} did not exist, and only a live
 * request found out. A test now reads the schema a deployment gets.
 */
class MigrationsTest {

    @Test
    void appliesEveryTableTheMigrationsDeclare() {
        try (EphemeralDatabase database = EphemeralDatabase.create()) {
            for (String table : List.of(
                    "settings", "accounts", "sessions", "threads", "schema_events", "schema_migrations",
                    "thread_outbox", "thread_event_log")) {
                assertTrue(database.hasTable(table), "missing table " + table);
            }
        }
    }

    @Test
    void aSecondRunAppliesNothing() {
        try (EphemeralDatabase database = EphemeralDatabase.create()) {
            List<String> again = Migrations.apply(database.dataSource(), "db/migration", database.clock());
            assertEquals(List.of(), again);
            assertEquals(Migrations.index("db/migration").size(),
                    Migrations.applied(database.dataSource()).size());
        }
    }

    @Test
    void aFailingMigrationRollsBackAndRecordsNothing() {
        try (EphemeralDatabase database = EphemeralDatabase.createEmpty()) {
            IllegalStateException failure = assertThrows(IllegalStateException.class,
                    () -> Migrations.apply(database.dataSource(), "db/migration-broken", database.clock()));
            assertTrue(failure.getMessage().startsWith("migration_failed"), failure.getMessage());
            assertFalse(database.hasTable("probe"), "a failed migration must leave no table behind");
            assertEquals(List.of(), Migrations.applied(database.dataSource()));
        }
    }

    @Test
    void aHeaderCommentDoesNotSwallowTheFirstStatement() {
        String file = """
                -- header line one
                -- header line two

                CREATE TABLE first (id TEXT);

                CREATE TABLE second (id TEXT);
                """;
        List<String> statements = Migrations.statements(file);
        assertEquals(2, statements.size(), statements.toString());
        assertTrue(statements.get(0).startsWith("CREATE TABLE first"), statements.get(0));
        assertTrue(statements.get(1).startsWith("CREATE TABLE second"), statements.get(1));
    }

    @Test
    void refusesAnIndexThatListsNothingOrIsMissing() {
        IllegalStateException empty = assertThrows(IllegalStateException.class,
                () -> Migrations.index("db/migration-empty"));
        assertEquals("migration_index_empty: db/migration-empty", empty.getMessage());
        IllegalStateException missing = assertThrows(IllegalStateException.class,
                () -> Migrations.index("db/nonexistent"));
        assertEquals("migration_missing: /db/nonexistent/index.txt", missing.getMessage());
    }
}
