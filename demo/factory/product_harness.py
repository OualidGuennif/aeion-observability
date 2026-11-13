"""Protected JUnit/Quarkus test harness oracle for feature 003.

Runs inside an isolated ProductUnitRunner copy of the packaged workspace AFTER
candidate unit tests so candidate tests cannot forge or alter the verifier.
"""
import hashlib
import shutil
import tempfile
from pathlib import Path

from .checks import _compiler_errors, _failed_tests, _junit_failures
from .product_unit import ProductUnitRunner

ORACLE_CLASS = 'local.aeion.forum.FactoryHarness003OracleTest'
ORACLE_REL_PATH = 'demo/forum-app/src/test/java/local/aeion/forum/FactoryHarness003OracleTest.java'

ORACLE_JAVA = """package local.aeion.forum;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import io.quarkus.test.common.QuarkusTestResourceLifecycleManager;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import org.junit.jupiter.api.Test;

class FactoryHarness003OracleTest {

    @Test
    void twoSuitesRunConcurrentlyWithoutInterfering() throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(2);
        try {
            List<Callable<String>> suites = List.of(
                    () -> writeAndRead("oracle-a", "alpha"),
                    () -> writeAndRead("oracle-b", "beta"));
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
    void aRowLeftByOneDatabaseIsAbsentFromTheNext() throws Exception {
        try (EphemeralDatabase first = EphemeralDatabase.create()) {
            first.execute("INSERT INTO settings(name, value, updated_ns) VALUES ('oracle.leftover', 'yes', 1)");
            assertEquals(1, count(first, "settings"));
        }
        try (EphemeralDatabase second = EphemeralDatabase.create()) {
            assertEquals(0, count(second, "settings"));
        }
    }

    @Test
    void refusesUnmarkedDatabasesBeforeAnyDdl() {
        IllegalStateException unmarked = assertThrows(IllegalStateException.class,
                () -> EphemeralDatabase.createAt("someone-elses-database"));
        assertFalse(unmarked.getCause() instanceof SQLException,
                "unmarked database refusal must happen before any JDBC connection or DDL");
        IllegalStateException lookalike = assertThrows(IllegalStateException.class,
                () -> EphemeralDatabase.createAt("agora_test_prod"));
        assertFalse(lookalike.getCause() instanceof SQLException,
                "lookalike database refusal must happen before any JDBC connection or DDL");
    }

    @Test
    void refusesUnapprovedHostBeforeAnyDdl() {
        EphemeralDatabase.AdminCredentials original = EphemeralDatabase.adminCredentials;
        EphemeralDatabase.adminCredentials = () -> new String[] {
                "jdbc:postgresql://unapproved.example.invalid:5432/postgres", "admin", "secret" };
        try {
            RuntimeException refusal = assertThrows(RuntimeException.class, EphemeralDatabase::create);
            assertFalse(refusal.getCause() instanceof SQLException,
                    "unapproved host must be refused before attempting any JDBC connection or DDL");
        } finally {
            EphemeralDatabase.adminCredentials = original;
        }
    }

    @Test
    void setupFailureNeverDropsPreExistingApplicationRole() throws Exception {
        String[] admin = EphemeralDatabase.adminCredentials.get();
        assertNotNull(admin, "fixture admin credentials are required");
        String existingRole = "agora_app_deadbeef0001";
        String targetDb = "agora_test_deadbeef0001";
        try (Connection connection = DriverManager.getConnection(admin[0], admin[1], admin[2]);
             Statement statement = connection.createStatement()) {
            statement.execute("DROP ROLE IF EXISTS " + existingRole);
            statement.execute("CREATE ROLE " + existingRole + " LOGIN PASSWORD 'preexisting-pass'");
        }
        try {
            assertThrows(RuntimeException.class, () -> EphemeralDatabase.createAt(targetDb));
            try (Connection connection = DriverManager.getConnection(admin[0], admin[1], admin[2]);
                 PreparedStatement query = connection.prepareStatement(
                         "SELECT COUNT(*) FROM pg_roles WHERE rolname = ?")) {
                query.setString(1, existingRole);
                try (ResultSet rows = query.executeQuery()) {
                    rows.next();
                    assertEquals(1L, rows.getLong(1),
                            "teardown/close must only drop roles created by this instance, never pre-existing roles");
                }
            }
        } finally {
            try (Connection connection = DriverManager.getConnection(admin[0], admin[1], admin[2]);
                 Statement statement = connection.createStatement()) {
                statement.execute("DROP DATABASE IF EXISTS " + targetDb + " WITH (FORCE)");
                statement.execute("DROP ROLE IF EXISTS " + existingRole);
            }
        }
    }

    @Test
    void quarkusTestDatabaseImplementsSpiTestInjector() throws Exception {
        Method inject = QuarkusTestDatabase.class.getDeclaredMethod(
                "inject", QuarkusTestResourceLifecycleManager.TestInjector.class);
        assertTrue(Modifier.isPublic(inject.getModifiers()),
                "QuarkusTestDatabase.inject(TestInjector) must be public");
    }

    @Test
    void frozenClockAndSeededRandomSourceAreDeterministic() throws Exception {
        try (EphemeralDatabase first = EphemeralDatabase.create();
             EphemeralDatabase second = EphemeralDatabase.create()) {
            assertTrue(first.clock().frozen(), "ephemeral database clock must start frozen");
            assertEquals(first.clock().nowNs(), second.clock().nowNs(),
                    "frozen clock must start deterministically across instances");
            Random r1 = extractSeededRandom(first);
            Random r2 = extractSeededRandom(second);
            assertNotNull(r1, "EphemeralDatabase must expose a seeded java.util.Random source");
            assertNotNull(r2, "EphemeralDatabase must expose a seeded java.util.Random source");
            assertEquals(r1.nextLong(), r2.nextLong(),
                    "seeded random source must produce deterministic sequence across instances");
        }
    }

    private static Random extractSeededRandom(EphemeralDatabase db) throws Exception {
        for (Method m : EphemeralDatabase.class.getDeclaredMethods()) {
            if (m.getParameterCount() == 0 && Random.class.isAssignableFrom(m.getReturnType())) {
                m.setAccessible(true);
                return (Random) m.invoke(db);
            }
        }
        for (Field f : EphemeralDatabase.class.getDeclaredFields()) {
            if (Random.class.isAssignableFrom(f.getType())) {
                f.setAccessible(true);
                return (Random) f.get(db);
            }
        }
        return null;
    }

    private static String writeAndRead(String name, String value) throws Exception {
        try (EphemeralDatabase database = EphemeralDatabase.create()) {
            database.execute("INSERT INTO settings(name, value, updated_ns) VALUES ('" + name + "', '" + value + "', 1)");
            try (Connection connection = database.dataSource().getConnection();
                 Statement statement = connection.createStatement();
                 ResultSet rows = statement.executeQuery("SELECT value FROM settings WHERE name = '" + name + "'")) {
                return rows.next() ? rows.getString(1) : "no row";
            }
        }
    }

    private static long count(EphemeralDatabase database, String table) throws Exception {
        try (Connection connection = database.dataSource().getConnection();
             Statement statement = connection.createStatement();
             ResultSet rows = statement.executeQuery("SELECT COUNT(*) FROM " + table)) {
            return rows.next() ? rows.getLong(1) : -1;
        }
    }
}
"""


def verify_harness(runner, snapshot, timeout_seconds):
    """Run the immutable Feature 003 JUnit harness oracle inside an isolated workspace."""
    required = (
        snapshot / 'demo/forum-app/src/test/java/local/aeion/forum/EphemeralDatabase.java',
        snapshot / 'demo/forum-app/src/test/java/local/aeion/forum/QuarkusTestDatabase.java',
    )
    if not all(path.is_file() for path in required):
        return False, 'registered_harness_oracle_failed', {
            'failed_tests': ['EphemeralDatabase or QuarkusTestDatabase missing'],
        }
    with tempfile.TemporaryDirectory(prefix='aeion-harness-oracle-') as temporary:
        harness_snapshot = Path(temporary) / 'harness-repo'
        shutil.copytree(
            snapshot,
            harness_snapshot,
            symlinks=True,
            ignore=shutil.ignore_patterns('.git', 'build', 'node_modules'),
        )
        oracle_path = harness_snapshot / ORACLE_REL_PATH
        if oracle_path.exists():
            return False, 'registered_harness_oracle_collision', {}
        oracle_path.parent.mkdir(parents=True, exist_ok=True)
        oracle_path.write_text(ORACLE_JAVA, encoding='utf-8')
        command = [
            str(runner.tools_dir / 'gradle-9.8.2/bin/gradle'),
            '-p',
            str(harness_snapshot / 'demo/forum-app'),
            'test',
            '--tests',
            ORACLE_CLASS,
            '--offline',
            '--console=plain',
            '--no-daemon',
        ]
        unit_runner = ProductUnitRunner(
            runner.controller,
            docker=runner.docker,
            tools_dir=runner.tools_dir,
            cache_dir=runner.cache_dir,
        )
        tested = unit_runner(command, cwd=harness_snapshot, timeout=max(30, int(timeout_seconds)))
        output = (tested.stdout or '') + '\n' + (tested.stderr or '')
        compiler_errors = _compiler_errors(output)
        if compiler_errors:
            return False, 'product_compile_failed', {
                'returncode': tested.returncode,
                'compiler_errors': compiler_errors,
            }
        reports = harness_snapshot / 'demo/forum-app/build/test-results/test'
        failures = _junit_failures(reports, _failed_tests(output))
        if tested.returncode != 0 or failures:
            return False, 'registered_harness_oracle_failed', {
                'returncode': tested.returncode,
                'failed_tests': failures,
                'oracle_sha256': hashlib.sha256(ORACLE_JAVA.encode('utf-8')).hexdigest(),
            }
        xml_report = reports / f'TEST-{ORACLE_CLASS}.xml'
        if not xml_report.is_file():
            return False, 'registered_harness_oracle_failed', {
                'returncode': tested.returncode,
                'failed_tests': ['oracle JUnit XML report missing'],
            }
        return True, 'passed', {
            'oracle_sha256': hashlib.sha256(ORACLE_JAVA.encode('utf-8')).hexdigest(),
        }
