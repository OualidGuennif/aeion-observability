"""Bounded cleanup: old terminal workspaces and the branches of failed builds whose PR was closed.

Spec: knowledge/components/factory-flue.md
"""
import json
from pathlib import Path
import re
import shutil
import time

from .store import CANCELLED, FAILED, TERMINAL

RETENTION_DAYS = 7
DAY_NS = 86400 * 10**9
BUILD_ID = re.compile('[0-9a-f]{32}')


class Retention:
    """Runs at controller start and then at most once a day; every error leaves data in place."""

    def __init__(self, store, work_root, prune_branch=None, days=RETENTION_DAYS, clock=time.time_ns):
        self.store, self.work_root = store, Path(work_root)
        self.prune_branch, self.days, self.clock = prune_branch, days, clock
        self.last_run_ns = None

    def tick(self):
        now = self.clock()
        if self.last_run_ns is not None and now - self.last_run_ns < DAY_NS:
            return None
        self.last_run_ns = now
        return self.run(now)

    def _needed(self, rows):
        """Workspaces a queued or running continuation still reads its candidate from."""
        needed = set()
        for row in rows:
            if row['status'] in TERMINAL:
                continue
            link = self.store.correction_of(row['build_id'])
            if link:
                needed.add(link['previous_build_id'])
        return needed

    def run(self, now=None):
        now = self.clock() if now is None else now
        cutoff = now - self.days * DAY_NS
        rows = self.store.board()
        by_id = {row['build_id']: row for row in rows}
        needed = self._needed(rows)
        removed, branches = [], []
        if self.work_root.is_dir():
            for path in sorted(self.work_root.iterdir()):
                row = by_id.get(path.name)
                # Only a known build's own folder, never a link, an unknown name or a live build.
                if (not BUILD_ID.fullmatch(path.name) or path.is_symlink() or not path.is_dir()
                        or row is None or row['status'] not in TERMINAL or row['updated_ns'] > cutoff
                        or path.name in needed):
                    continue
                try:
                    shutil.rmtree(path)
                    removed.append(path.name)
                except OSError:
                    continue
        if self.prune_branch is not None:
            for row in rows:
                if row['status'] not in (FAILED, CANCELLED) or not row.get('attempt_id'):
                    continue
                key = 'branch_pruned:' + row['attempt_id']
                if self.store.meta_get(key) or not _published(row):
                    continue
                try:
                    result = self.prune_branch(row['attempt_id'])
                except Exception:  # noqa: BLE001 - cleanup never breaks the build loop
                    continue
                if isinstance(result, dict) and result.get('status') in ('deleted', 'absent'):
                    self.store.meta_set(key, result['status'])
                    branches.append(row['attempt_id'])
        return {'workspaces_removed': removed, 'branches_pruned': branches}


def _published(row):
    """Only a build whose receipt names a pull request ever pushed a branch."""
    try:
        receipt = json.loads(row['receipt']) if row.get('receipt') else {}
    except ValueError:
        return False
    publisher = receipt.get('publisher') if isinstance(receipt, dict) else None
    return isinstance(publisher, dict) and isinstance(publisher.get('pr'), dict)

