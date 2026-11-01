package local.aeion.forum;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.persistence.EntityManager;
import jakarta.transaction.Transactional;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/**
 * Feature 010: a thread is stored and its event is queued in the same transaction.
 *
 * The transactional outbox is the whole point: publishing inside the request would lose the event
 * when the broker is down, and publishing after the commit would lose it when the process dies
 * between the two. One transaction means the event exists exactly when the thread does, and the
 * publisher is free to be late, retried or restarted.
 *
 * Feature 011: the consumer side is idempotent on the event id, so at-least-once delivery applies
 * once. A replay is not an error; it is a no-op that says so.
 */
@ApplicationScoped
public class ThreadService {

    static final int MAX_TITLE = 200;
    static final int MAX_BODY = 4000;
    static final int MIN_TITLE = 3;

    @Inject
    EntityManager entityManager;

    @Inject
    ForumClock clock;

    @Inject
    ObjectMapper json;

    public record ThreadView(String id, String title, String body, String authorId, long createdNs) {
    }

    public record OutboxRow(String eventId, String topic, String payload, int attempts) {
    }

    /** Store the thread and its event together; nothing is published here. */
    @Transactional
    public ThreadView create(AuthService.Account author, String topic, String title, String rawBody) {
        String cleanTitle = title == null ? "" : title.strip();
        String body = rawBody == null ? "" : rawBody.strip();
        if (cleanTitle.length() < MIN_TITLE || cleanTitle.length() > MAX_TITLE) {
            throw new ThreadException("invalid_title");
        }
        if (body.isEmpty() || body.length() > MAX_BODY) {
            throw new ThreadException("invalid_body");
        }
        long now = clock.nowNs();
        ForumThread thread = new ForumThread(UUID.randomUUID().toString(), cleanTitle, body, author.id(), now);
        entityManager.persist(thread);
        entityManager.flush();
        String eventId = UUID.randomUUID().toString();
        String payload = event(eventId, thread);
        entityManager.createNativeQuery(
                        "INSERT INTO thread_outbox(event_id, topic, payload, created_ns, attempts) "
                                + "VALUES (?, ?, ?, ?, 0)")
                .setParameter(1, eventId)
                .setParameter(2, topic)
                .setParameter(3, payload)
                .setParameter(4, now)
                .executeUpdate();
        return view(thread);
    }

    /** The event body: one shape, built here, so producer and consumer agree by construction. */
    String event(String eventId, ForumThread thread) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("event_id", eventId);
        body.put("type", "thread.created");
        body.put("thread_id", thread.id);
        body.put("author_id", thread.authorId);
        body.put("title", thread.title);
        body.put("created_ns", thread.createdNs);
        try {
            return json.writeValueAsString(body);
        } catch (com.fasterxml.jackson.core.JsonProcessingException impossible) {
            throw new IllegalStateException("event_unserialisable", impossible);
        }
    }

    @Transactional
    public List<ThreadView> recent(int limit) {
        int cap = Math.clamp(limit, 1, 100);
        return entityManager.createQuery("select t from ForumThread t order by t.createdNs desc", ForumThread.class)
                .setMaxResults(cap)
                .getResultList()
                .stream()
                .map(ThreadService::view)
                .toList();
    }

    @Transactional
    public Optional<ThreadView> find(String id) {
        return Optional.ofNullable(entityManager.find(ForumThread.class, id)).map(ThreadService::view);
    }

    /** The oldest unpublished events, in insertion order. */
    @Transactional
    public List<OutboxRow> pending(int limit) {
        int cap = Math.clamp(limit, 1, 500);
        List<?> rows = entityManager.createNativeQuery(
                        "SELECT event_id, topic, payload, attempts FROM thread_outbox "
                                + "WHERE published_ns IS NULL ORDER BY created_ns LIMIT ?")
                .setParameter(1, cap)
                .getResultList();
        List<OutboxRow> pending = new ArrayList<>();
        for (Object row : rows) {
            Object[] columns = (Object[]) row;
            pending.add(new OutboxRow((String) columns[0], (String) columns[1], (String) columns[2],
                    ((Number) columns[3]).intValue()));
        }
        return pending;
    }

    @Transactional
    public boolean markPublished(String eventId) {
        return entityManager.createNativeQuery(
                        "UPDATE thread_outbox SET published_ns = ?, last_error = NULL "
                                + "WHERE event_id = ? AND published_ns IS NULL")
                .setParameter(1, clock.nowNs())
                .setParameter(2, eventId)
                .executeUpdate() == 1;
    }

    @Transactional
    public void markFailed(String eventId, String error) {
        entityManager.createNativeQuery(
                        "UPDATE thread_outbox SET attempts = attempts + 1, last_error = ? "
                                + "WHERE event_id = ? AND published_ns IS NULL")
                .setParameter(1, error == null ? "unknown" : error.substring(0, Math.min(200, error.length())))
                .setParameter(2, eventId)
                .executeUpdate();
    }

    /**
     * Record a consumed event once. Returns false for a replay: the caller must not treat that as
     * a failure, and must not apply the event twice.
     */
    @Transactional
    public boolean recordEvent(String eventId, String topic, String payload) {
        int inserted = entityManager.createNativeQuery(
                        "INSERT INTO thread_event_log(event_id, topic, received_ns, payload) "
                                + "VALUES (?, ?, ?, ?) ON CONFLICT(event_id) DO NOTHING")
                .setParameter(1, eventId)
                .setParameter(2, topic)
                .setParameter(3, clock.nowNs())
                .setParameter(4, payload)
                .executeUpdate();
        return inserted == 1;
    }

    @Transactional
    public long eventCount() {
        return ((Number) entityManager.createNativeQuery("SELECT COUNT(*) FROM thread_event_log")
                .getSingleResult()).longValue();
    }

    @Transactional
    public long pendingCount() {
        return ((Number) entityManager.createNativeQuery(
                "SELECT COUNT(*) FROM thread_outbox WHERE published_ns IS NULL").getSingleResult()).longValue();
    }

    private static ThreadView view(ForumThread thread) {
        return new ThreadView(thread.id, thread.title, thread.body, thread.authorId, thread.createdNs);
    }

    /** A refusal the API can turn into a 400 without leaking anything. */
    public static class ThreadException extends RuntimeException {
        private final String code;

        public ThreadException(String code) {
            super(code);
            this.code = code;
        }

        public String code() {
            return code;
        }
    }
}
