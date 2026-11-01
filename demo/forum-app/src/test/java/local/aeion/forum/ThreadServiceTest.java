package local.aeion.forum;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.quarkus.test.common.WithTestResource;
import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.InjectMock;
import jakarta.inject.Inject;
import java.sql.Connection;
import java.sql.Statement;
import java.util.List;
import javax.sql.DataSource;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

/**
 * Features 010 and 011 on the running application, with the broker replaced by a mock.
 *
 * The mock is the point: a real broker proves delivery, but only a sender that throws can prove the
 * failure path — the event stays in the outbox with its attempt counted, and the thread is not lost.
 * The scheduler is disabled in the test profile, so every drain here is one the test asked for.
 */
@QuarkusTest
@WithTestResource(QuarkusTestDatabase.class)
class ThreadServiceTest {

    @Inject
    ThreadService threads;

    @Inject
    ThreadPublisher publisher;

    @Inject
    ThreadEventConsumer consumer;

    @Inject
    ForumClock clock;

    @Inject
    DataSource dataSource;

    @InjectMock
    KafkaEventSender sender;

    private static final AuthService.Account AUTHOR =
            new AuthService.Account("author-1", "writer", "member");

    @BeforeEach
    void clean() throws Exception {
        try (Connection connection = dataSource.getConnection();
             Statement statement = connection.createStatement()) {
            for (String table : List.of("threads", "thread_outbox", "thread_event_log")) {
                statement.executeUpdate("DELETE FROM " + table);
            }
        }
        clock.freeze(1_790_000_000_000_000_000L);
        when(sender.enabled()).thenReturn(true);
    }

    @AfterEach
    void release() {
        clock.release();
    }

    @Test
    void aThreadAndItsEventAreStoredTogether() throws Exception {
        ThreadService.ThreadView thread = threads.create(AUTHOR, "agora.threads", "First thread", "Hello there");
        assertEquals(1, threads.pendingCount(), "the event must be queued with the thread");
        List<ThreadService.OutboxRow> pending = threads.pending(10);
        assertEquals(1, pending.size());
        JsonNode event = new ObjectMapper().readTree(pending.get(0).payload());
        assertEquals("thread.created", event.get("type").asText());
        assertEquals(thread.id(), event.get("thread_id").asText());
        assertEquals(AUTHOR.id(), event.get("author_id").asText());
        assertEquals(thread.createdNs(), event.get("created_ns").asLong());
        assertEquals(pending.get(0).eventId(), event.get("event_id").asText());
        assertEquals("agora.threads", pending.get(0).topic());
    }

    @Test
    void refusesAnEmptyTitleOrBody() {
        assertEquals("invalid_title", assertThrows(ThreadService.ThreadException.class,
                () -> threads.create(AUTHOR, "t", "ab", "body")).code());
        assertEquals("invalid_body", assertThrows(ThreadService.ThreadException.class,
                () -> threads.create(AUTHOR, "t", "ok title", "  ")).code());
        assertEquals(0, threads.pendingCount(), "a refused thread must not queue an event");
    }

    @Test
    void publishesOnlyWhenTheBrokerConfirms() {
        threads.create(AUTHOR, "agora.threads", "First thread", "Hello");
        doThrow(new IllegalStateException("broker_unavailable")).when(sender).send(anyString(), anyString(), anyString());
        assertEquals(0, publisher.drain());
        assertEquals(1, threads.pendingCount(), "a failed send leaves the event queued");
        assertEquals(1, threads.pending(10).get(0).attempts(), "the attempt is recorded");

        org.mockito.Mockito.reset(sender);
        when(sender.enabled()).thenReturn(true);
        assertEquals(1, publisher.drain());
        assertEquals(0, threads.pendingCount());
        assertEquals(0, publisher.drain(), "nothing left to publish");
    }

    @Test
    void aDisabledBrokerQueuesInsteadOfFailing() {
        when(sender.enabled()).thenReturn(false);
        threads.create(AUTHOR, "agora.threads", "Offline thread", "Still stored");
        assertEquals(0, publisher.drain());
        assertEquals(1, threads.pendingCount());
        org.mockito.Mockito.verify(sender, org.mockito.Mockito.never())
                .send(anyString(), anyString(), anyString());
    }

    @Test
    void appliesAnEventOnceAndIgnoresAReplay() {
        threads.create(AUTHOR, "agora.threads", "First thread", "Hello");
        String payload = threads.pending(10).get(0).payload();
        ThreadEventConsumer.Outcome first = consumer.handle(payload);
        assertTrue(first.applied());
        ThreadEventConsumer.Outcome second = consumer.handle(payload);
        assertFalse(second.applied(), "a replay must not apply twice");
        assertEquals(first.eventId(), second.eventId());
        assertEquals(1, threads.eventCount());
    }

    @Test
    void refusesAnEventWithoutAnIdOrJson() {
        assertEquals("event_id_missing", assertThrows(IllegalStateException.class,
                () -> consumer.handle("{\"type\":\"thread.created\"}")).getMessage());
        assertThrows(IllegalStateException.class, () -> consumer.handle("not json"));
        assertThrows(IllegalStateException.class, () -> consumer.handle("  "));
        assertEquals(0, threads.eventCount());
    }

    @Test
    void listsAndFindsThreadsNewestFirst() {
        threads.create(AUTHOR, "agora.threads", "Older", "one");
        clock.advance(1_000_000_000L);
        ThreadService.ThreadView newer = threads.create(AUTHOR, "agora.threads", "Newer", "two");
        List<ThreadService.ThreadView> recent = threads.recent(10);
        assertEquals(2, recent.size());
        assertEquals(newer.id(), recent.get(0).id());
        assertTrue(threads.find(newer.id()).isPresent());
        assertTrue(threads.find("absent").isEmpty());
    }
}
