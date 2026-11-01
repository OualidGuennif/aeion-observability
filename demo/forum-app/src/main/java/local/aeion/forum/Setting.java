package local.aeion.forum;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** One settings row; the migration owns the table, Hibernate only maps it. */
@Entity
@Table(name = "settings")
public class Setting {

    @Id
    @Column(name = "name", nullable = false, length = 120)
    public String name;

    @Column(name = "value", nullable = false, length = 4000)
    public String value;

    @Column(name = "updated_ns", nullable = false)
    public long updatedNs;

    public Setting() {
    }

    public Setting(String name, String value, long updatedNs) {
        this.name = name;
        this.value = value;
        this.updatedNs = updatedNs;
    }
}
