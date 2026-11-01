package local.aeion.forum;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.sql.DataSource;

/**
 * Feature 002: the migration engine, with no CDI in it so a test can drive it directly.
 *
 * Every migration is a file listed in {@code <location>/index.txt}, applied in that order, each in
 * its own transaction and recorded in {@code schema_migrations}. Re-running is a no-op because
 * applied versions are read first, and a migration that fails rolls back alone: the database is
 * never left half-migrated, and never records a version it did not apply.
 *
 * The application ({@link MigrationRunner}) and the test harness ({@code EphemeralDatabase}) call
 * this same code, so a test proves the schema a deployment actually gets.
 */
public final class Migrations {

    static final String LEDGER = """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                applied_ns INTEGER NOT NULL
            )
            """;

    private Migrations() {
    }

    /** Apply every pending migration in index order; returns the versions applied now. */
    public static List<String> apply(DataSource dataSource, String location, ForumClock clock) {
        List<String> appliedNow = new ArrayList<>();
        try (Connection connection = dataSource.getConnection()) {
            connection.setAutoCommit(true);
            try (Statement statement = connection.createStatement()) {
                statement.executeUpdate(LEDGER);
            }
            List<String> alreadyApplied = appliedVersions(connection);
            for (String file : index(location)) {
                String version = version(file);
                if (alreadyApplied.contains(version)) {
                    continue;
                }
                applyOne(connection, location, version, file, clock.nowNs());
                appliedNow.add(version);
            }
        } catch (SQLException error) {
            throw new IllegalStateException("migration_failed: " + error.getMessage(), error);
        }
        return appliedNow;
    }

    /** The applied rows, oldest version first. */
    public static List<Map<String, Object>> applied(DataSource dataSource) {
        List<Map<String, Object>> rows = new ArrayList<>();
        try (Connection connection = dataSource.getConnection();
             Statement statement = connection.createStatement();
             ResultSet result = statement.executeQuery(
                     "SELECT version, name, applied_ns FROM schema_migrations ORDER BY version")) {
            while (result.next()) {
                Map<String, Object> row = new LinkedHashMap<>();
                row.put("version", result.getString(1));
                row.put("name", result.getString(2));
                row.put("applied_ns", result.getLong(3));
                rows.add(row);
            }
        } catch (SQLException error) {
            throw new IllegalStateException("schema_unreadable", error);
        }
        return rows;
    }

    /** The migration files the index lists, in order. */
    public static List<String> index(String location) {
        List<String> files = new ArrayList<>();
        for (String line : read(location, "index.txt").split("\n")) {
            String name = line.strip();
            if (!name.isEmpty() && !name.startsWith("#")) {
                files.add(name);
            }
        }
        if (files.isEmpty()) {
            throw new IllegalStateException("migration_index_empty: " + location);
        }
        return files;
    }

    /** The version a file declares, the part before {@code __}. */
    public static String version(String file) {
        int marker = file.indexOf("__");
        if (marker <= 0) {
            throw new IllegalStateException("migration_name_invalid: " + file);
        }
        return file.substring(0, marker);
    }

    private static void applyOne(Connection connection, String location, String version, String file, long nowNs)
            throws SQLException {
        List<String> statements = statements(read(location, file));
        if (statements.isEmpty()) {
            // A listed file that yields nothing is a broken migration, never a silent no-op.
            throw new IllegalStateException("migration_empty: " + file);
        }
        connection.setAutoCommit(false);
        try {
            for (String statement : statements) {
                try (Statement executor = connection.createStatement()) {
                    executor.executeUpdate(statement);
                }
            }
            try (PreparedStatement record = connection.prepareStatement(
                    "INSERT INTO schema_migrations(version, name, applied_ns) VALUES (?, ?, ?)")) {
                record.setString(1, version);
                record.setString(2, file);
                record.setLong(3, nowNs);
                record.executeUpdate();
            }
            connection.commit();
        } catch (SQLException | RuntimeException failure) {
            connection.rollback();
            throw failure;
        } finally {
            connection.setAutoCommit(true);
        }
    }

    private static List<String> appliedVersions(Connection connection) throws SQLException {
        List<String> versions = new ArrayList<>();
        try (Statement statement = connection.createStatement();
             ResultSet rows = statement.executeQuery("SELECT version FROM schema_migrations")) {
            while (rows.next()) {
                versions.add(rows.getString(1));
            }
        }
        return versions;
    }

    static String read(String location, String name) {
        String resource = "/" + location + "/" + name;
        try (InputStream stream = Migrations.class.getResourceAsStream(resource)) {
            if (stream == null) {
                throw new IllegalStateException("migration_missing: " + resource);
            }
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(stream, StandardCharsets.UTF_8))) {
                StringBuilder text = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    text.append(line).append('\n');
                }
                return text.toString();
            }
        } catch (IOException error) {
            throw new IllegalStateException("migration_unreadable: " + resource, error);
        }
    }

    /**
     * Split a migration file into executable statements.
     *
     * Whole-line comments are removed before splitting: a file that opens with a {@code --} header
     * used to lose its first statement, which silently left a table uncreated while the ledger
     * recorded the version as applied. Trailing comments on a statement line are kept, SQLite
     * accepts them.
     */
    static List<String> statements(String sql) {
        StringBuilder body = new StringBuilder();
        for (String line : sql.split("\n")) {
            if (line.stripLeading().startsWith("--")) {
                continue;
            }
            body.append(line).append('\n');
        }
        List<String> statements = new ArrayList<>();
        for (String chunk : body.toString().split(";\\s*(?:\\r?\\n|$)")) {
            String statement = chunk.strip();
            if (!statement.isEmpty()) {
                statements.add(statement);
            }
        }
        return statements;
    }
}
