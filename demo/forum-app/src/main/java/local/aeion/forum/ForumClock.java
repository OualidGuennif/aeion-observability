package local.aeion.forum;

import jakarta.enterprise.context.ApplicationScoped;
import java.util.concurrent.atomic.AtomicLong;

/**
 * The one place the application reads the time.
 *
 * Production uses the wall clock. A test freezes it and advances it, so an expiry is proven in
 * milliseconds instead of by sleeping for fifteen minutes, and a decision stays a function of
 * (state, inputs, now) instead of depending on when the suite happened to run.
 */
@ApplicationScoped
public class ForumClock {

    private static final long RUNNING = Long.MIN_VALUE;

    private final AtomicLong frozenNs = new AtomicLong(RUNNING);

    /** Nanoseconds since the epoch, real or frozen. */
    public long nowNs() {
        long frozen = frozenNs.get();
        return frozen == RUNNING ? System.currentTimeMillis() * 1_000_000L : frozen;
    }

    /** Stop the clock at {@code ns}; every later read returns it until {@link #release()}. */
    public void freeze(long ns) {
        frozenNs.set(ns);
    }

    /** Move a frozen clock forward; a running clock is left alone and says so. */
    public boolean advance(long byNs) {
        if (byNs <= 0) {
            throw new IllegalArgumentException("advance_must_be_positive");
        }
        long frozen = frozenNs.get();
        if (frozen == RUNNING) {
            return false;
        }
        frozenNs.set(frozen + byNs);
        return true;
    }

    public boolean frozen() {
        return frozenNs.get() != RUNNING;
    }

    /** Return to the wall clock. */
    public void release() {
        frozenNs.set(RUNNING);
    }
}
