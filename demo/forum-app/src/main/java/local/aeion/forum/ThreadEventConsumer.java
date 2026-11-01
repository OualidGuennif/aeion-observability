package local.aeion.forum;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.quarkus.runtime.ShutdownEvent;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;
import java.time.Duration;
import java.util.List;
import java.util.Properties;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

/**
 * Feature 011: the consumer applies each event once, and says so when it recognises a replay.
 *
 * Kafka gives at-least-once delivery here on purpose: offsets are committed only after a record has
 * been applied, so a crash replays instead of losing. That is only safe because the ledger makes the
 * apply idempotent — a duplicate event id is a no-op, never a second thread.
 *
 * The handler is separated from the poll loop so a test can drive it without a broker.
 */
@ApplicationScoped
public class ThreadEventConsumer {

    @Inject
    ThreadService threads;

    @Inject
    ObjectMapper json;

    @Inject
    KafkaTopics topics;

    @Inject
    Logger log;

    @ConfigProperty(name = "agora.kafka.enabled", defaultValue = "false")
    boolean enabled;

    @ConfigProperty(name = "agora.kafka.bootstrap.servers", defaultValue = "127.0.0.1:9092")
    String bootstrap;

    @ConfigProperty(name = "agora.kafka.topic", defaultValue = "agora.threads")
    String topic;

    @ConfigProperty(name = "agora.kafka.group", defaultValue = "agora-forum")
    String group;

    private volatile KafkaConsumer<String, String> consumer;
    private volatile java.lang.Thread loop;
    private volatile boolean stopping;

    /** The outcome of one record: what it was, and whether it changed anything. */
    public record Outcome(String eventId, boolean applied) {
    }

    /**
     * Apply one event payload. A duplicate event id is a no-op; a payload with no event id is a
     * refusal, because an event nobody can deduplicate must not be applied at all.
     */
    public Outcome handle(String payload) {
        if (payload == null || payload.isBlank()) {
            throw new IllegalStateException("event_empty");
        }
        String eventId;
        try {
            JsonNode node = json.readTree(payload);
            eventId = node.path("event_id").asText("");
        } catch (com.fasterxml.jackson.core.JsonProcessingException malformed) {
            throw new IllegalStateException("event_not_json", malformed);
        }
        if (eventId.isBlank()) {
            throw new IllegalStateException("event_id_missing");
        }
        boolean applied = threads.recordEvent(eventId, topic, payload);
        if (!applied) {
            log.infof("event %s already applied: replay ignored", eventId);
        }
        return new Outcome(eventId, applied);
    }

    void onStart(@Observes StartupEvent event) {
        if (!enabled) {
            log.info("kafka consumer disabled: no thread-events are read");
            return;
        }
        loop = new java.lang.Thread(this::consume, "agora-thread-consumer");
        loop.setDaemon(true);
        loop.start();
        log.infof("kafka consumer subscribed to %s as %s", topic, group);
    }

    void onStop(@Observes ShutdownEvent event) {
        stopping = true;
        KafkaConsumer<String, String> current = consumer;
        if (current != null) {
            current.wakeup();
        }
        if (loop != null) {
            try {
                loop.join(Duration.ofSeconds(5).toMillis());
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
            }
        }
    }

    private void consume() {
        while (!stopping && !Thread.currentThread().isInterrupted()) {
            try {
                pollUntilFailure();
            } catch (org.apache.kafka.common.errors.WakeupException stoppingSignal) {
                break;
            } catch (RuntimeException failure) {
                // A broker that went away is an outage, not the end of the consumer: rebuild and
                // retry, because the alternative is a forum that silently stops recording events.
                log.warnf("consumer reconnecting in 2s: %s", failure.getMessage());
                sleep(Duration.ofSeconds(2));
            } finally {
                closeConsumer();
            }
        }
    }

    private void pollUntilFailure() {
        Properties properties = new Properties();
        properties.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrap);
        properties.put(ConsumerConfig.GROUP_ID_CONFIG, group);
        properties.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        properties.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        properties.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
        properties.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        properties.put(ConsumerConfig.CLIENT_ID_CONFIG, "agora-forum-consumer");
        topics.ensure(topic);
        consumer = new KafkaConsumer<>(properties);
        consumer.subscribe(List.of(topic));
        while (!stopping && !Thread.currentThread().isInterrupted()) {
            ConsumerRecords<String, String> records = consumer.poll(Duration.ofSeconds(1));
            boolean clean = true;
            for (ConsumerRecord<String, String> record : records) {
                try {
                    handle(record.value());
                } catch (RuntimeException failure) {
                    // Do not commit past a record we could not apply: it is replayed, not lost.
                    clean = false;
                    log.warnf("event at offset %d not applied: %s", record.offset(), failure.getMessage());
                }
            }
            if (clean && !records.isEmpty()) {
                consumer.commitSync();
            }
        }
    }

    private void closeConsumer() {
        KafkaConsumer<String, String> current = consumer;
        consumer = null;
        if (current == null) {
            return;
        }
        try {
            current.close(Duration.ofSeconds(5));
        } catch (RuntimeException ignored) {
            // closing a broken consumer must not mask the reason it broke
        }
    }

    private static void sleep(Duration duration) {
        try {
            java.lang.Thread.sleep(duration.toMillis());
        } catch (InterruptedException interrupted) {
            java.lang.Thread.currentThread().interrupt();
        }
    }
}
