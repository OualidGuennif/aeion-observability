"""Load and validate the schema-v2 feature manifest (the factory catalog).

This validates catalog structure and the dependency graph. It is not the runtime
permission enforcer: build/queue code independently re-validates ids, phases and
write scopes before any effect.
"""
import hashlib
import json
from pathlib import Path

SUPPORTED_SCHEMA = 2
PHASES = ("P0", "P1", "P2", "P3", "P4", "P5")
_REQUIRED = ("id", "title", "area", "size", "parallel", "phase", "tier", "write_paths", "depends_on", "file")


class ManifestError(ValueError):
    """A catalog that cannot be safely loaded or trusted."""


class Catalog:
    """Validated feature catalog with a stable digest and dependency helpers."""

    def __init__(self, raw, source=None):
        if not isinstance(raw, dict):
            raise ManifestError("manifest_not_object")
        self.source = str(source) if source is not None else None
        self.raw = raw
        self.schema_version = raw.get("schema_version")
        self.features = raw.get("features")
        self.by_id = {}
        self._validate()
        self.digest = self._digest()

    def _digest(self):
        # Stable over the semantic feature list: ids are the canonical order, so a
        # reordered or differently-indented manifest hashes to the same catalog digest.
        ordered = sorted(self.features, key=lambda f: f.get("id", ""))
        return hashlib.sha256(
            json.dumps(ordered, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _validate(self):
        if self.schema_version != SUPPORTED_SCHEMA:
            raise ManifestError(f"unsupported_schema_version:{self.schema_version!r}")
        if not isinstance(self.features, list) or len(self.features) != int(self.raw.get("count", -1)):
            raise ManifestError("feature_count_mismatch")
        for feature in self.features:
            if not isinstance(feature, dict) or set(_REQUIRED) - set(feature):
                raise ManifestError(f"feature_missing_fields:{feature.get('id', '?')}")
            fid = feature["id"]
            if not isinstance(fid, str) or not fid or fid in self.by_id:
                raise ManifestError(f"duplicate_or_invalid_id:{fid!r}")
            if feature.get("tier") != 3:
                raise ManifestError(f"invalid_tier:{fid}")
            if feature.get("phase") not in PHASES:
                raise ManifestError(f"invalid_phase:{fid}")
            if not isinstance(feature.get("parallel"), bool):
                raise ManifestError(f"invalid_parallel:{fid}")
            if not isinstance(feature.get("depends_on"), list):
                raise ManifestError(f"invalid_depends_on:{fid}")
            write_paths = feature.get("write_paths")
            if not isinstance(write_paths, list) or not write_paths or not all(_valid_scope(p) for p in write_paths):
                raise ManifestError(f"invalid_write_paths:{fid}")
            self.by_id[fid] = feature
        for feature in self.features:
            for dep in feature["depends_on"]:
                if dep not in self.by_id:
                    raise ManifestError(f"unknown_dependency:{feature['id']}->{dep}")
                if PHASES.index(self.by_id[dep]["phase"]) > PHASES.index(feature["phase"]):
                    raise ManifestError(f"later_phase_dependency:{feature['id']}->{dep}")
        self._check_acyclic()

    def _check_acyclic(self):
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {fid: WHITE for fid in self.by_id}
        stack = []

        def visit(fid):
            color[fid] = GRAY
            stack.append(fid)
            for dep in self.by_id[fid]["depends_on"]:
                if color[dep] == GRAY:
                    cycle = stack[stack.index(dep):] + [dep]
                    raise ManifestError("cycle:" + "->".join(cycle))
                if color[dep] == WHITE:
                    visit(dep)
            stack.pop()
            color[fid] = BLACK

        for fid in self.by_id:
            if color[fid] == WHITE:
                visit(fid)

    def missing_dependencies(self, feature_id, merged):
        """Dependency ids of a feature that are not in the merged set."""
        if feature_id not in self.by_id:
            raise ManifestError(f"unknown_feature:{feature_id}")
        return [d for d in self.by_id[feature_id]["depends_on"] if d not in merged]

    def phase_index(self, feature_id):
        return PHASES.index(self.by_id[feature_id]["phase"])


def _valid_scope(path):
    if not isinstance(path, str) or not path:
        return False
    if path.startswith("/") or "\\" in path or path.startswith("..") or "/../" in path:
        return False
    return True


def load_manifest(path):
    """Load a manifest file from disk and validate it."""
    data = json.loads(Path(path).read_text())
    return Catalog(data, source=path)
