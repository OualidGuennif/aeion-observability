package local.aeion.forum;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** One forum thread; the migration owns the table, Hibernate only maps it. */
@Entity
@Table(name = "threads")
public class ForumThread {

    @Id
    @Column(name = "id", nullable = false, length = 36)
    public String id;

    @Column(name = "title", nullable = false, length = 200)
    public String title;

    @Column(name = "body", nullable = false, length = 4000)
    public String body;

    @Column(name = "author_id", nullable = false, length = 36)
    public String authorId;

    @Column(name = "created_ns", nullable = false)
    public long createdNs;

    public ForumThread() {
    }

    public ForumThread(String id, String title, String body, String authorId, long createdNs) {
        this.id = id;
        this.title = title;
        this.body = body;
        this.authorId = authorId;
        this.createdNs = createdNs;
    }
}
