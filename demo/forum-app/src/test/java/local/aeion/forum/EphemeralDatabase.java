package local.aeion.forum;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.List;
import java.util.UUID;
import javax.sql.DataSource;
import org.sqlite.SQLiteDataSource;

/**
 * Feature 003: a database that exists for one test and is thrown away afterwards.
 *
 * Three properties, all enforced here:
 *  * <b>Isolated.</b> Every instance is a new file under {@code build/test-db/}, so two suites can
 *    run at once, and a row one test leaves cannot change the next test's result.
 *  * <b>Marked disposable.</b> The file is created together with a {@code .disposable} marker, and
 *    {@link #open} refuses a path that is not inside a build directory or that names a production
 *    file, before any DDL runs.
 *  * <b>Same schema as a deployment.</b> Migrations come from the application's own resources
 *    through {@link Migrations}, never from a hand-written test schema.
 *
 * It can be used two ways: directly ({@code EphemeralDatabase.create()}) in a plain unit test, or
 * through {@code QuarkusTestDatabase} which binds it to a running application.
 */
public final class EphemeralDatabase implements AutoCloseable {

    private static final String MARKER = ".disposable";
    private static final String SCHEMA = "db/migration";

    private final Path file;
    private final Path marker;
    private final SQLiteDataSource dataSource;
    private final ForumClock clock;

    private EphemeralDatabase(Path file, Path marker, SQLiteDataSource dataSource, ForumClock clock) {
        this.file = file;
        this.marker = marker;
        this.dataSource = dataSource;
        this.clock = clock;
    }

    /** Create a marked, isolated, migrated database; the caller closes it. */
    public static EphemeralDatabase create() {
        Path root = Path.of("build", "test-db").toAbsolutePath().normalize();
        return createAt(root.resolve(UUID.randomUUID() + ".db"));
    }

    /**
     * Create a marked, isolated database with no schema at all: the shape a migration test needs,
     * where the migrations under test are the first thing the database ever sees.
     */
    public static EphemeralDatabase createEmpty() {
        return open(Path.of("build", "test-db").toAbsolutePath().normalize()
                .resolve(UUID.randomUUID() + ".db"), false);
    }

    /** Create a marked, isolated, migrated database at an explicit path, refusing an unsafe one. */
    public static EphemeralDatabase createAt(Path target) {
        return open(target, true);
    }

    private static EphemeralDatabase open(Path target, boolean migrate) {
        Path file = target.toAbsolutePath().normalize();
        requireDisposableTarget(file);
        Path marker = file.resolveSibling(file.getFileName() + MARKER);
        try {
            Files.createDirectories(file.getParent());
            Files.writeString(marker, "disposable: created by EphemeralDatabase, delete at will\n");
        } catch (IOException error) {
            throw new IllegalStateException("test_db_unprepared: " + file, error);
        }
        SQLiteDataSource dataSource = new SQLiteDataSource();
        dataSource.setUrl("jdbc:sqlite:" + file);
        ForumClock clock = new ForumClock();
        clock.freeze(1_790_000_000_000_000_000L);
        EphemeralDatabase database = new EphemeralDatabase(file, marker, dataSource, clock);
        try {
            database.pragma("journal_mode=WAL");
            database.pragma("busy_timeout=5000");
            if (migrate) {
                Migrations.apply(dataSource, SCHEMA, clock);
            }
        } catch (RuntimeException failure) {
            database.close();
            throw failure;
        }
        return database;
    }

    /**
     * Refuse anything that could be someone's data: a path that is not under a build directory, or
     * one that names a production file. The check runs before the marker exists, so an existing
     * unmarked file is never opened.
     */
    static void requireDisposableTarget(Path file) {
        String text = file.toString();
        if (!text.contains("build")) {
            throw new IllegalStateException("test_db_not_disposable: " + file);
        }
        String name = file.getFileName().toString().toLowerCase(java.util.Locale.ROOT);
        for (String forbidden : List.of("prod", "production", "live", "agora.db")) {
            if (name.equals(forbidden) || name.startsWith(forbidden + ".")) {
                throw new IllegalStateException("test_db_production_name: " + file);
            }
        }
        if (Files.exists(file) && !Files.exists(file.resolveSibling(file.getFileName() + MARKER))) {
            throw new IllegalStateException("test_db_existing_unmarked: " + file);
        }
    }

    public DataSource dataSource() {
        return dataSource;
    }

    public ForumClock clock() {
        return clock;
    }

    public Path file() {
        return file;
    }

    /** The marker text, or empty when the marker was removed. */
    public String marker() {
        try {
            return Files.exists(marker) ? Files.readString(marker).strip() : "";
        } catch (IOException error) {
            throw new IllegalStateException("test_db_marker_unreadable", error);
        }
    }

    /** Run one statement; the harness is for DDL probes and assertions, not for application writes. */
    public void execute(String sql) {
        try (Connection connection = dataSource.getConnection();
             Statement statement = connection.createStatement()) {
            statement.execute(sql);
        } catch (SQLException error) {
            throw new IllegalStateException("test_db_statement_failed: " + sql, error);
        }
    }

    /** True when the database carries a table with that name. */
    public boolean hasTable(String table) {
        try (Connection connection = dataSource.getConnection();
             Statement statement = connection.createStatement();
             var rows = statement.executeQuery(
                     "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = '" + table + "'")) {
            return rows.next() && rows.getLong(1) == 1;
        } catch (SQLException error) {
            throw new IllegalStateException("test_db_inspect_failed", error);
        }
    }

    private void pragma(String pragma) {
        execute("PRAGMA " + pragma);
    }

    /** Delete the database and its marker: a test must not leave a file behind. */
    @Override
    public void close() {
        for (String suffix : List.of("", "-wal", "-shm")) {
            try {
                Files.deleteIfExists(Path.of(file + suffix));
            } catch (IOException ignored) {
                // a leftover file in a build directory must not fail the test
            }
        }
        try {
            Files.deleteIfExists(marker);
        } catch (IOException ignored) {
            // same
        }
    }
}
