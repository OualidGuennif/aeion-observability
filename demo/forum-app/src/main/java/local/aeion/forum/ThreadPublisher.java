package local.aeion.forum;

import io.quarkus.runtime.ShutdownEvent;
import io.quarkus.runtime.StartupEvent;
import io.quarkus.scheduler.Scheduled;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;
import java.util.List;
import org.jboss.logging.Logger;

/**
 * Feature 011: the outbox drain. Nothing here runs inside a request.
 *
 * Each tick takes the oldest unpublished events and hands them to the broker one at a time. A
 * confirmed send marks the row published; a failure records why, leaves the row pending, and ends
 * the tick, so a broker that is down produces backpressure instead of a growing in-memory queue.
 */
@ApplicationScoped
public class ThreadPublisher {

    static final int BATCH = 50;

    @Inject
    ThreadService threads;

    @Inject
    KafkaEventSender sender;

    @Inject
    Logger log;

    private volatile boolean announcedDisabled;

    /** Run every two seconds; a paused application does nothing rather than piling up work. */
    @Scheduled(every = "2s", concurrentExecution = Scheduled.ConcurrentExecution.SKIP)
    void drainOnSchedule() {
        drain();
    }

    void onStart(@Observes StartupEvent event) {
        drain();
    }

    void onStop(@Observes ShutdownEvent event) {
        sender.close();
    }

    /** Returns how many events were published now; a test calls this directly. */
    public int drain() {
        if (!sender.enabled()) {
            if (!announcedDisabled) {
                log.infof("kafka disabled: %d event(s) stay in the outbox", threads.pendingCount());
                announcedDisabled = true;
            }
            return 0;
        }
        List<ThreadService.OutboxRow> pending = threads.pending(BATCH);
        int published = 0;
        for (ThreadService.OutboxRow row : pending) {
            try {
                sender.send(row.topic(), row.eventId(), row.payload());
            } catch (RuntimeException failure) {
                threads.markFailed(row.eventId(), failure.getMessage());
                log.warnf("outbox publish failed for %s: %s", row.eventId(), failure.getMessage());
                break;
            }
            threads.markPublished(row.eventId());
            published++;
        }
        return published;
    }
}
