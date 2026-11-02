"""Daily USD budget ledger for the two repositories that may spend.

The demo has two independent purses, each capped at $15.00 per local day:
``aeion-observability`` for the cockpit's own runs and ``aeion-autonomous-forum`` for the
factory workers that build the product. A reservation is journaled before a paid action and
settled with the actual cost after it; an open reservation counts against the day so two
workers cannot both spend the last dollar. A missing or unreadable ledger fails closed.

Only amounts, dates, scopes and opaque reservation ids are stored: no prompt, source,
credential or provider response.
"""
import argparse
import fcntl
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from pathlib import Path

DEFAULT_LIMIT_USD = Decimal("15.00")
SCOPES = ("aeion-observability", "aeion-autonomous-forum")
_LEDGER_VERSION = 1


class BudgetError(ValueError):
    """A budget decision that cannot be trusted."""


@dataclass(frozen=True)
class Reservation:
    id: str
    scope: str
    day: str
    estimate_usd: Decimal


def _fmt(amount):
    """Two decimals everywhere: a ledger line and its summary must read the same."""
    return format(amount, ".2f")


def _money(value, label="amount"):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise BudgetError(f"invalid_{label}") from None
    if not amount.is_finite() or amount < 0:
        raise BudgetError(f"invalid_{label}")
    return amount


def _cents_up(value, label="amount"):
    """A positive amount never becomes free when the journal records cents."""
    return _money(value, label).quantize(Decimal("0.01"), rounding=ROUND_CEILING)


class DailyBudget:
    def __init__(self, path, limits=None, today=None):
        self.path = Path(path)
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        configured = limits or {scope: DEFAULT_LIMIT_USD for scope in SCOPES}
        self.limits = {str(scope): _money(limit, "limit") for scope, limit in configured.items()}
        if not self.limits or any(not scope or "/" in scope for scope in self.limits):
            raise BudgetError("invalid_budget_scopes")
        self._today = today or (lambda: date.today().isoformat())

    # ---------------------------------------------------------------- journal
    def _read(self):
        if not self.path.exists():
            return []
        entries = []
        try:
            with self.path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    if (not isinstance(entry, dict)
                            or entry.get("version") != _LEDGER_VERSION
                            or entry.get("kind") not in {"reserve", "settle"}
                            or entry.get("scope") not in self.limits
                            or not isinstance(entry.get("day"), str) or not entry["day"]
                            or not isinstance(entry.get("reservation"), str)
                            or not entry["reservation"]):
                        raise ValueError("shape")
                    entry["usd"] = _money(entry.get("usd"), "ledger_amount")
                    entries.append(entry)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            raise BudgetError("budget_ledger_corrupt") from None
        return entries

    def _append(self, entry):
        line = json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n"
        descriptor = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            os.write(descriptor, line.encode("utf-8"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _locked(self):
        return _FileLock(self.lock_path)

    def _spent(self, entries, scope, day):
        settled = {e["reservation"] for e in entries
                   if e["kind"] == "settle" and e["scope"] == scope and e["day"] == day}
        total = Decimal("0")
        for entry in entries:
            if entry["scope"] != scope or entry["day"] != day:
                continue
            if entry["kind"] == "settle":
                total += entry["usd"]
            elif entry["reservation"] not in settled:
                total += entry["usd"]
        return total

    # ------------------------------------------------------------------ public
    def spent(self, scope, day=None):
        self._check_scope(scope)
        day = day or self._today()
        with self._locked():
            return self._spent(self._read(), scope, day)

    def remaining(self, scope, day=None):
        self._check_scope(scope)
        day = day or self._today()
        with self._locked():
            return self.limits[scope] - self._spent(self._read(), scope, day)

    def admit(self, scope, estimate_usd, note=""):
        """Journal a reservation before a paid action; refuse past the daily limit."""
        self._check_scope(scope)
        estimate = _cents_up(estimate_usd, "estimate")
        day = self._today()
        with self._locked():
            entries = self._read()
            spent = self._spent(entries, scope, day)
            if spent + estimate > self.limits[scope]:
                raise BudgetError("budget_unavailable")
            reservation = Reservation(uuid.uuid4().hex, scope, day, estimate)
            self._append({
                "version": _LEDGER_VERSION, "kind": "reserve", "scope": scope, "day": day,
                "reservation": reservation.id, "usd": _fmt(estimate),
                "note": str(note)[:80], "ts_ns": time.time_ns(),
            })
            return reservation

    def settle(self, reservation, actual_usd):
        """Close a reservation with the actual (or conservatively estimated) cost."""
        actual = _cents_up(actual_usd, "actual")
        with self._locked():
            entries = self._read()
            if any(e["kind"] == "settle" and e["reservation"] == reservation.id for e in entries):
                return self._spent(entries, reservation.scope, reservation.day)
            if not any(e["kind"] == "reserve" and e["reservation"] == reservation.id
                       and e["scope"] == reservation.scope for e in entries):
                raise BudgetError("unknown_reservation")
            # A free reservation cannot be turned into a paid one after the fact.
            if actual > 0 and reservation.estimate_usd == 0:
                raise BudgetError("settlement_exceeds_reservation")
            self._append({
                "version": _LEDGER_VERSION, "kind": "settle", "scope": reservation.scope,
                "day": reservation.day, "reservation": reservation.id,
                "usd": _fmt(actual), "ts_ns": time.time_ns(),
            })
            return self._spent(entries + [{"kind": "settle", "scope": reservation.scope,
                                            "day": reservation.day, "usd": actual,
                                            "reservation": reservation.id}],
                               reservation.scope, reservation.day)

    def summary(self, day=None):
        day = day or self._today()
        with self._locked():
            entries = self._read()
            return {
                scope: {
                    "day": day,
                    "limit_usd": _fmt(limit),
                    "spent_usd": _fmt(self._spent(entries, scope, day)),
                    "remaining_usd": _fmt(limit - self._spent(entries, scope, day)),
                }
                for scope, limit in self.limits.items()
            }

    def _check_scope(self, scope):
        if scope not in self.limits:
            raise BudgetError("budget_unknown_scope")


class _FileLock:
    def __init__(self, path):
        self.path = Path(path)
        self.handle = None

    def __enter__(self):
        self.handle = self.path.open("a+", encoding="utf-8")
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *_):
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default="demo/.local/budget/ledger.jsonl")
    parser.add_argument("--day")
    args = parser.parse_args(argv)
    budget = DailyBudget(args.ledger)
    print(json.dumps(budget.summary(args.day), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
