"""The release service: staging, promotion, canary traffic, samples and flags.

It is the only place that couples the three halves of a release — the content-addressed release
record (`release.py`), the traffic that proves it (`demo/deploy/playground.py`) and the monitor that
judges it (`canary.py`) — and it is deliberately boring: every entry point takes `now`, persists
the whole record atomically, and refuses anything it cannot prove.

Invariants:
  * a staged release never receives production traffic;
  * `percent` only grows through `advance` or `deploy_now`, and only when the gate says `continue`;
  * a policy violation holds or rolls back on the same tick, never on a later one;
  * samples come from the balancer, never from the caller.
"""
import json
import time

from . import canary, release


# One exception class for the whole release path: the record's own refusals are the service's.
ReleaseError = release.ReleaseError


class ReleaseService:
    def __init__(self, store, playground, work_dir, scale=1.0, clock=None,
                 sample_interval_seconds=60, page_size=48):
        self.store = store
        self.playground = playground
        self.work_dir = work_dir
        self.scale = scale
        self.clock = clock or time.time_ns
        self.sample_interval_ns = int(sample_interval_seconds * 1_000_000_000)
        self.page_size = page_size
        self._restore_staging()

    def _restore_staging(self):
        """A release staged by another process (a script, a restart) is still staged here."""
        record = self._load()
        if record is None:
            return
        try:
            self.playground.deploy("staging", self._manifest(record))
        except OSError:
            pass

    # ------------------------------------------------------------------ persistence
    def _key(self, release_id):
        return f"release:{release_id}"

    def _save(self, record):
        self.store.meta_set(self._key(record["release_id"]), json.dumps(record, sort_keys=True))
        if self.store.meta_get("release:current") != record["release_id"]:
            self.store.meta_set("release:current", record["release_id"])

    def _load(self):
        release_id = self.store.meta_get("release:current")
        if not release_id:
            return None
        raw = self.store.meta_get(self._key(release_id))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except ValueError as exc:
            raise ReleaseError("release_record_corrupt") from exc

    def _samples(self, release_id):
        raw = self.store.meta_get(f"samples:{release_id}")
        try:
            return json.loads(raw) if raw else []
        except ValueError:
            return []

    def _save_samples(self, release_id, samples):
        self.store.meta_set(f"samples:{release_id}", json.dumps(samples[-self.page_size:]))

    # ------------------------------------------------------------------ release lifecycle
    def current(self):
        return self._load()

    def stage(self, features, flags=None, now=None):
        """Create a release from built features and put it in staging only."""
        now = self.clock() if now is None else now
        existing = self._load()
        if existing and existing["release_id"] == release.release_id(
                [{"id": f["id"], "digest": f["digest"]} for f in features]):
            return existing
        record = release.create(features, now_ns=now, flags=flags, scale=self.scale)
        self.playground.deploy("staging", self._manifest(record))
        self._save(record)
        self._save_samples(record["release_id"], [])
        return record

    def _manifest(self, record):
        return {"release_id": record["release_id"], "features": record["features"],
                "work_dir": str(self.work_dir)}

    def _require(self, release_id=None):
        record = self._load()
        if record is None:
            raise ReleaseError("no_release")
        if release_id and record["release_id"] != release_id:
            raise ReleaseError("release_mismatch")
        return record

    def validate(self, release_id=None, now=None):
        """The front's Validate button: the release may now reach production, at the first step."""
        now = self.clock() if now is None else now
        record = self._require(release_id)
        if record["state"] != release.STATE_STAGED:
            raise ReleaseError(f"cannot_validate_from:{record['state']}")
        self.playground.deploy("canary", self._manifest(record))
        if not self.playground.has_release("stable"):
            # The first release also bootstraps production: there is no previous version to keep,
            # and a 25/75 split against an empty slot would serve 503s to three visitors in four.
            self.playground.deploy("stable", self._manifest(record))
            release._record(record, now, "stable_bootstrapped", "first release serves production")
        release.promote(record, now_ns=now)
        self.playground.set_percent(record["percent"])
        self._save(record)
        return record

    def deploy_now(self, release_id=None, now=None):
        """The front's "immediate full deploy": 100% now, dwells skipped and recorded."""
        now = self.clock() if now is None else now
        record = self._require(release_id)
        if record["state"] == release.STATE_STAGED:
            self.playground.deploy("canary", self._manifest(record))
        release.deploy_now(record, now_ns=now)
        self.playground.set_percent(100)
        self._save(record)
        return record

    def advance(self, release_id=None, now=None):
        """Move to the next step when the dwell is over and the last sample series allows it."""
        now = self.clock() if now is None else now
        record = self._require(release_id)
        gate = self.gate(record)
        release.advance(record, now_ns=now, verdict=gate["verdict"])
        self.playground.set_percent(record["percent"])
        self._save(record)
        return record

    def resume(self, release_id=None, now=None):
        """Leave a hold when the evidence is good again, without widening the rollout."""
        now = self.clock() if now is None else now
        record = self._require(release_id)
        if record["state"] != release.STATE_HELD:
            raise ReleaseError(f"cannot_resume_from:{record['state']}")
        gate = self.gate(record)
        if gate["verdict"] != "continue":
            raise ReleaseError(f"gate_blocks_resume:{gate['verdict']}")
        record["state"] = release.STATE_CANARY
        record["history"].append({"at_ns": now, "event": "resumed", "detail": f"{record['percent']}%"})
        self._save(record)
        return record

    def rollback(self, release_id=None, reason="operator", now=None):
        now = self.clock() if now is None else now
        record = self._require(release_id)
        release.rollback(record, now_ns=now, reason=reason)
        self.playground.set_percent(0)
        self._save(record)
        return record

    # ------------------------------------------------------------------ monitoring
    def gate(self, record=None):
        record = record or self._load()
        if record is None:
            return {"verdict": "hold", "reason": "no_release", "samples": 0}
        return canary.evaluate(self._samples(record["release_id"]))

    def sample(self, record=None, now=None):
        """Record one reading of what the balancer actually served."""
        now = self.clock() if now is None else now
        record = record or self._require()
        samples = canary.record(self._samples(record["release_id"]), self.playground.sample(),
                                limit=self.page_size)
        self._save_samples(record["release_id"], samples)
        record["last_sample_ns"] = now
        self._save(record)
        return samples[-1]

    def tick(self, now=None):
        """One monitoring pass: sample if due, then hold, roll back or advance."""
        now = self.clock() if now is None else now
        record = self._load()
        if record is None or record["state"] not in {release.STATE_CANARY, release.STATE_HELD}:
            return None
        last = record.get("last_sample_ns") or 0
        if now - last >= self.sample_interval_ns:
            self.sample(record, now=now)
            record = self._load()
        gate = self.gate(record)
        if gate["verdict"] == "rollback" and record["state"] == release.STATE_CANARY:
            release.rollback(record, now_ns=now, reason=gate["reason"])
            self.playground.set_percent(0)
            self._save(record)
            return {"event": "rolled_back", "reason": gate["reason"]}
        if gate["verdict"] == "hold" and record["state"] == release.STATE_CANARY:
            release.hold(record, now_ns=now, reason=gate["reason"])
            self._save(record)
            return {"event": "held", "reason": gate["reason"]}
        if record["state"] == release.STATE_CANARY:
            due = release.step_status(record, now)["due"]
            if due and gate["verdict"] == "continue":
                release.advance(record, now_ns=now, verdict="continue")
                self.playground.set_percent(record["percent"])
                self._save(record)
                return {"event": "advanced", "percent": record["percent"]}
        return None

    # ------------------------------------------------------------------ flags
    def set_flag(self, name, enabled=None, rollout=None, release_id=None, now=None):
        now = self.clock() if now is None else now
        record = self._require(release_id)
        release.set_flag(record, name, enabled=enabled, rollout=rollout, now_ns=now)
        self._save(record)
        return record

    # ------------------------------------------------------------------ view
    def view(self, now=None):
        now = self.clock() if now is None else now
        record = self._load()
        endpoints = {"staging": f"http://127.0.0.1:{self.playground.staging_port}/",
                     "production": f"http://127.0.0.1:{self.playground.port}/"}
        if record is None:
            return {"release": None, "samples": canary.summarise([]), "traffic": self.playground.stats(),
                    "endpoints": endpoints, "plan_label": "25% / 6 h, 50% / 12 h, 100%"}
        gate = self.gate(record)
        return {
            "release": release.status(record, now_ns=now, gate=gate),
            "samples": canary.summarise(self._samples(record["release_id"])),
            "traffic": self.playground.stats(),
            "endpoints": endpoints,
            "plan_label": "25% / 6 h, 50% / 12 h, 100%",
        }
