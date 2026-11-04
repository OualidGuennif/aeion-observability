"""A live factory must qualify its actual Flue/OpenShell path, never a direct-call fallback."""
import hashlib
import json
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_FILES = (
    'demo/factory/flue_qualification.py', 'demo/factory/flue_builder.py',
    'demo/factory/agent_files.py', 'demo/factory/flue_session.py', 'demo/factory/flue_review.py',
    'demo/factory/preparation.py', 'demo/factory/source.py',
    'demo/factory/routing.py', 'demo/factory/models.py', 'demo/factory/store.py', 'demo/factory/manifest.py',
    'demo/factory/review.py', 'demo/factory/review_circuit.py', 'demo/factory/checks.py',
    'demo/factory/artifact.py', 'demo/factory/freeze.py', 'demo/factory/isolation.py', 'demo/factory/postgres.py',
    'demo/factory/publication.py', 'demo/factory/publication_role.py', 'demo/factory/github.py',
    'demo/factory/publish.py', 'demo/factory/publisher.py', 'demo/factory/execution.py',
    'demo/factory/keys.py', 'demo/factory/budget.py', 'demo/app/provider_usage.py',
    'demo/app/token_budget.py', 'demo/app/profiles.py',
    'demo/app/memory.py', 'demo/app/telemetry.py', 'demo/factory/telemetry.py', 'demo/compose.yaml',
    'demo/factory/dispatch.py', 'demo/factory/api.py', 'demo/factory/target.py', 'demo/app/sandbox.py',
    'demo/app/bridge.py', 'demo/app/relay.py', 'demo/app/runner.py',
    'demo/flue/package-lock.json', 'demo/flue/src/agents/coder.ts',
    'demo/flue/src/provider.ts', 'demo/flue/src/observe.ts',
    'demo/flue/src/agents/reviewer.ts', 'demo/flue/src/tools/submit-review.ts',
    'demo/flue/src/agents/preparer.ts', 'demo/flue/src/tools/submit-preparation.ts',
    'demo/flue/src/tools/factory-checks.ts',
    'demo/flue/src/sandboxes/openshell.ts', 'demo/flue/src/db.ts',
    'demo/forum/ARCHITECTURE.md',
)


def protocol_hash(root=ROOT):
    digest = hashlib.sha256()
    for name in PROTOCOL_FILES:
        digest.update(name.encode() + b'\0' + (Path(root) / name).read_bytes() + b'\0')
    return digest.hexdigest()


def ready(root=ROOT, now_ns=None):
    """An exact protocol match and fresh real-path evidence are required before admission."""
    try:
        proof = json.loads((Path(root) / 'demo/.local/data/factory-flue-qualification.json').read_text())
        if not isinstance(proof, dict) or type(proof.get('expires_ns')) is not int:
            return False
        publication = proof.get('protected_main')
        if not isinstance(publication, dict):
            return False
        return (proof.get('protocol_sha256') == protocol_hash(root)
                and proof.get('runtime') == 'flue-openshell'
                and proof.get('sandbox') == 'openshell'
                and proof.get('protected_check') == 'passed'
                and proof.get('teardown_confirmed') is True
                and proof.get('automatic_preparation') == 'qualified'
                and proof.get('publication_state_machine') == 'qualified'
                and proof.get('routing_persistence') == 'qualified'
                and proof.get('postgres_migration_restore') == 'qualified'
                and proof.get('postgres_least_privilege') == 'qualified'
                and proof.get('react_browser_api') == 'qualified'
                and publication.get('confirmed_main') is True
                and publication.get('synthetic') is False
                and isinstance(publication.get('merge_sha'), str)
                and re.fullmatch('[a-f0-9]{40}', publication['merge_sha']) is not None
                and isinstance(publication.get('main_sha'), str)
                and re.fullmatch('[a-f0-9]{40}', publication['main_sha']) is not None
                and proof.get('expires_ns', 0) > (time.time_ns() if now_ns is None else now_ns))
    except (OSError, ValueError, TypeError):
        return False
