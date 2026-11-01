package local.aeion.forum;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.time.Duration;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import org.apache.kafka.clients.admin.Admin;
import org.apache.kafka.clients.admin.AdminClientConfig;
import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.common.errors.TopicExistsException;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

/**
 * Feature 011: the topic exists before anyone writes to it.
 *
 * The broker is not trusted to create topics on demand — that setting turns a typo in a topic name
 * into a silently empty stream. The application asks the cluster what exists, creates the topic with
 * an explicit partition count when it is missing, and fails closed when the cluster cannot answer.
 */
@ApplicationScoped
public class KafkaTopics {

    @ConfigProperty(name = "agora.kafka.bootstrap.servers", defaultValue = "127.0.0.1:9092")
    String bootstrap;

    @ConfigProperty(name = "agora.kafka.partitions", defaultValue = "3")
    int partitions;

    @ConfigProperty(name = "agora.kafka.replication", defaultValue = "1")
    short replication;

    @Inject
    Logger log;

    private final Set<String> ensured = ConcurrentHashMap.newKeySet();

    /** Create the topic once per process; returns true when this call created it. */
    public boolean ensure(String topic) {
        if (ensured.contains(topic)) {
            return false;
        }
        Properties properties = new Properties();
        properties.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrap);
        properties.put(AdminClientConfig.REQUEST_TIMEOUT_MS_CONFIG, "5000");
        properties.put(AdminClientConfig.DEFAULT_API_TIMEOUT_MS_CONFIG, "5000");
        try (Admin admin = Admin.create(properties)) {
            boolean exists = admin.listTopics().names().get()
                    .contains(topic);
            if (exists) {
                ensured.add(topic);
                return false;
            }
            admin.createTopics(List.of(new NewTopic(topic, partitions, replication))).all().get();
            ensured.add(topic);
            log.infof("created kafka topic %s (%d partitions)", topic, partitions);
            return true;
        } catch (TopicExistsException raced) {
            ensured.add(topic);
            return false;
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("kafka_unavailable", interrupted);
        } catch (Exception failure) {
            throw new IllegalStateException("kafka_unavailable: " + failure.getClass().getSimpleName(), failure);
        }
    }
}
