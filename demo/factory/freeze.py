"""Frozen dispatch identity.

A build is bound to its manifest, spec, base, write scopes and configured bounds
before any worker runs. Missing or invalid bounds hold the build rather than letting
the builder invent them. The frozen record is the only thing later gates and the
publisher may trust.
"""
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path


class FreezeError(ValueError):
    """A build that cannot be frozen (missing spec or bound)."""


@dataclass
class FrozenBuild:
    build_id: str
    feature_id: str
    manifest_digest: str
    spec_digest: str
    base_sha: str
    write_scopes: list
    tier: int
    parallel: bool
    dependencies: list
    profile: str
    mode: str
    deadline_ns: int
    step_cap: int
    context_limit: int
    cost_reservation_usd: str
    acceptance_digest: str = ''
    contract_digest: str = ''
    dependency_changes: dict = None

    def digest(self):
        record=asdict(self)
        if self.dependency_changes is None:
            record.pop('dependency_changes')  # Preserve existing frozen receipt identities.
        return hashlib.sha256(
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


def _require(value, label):
    if value is None or (isinstance(value, (int, float)) and value <= 0):
        raise FreezeError(f"missing_bound:{label}")
    return value


def spec_digest(spec_dir, feature, spec_path=None):
    path = Path(spec_path) if spec_path is not None else Path(spec_dir) / feature["file"]
    if not path.is_file():
        raise FreezeError(f"missing_spec:{feature['id']}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_build(build, catalog, spec_dir, base_sha, config, write_scopes=None, spec_path=None,
                 acceptance_path=None):
    """Freeze a store build dict into a FrozenBuild, validating every required bound.

    A pinned target may supply the adapted brief and its own literal scopes; the
    catalog stays the canonical plan and is never mutated in place.
    """
    feature_id = build["feature_id"]
    feature = catalog.by_id[feature_id]
    config = config or {}
    scopes=list(write_scopes if write_scopes is not None else feature['write_paths'])
    dependencies=config.get('dependency_changes')
    if dependencies is not None:
        allowed={'demo/forum-app/build.gradle','demo/forum-web/package.json','demo/forum-web/package-lock.json'}
        if (not isinstance(dependencies,dict) or not 1<=len(dependencies)<=len(allowed)
                or any(path not in allowed or not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest)
                       for path,digest in dependencies.items())):
            raise FreezeError('invalid_dependency_policy')
        if any(not any(path==scope or (scope.endswith('/') and path.startswith(scope)) for scope in scopes)
               for path in dependencies):
            raise FreezeError('dependency_policy_out_of_scope')
        dependencies=dict(sorted(dependencies.items()))
    frozen = FrozenBuild(
        build_id=build["build_id"],
        feature_id=feature_id,
        manifest_digest=catalog.digest,
        spec_digest=spec_digest(spec_dir, feature, spec_path),
        base_sha=_require(base_sha, "base_sha"),
        write_scopes=scopes,
        tier=_require(feature.get("tier"), "tier"),
        parallel=bool(feature.get("parallel")),
        dependencies=list(feature.get("depends_on", [])),
        profile=str(config.get("profile", "fake")),
        mode=str(config.get("mode", "fake")),
        deadline_ns=int(_require(config.get("deadline_ns"), "deadline_ns")),
        step_cap=int(_require(config.get("step_cap"), "step_cap")),
        context_limit=int(_require(config.get("context_limit"), "context_limit")),
        cost_reservation_usd=str(_require(config.get("cost_reservation_usd"), "cost_reservation_usd")),
        acceptance_digest=(hashlib.sha256(Path(acceptance_path).read_bytes()).hexdigest()
                           if acceptance_path is not None else ''),
        contract_digest=build.get('contract_digest', ''),
        dependency_changes=dependencies,
    )
    return frozen
