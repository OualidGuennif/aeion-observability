"""Pinned atomic GitHub publication and exact-head protected merging.

Spec: knowledge/components/factory-flue.md

The isolated publisher creates a single tree/commit on a deterministic feature branch.
The isolated release role checks the actual protection, CI issuer/head and main ancestry.
An uncertain write is reconciled by reads; no direct or force update of main exists here.
"""
import hashlib
import json
import os
import re
import ssl
import urllib.error
import urllib.request
from urllib.parse import quote

from .review import content_digest

API = 'https://api.github.com'
MAX_FILE_BYTES = 512 * 1024
MAX_TOTAL_BYTES = 1024 * 1024
PRODUCT_ROOTS = ('demo/forum-app/', 'demo/forum-web/', 'demo/forum-docs/')
PRODUCT_DOCUMENTS = ('knowledge/components/agora-product.md', 'knowledge/components/factory-architecture.md')
SHA = re.compile(r'[a-f0-9]{40}')


class GitHubError(ValueError):
    """A fixed operational refusal, with no credential or remote response content."""


def tls_context():
    """Verify GitHub with certifi, or with the system CA bundle when certifi is absent.

    Verification stays on. A missing bundle still uses the default context, which fails closed.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError):
        pass
    for candidate in ('/etc/ssl/cert.pem', '/private/etc/ssl/cert.pem'):
        if os.path.isfile(candidate):
            return ssl.create_default_context(cafile=candidate)
    return ssl.create_default_context()


def branch_name(attempt_id):
    if not isinstance(attempt_id, str) or not re.fullmatch('[a-f0-9]{32}', attempt_id):
        raise GitHubError('invalid_attempt_id')
    return 'aeion/build-' + attempt_id[:24]


def _urllib_transport(method, url, payload, headers, timeout=20):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *_args, **_kwargs): return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=tls_context()))
    request = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                                     method=method, headers=headers)
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        data = response.read(4194305)
        if len(data) > 4194304:
            raise GitHubError('forge_response_too_large')
        try:
            return response.code, json.loads(data) if data else {}
        except (UnicodeError, ValueError):
            raise GitHubError('forge_response_invalid') from None


def _sha(value):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise GitHubError('invalid_commit_identity')
    return value


def _blob(text):
    raw = text.encode('utf-8')
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


class GitHubForge:
    def __init__(self, repo, token=None, transport=None, base_branch='main', dry_run=True,
                 allow_merge=False, before_write=None):
        if not isinstance(repo, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
            raise GitHubError('invalid_repository')
        if base_branch not in {'main', 'develop'}:
            raise GitHubError('invalid_base_branch')
        self.repo, self.base_branch = repo, base_branch
        self.token = token if token is not None else os.environ.get('GH_API_KEY')
        self.transport = transport or _urllib_transport
        self.dry_run, self.allow_merge = bool(dry_run), bool(allow_merge)
        self.calls = []
        self.before_write = before_write

    def _request(self, method, path, payload=None):
        if not self.token:
            raise GitHubError('publisher_unconfigured')
        if not path.startswith('/repos/' + self.repo + '/'):
            raise GitHubError('forbidden_forge_endpoint')
        if method != 'GET' and self.before_write is not None and not self.before_write():
            raise GitHubError('publication_revoked')
        url = API + path
        self.calls.append((method, url))
        return self.transport(method, url, payload, {
            'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'aeion-factory'})

    def _ref(self, branch):
        return '/repos/' + self.repo + '/git/ref/heads/' + quote(branch, safe='/')

    def base_sha(self):
        status, data = self._request('GET', self._ref(self.base_branch))
        if status != 200:
            raise GitHubError('base_unreadable:' + str(status))
        return _sha((data.get('object') or {}).get('sha'))

    def _commit(self, sha):
        status, data = self._request('GET', f'/repos/{self.repo}/git/commits/{_sha(sha)}')
        if status != 200:
            raise GitHubError('commit_unreadable:' + str(status))
        return data

    def _files(self, request):
        files = request.get('files')
        if not isinstance(files, dict) or not files or len(files) > 100:
            raise GitHubError('publisher_no_content')
        total = 0
        for path, text in files.items():
            if (not isinstance(path, str) or not (path.startswith(PRODUCT_ROOTS) or path in PRODUCT_DOCUMENTS)
                    or not re.fullmatch(r'[A-Za-z0-9_./-]+', path)
                    or any(not p or p.startswith('.') for p in path.split('/'))
                    or not isinstance(text, str) or '\0' in text):
                raise GitHubError('forbidden_product_content')
            size = len(text.encode('utf-8')); total += size
            if size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                raise GitHubError('publisher_content_too_large')
        if request.get('artifact_digest') != content_digest(files):
            raise GitHubError('artifact_digest_mismatch')
        return files

    def _matches_commit(self, head, base, files):
        commit = self._commit(head)
        if [p.get('sha') for p in commit.get('parents', [])] != [base]:
            return False
        status, diff = self._request('GET', f'/repos/{self.repo}/compare/{base}...{head}')
        changed = diff.get('files', []) if isinstance(diff, dict) else []
        if (status != 200 or len(changed) != len(files)
                or {p.get('filename') for p in changed} != set(files)
                or any(p.get('status') not in {'added', 'modified'}
                       or p.get('sha') != _blob(files[p['filename']]) for p in changed)):
            return False
        tree = _sha((commit.get('tree') or {}).get('sha'))
        status, listing = self._request('GET', f'/repos/{self.repo}/git/trees/{tree}?recursive=1')
        if status != 200 or listing.get('truncated') is not False:
            return False
        entries = {p.get('path'): p for p in listing.get('tree', [])}
        return all(entries.get(path, {}).get('mode') == '100644'
                   and entries[path].get('type') == 'blob'
                   and entries[path].get('sha') == _blob(text) for path, text in files.items())

    def find_pull_request(self, branch):
        query = quote(self.repo.split('/')[0] + ':' + branch, safe=':/')
        status, found = self._request('GET', f'/repos/{self.repo}/pulls?state=all&head={query}&per_page=100')
        if status != 200 or not isinstance(found, list) or len(found) > 1:
            raise GitHubError('pr_probe_failed:' + str(status))
        return found[0] if found else None

    def open_pull_request(self, branch, title, body):
        existing = self.find_pull_request(branch)
        if existing:
            return existing
        status, data = self._request('POST', f'/repos/{self.repo}/pulls',
            {'title': title, 'head': branch, 'base': self.base_branch, 'body': body})
        if status not in {200, 201}:
            existing = self.find_pull_request(branch)
            if existing:
                return existing
            raise GitHubError('pr_open_failed:' + str(status))
        return data

    def _pr_result(self, pr, head=None, base=None):
        number = pr.get('number')
        if type(number) is not int or number < 1:
            raise GitHubError('invalid_pr_identity')
        return {'simulated': False, 'dry_run': False, 'pr_number': number,
                'html_url': f'https://github.com/{self.repo}/pull/{number}',
                'head_sha': head or (pr.get('head') or {}).get('sha'),
                'base_sha': base or (pr.get('base') or {}).get('sha'),
                'merged': bool(pr.get('merged') or pr.get('merged_at')),
                'merge_sha': pr.get('merge_commit_sha')}

    def publish(self, request):
        if request.get('merge'):
            raise GitHubError('merge_requires_release_role')
        files = self._files(request)
        base, branch = _sha(request.get('base')), branch_name(request.get('attempt_id'))
        if self.dry_run:
            return {'status': 'dry_run', 'pr': {'simulated': False, 'dry_run': True, 'merged': False,
                                                'pr_number': None, 'branch': branch}}
        status, existing = self._request('GET', self._ref(branch))
        if status == 200:
            head = _sha((existing.get('object') or {}).get('sha'))
            if not self._matches_commit(head, base, files):
                raise GitHubError('branch_content_mismatch')
        elif status == 404:
            if self.base_sha() != base:
                raise GitHubError('stale_base')
            base_tree = _sha((self._commit(base).get('tree') or {}).get('sha'))
            status, tree = self._request('POST', f'/repos/{self.repo}/git/trees', {
                'base_tree': base_tree, 'tree': [{'path': p, 'mode': '100644', 'type': 'blob', 'content': t}
                                                for p, t in sorted(files.items())]})
            if status != 201:
                raise GitHubError('tree_create_failed:' + str(status))
            tree_sha = _sha(tree.get('sha'))
            status, commit = self._request('POST', f'/repos/{self.repo}/git/commits', {
                'message': (f"Feature {request.get('feature_id')} / {request['attempt_id']}\n\n"
                            f"Artifact: {request['artifact_digest']}\n\n"
                            "Docs-Checked: knowledge/components/factory-architecture.md -- automated factory build\n"),
                'tree': tree_sha, 'parents': [base]})
            if status != 201:
                raise GitHubError('commit_create_failed:' + str(status))
            head = _sha(commit.get('sha'))
            status, _ = self._request('POST', f'/repos/{self.repo}/git/refs',
                                      {'ref': 'refs/heads/' + branch, 'sha': head})
            if status not in {200, 201}:
                # A competing create or unknown response may have succeeded; read, never overwrite.
                status, ref = self._request('GET', self._ref(branch))
                observed = (ref.get('object') or {}).get('sha')
                if status != 200 or not self._matches_commit(observed, base, files):
                    raise GitHubError('branch_reconciliation_required')
                head = observed
        else:
            raise GitHubError('branch_probe_failed:' + str(status))
        if not self._matches_commit(head, base, files):
            raise GitHubError('branch_content_mismatch')
        pr = self.open_pull_request(branch, str(request.get('title') or 'Factory feature')[:200],
            'Protected factory checks and two independent reviews bind this exact artifact.\n\n'
            + 'Artifact: `' + request['artifact_digest'] + '`\nBase: `' + base + '`')
        return {'status': 'published', 'pr': {**self._pr_result(pr, head, base), 'branch': branch}}

    def protection(self):
        status, data = self._request('GET', f'/repos/{self.repo}/branches/{self.base_branch}/protection')
        if status != 200:
            return {'status': 'held', 'reason': 'protection_unreadable', 'http_status': status}
        checks = data.get('required_status_checks') or {}
        required = checks.get('checks') or [{'context': name, 'app_id': 15368} for name in checks.get('contexts', [])]
        if (checks.get('strict') is not True or not required
                or (data.get('enforce_admins') or {}).get('enabled') is not True
                or (data.get('allow_force_pushes') or {}).get('enabled') is not False
                or (data.get('allow_deletions') or {}).get('enabled') is not False
                or any(not isinstance(c.get('context'), str) or not c['context']
                       or c.get('app_id') not in {None, 15368} for c in required)):
            return {'status': 'held', 'reason': 'protection_unqualified'}
        return {'status': 'qualified', 'checks': sorted({c['context'] for c in required})}

    def _ci(self, head, required):
        status, body = self._request('GET', f'/repos/{self.repo}/commits/{head}/check-runs?per_page=100&filter=latest')
        if status != 200 or type(body.get('total_count')) is not int or body['total_count'] > 100:
            return {'status': 'held', 'reason': 'ci_unreadable'}
        valid = {c['name']: c for c in body.get('check_runs', []) if c.get('head_sha') == head
                 and (c.get('app') or {}).get('id') == 15368}
        if any(name not in valid or valid[name].get('status') != 'completed' for name in required):
            return {'status': 'pending', 'reason': 'ci_pending'}
        failed = self._failed_checks(required, valid)
        if failed:
            # Names and conclusions only. Check logs and annotations can carry source or secrets.
            return {'status': 'held', 'reason': 'ci_failed', 'failed_checks': failed}
        return {'status': 'passed', 'checks': required}

    @staticmethod
    def _failed_checks(required, valid):
        conclusions = {'failure', 'cancelled', 'timed_out', 'action_required', 'skipped',
                       'neutral', 'stale', 'startup_failure'}
        # A comma is a normal character in a GitHub check name. A newline is not.
        name_ok = re.compile(r'[A-Za-z0-9_ .,/:+-]{1,80}')
        failed = []
        for name in required:
            conclusion = valid[name].get('conclusion')
            if conclusion == 'success':
                continue
            failed.append({'name': name if isinstance(name, str) and name_ok.fullmatch(name) else 'check',
                           'conclusion': conclusion if conclusion in conclusions else 'failed'})
            if len(failed) == 8:
                break
        return failed

    def read_failed_checks(self, head):
        """Failed required checks for one commit, or None when the read is not definite.

        Names and conclusions only. The caller keeps the stored names when this returns None.
        """
        try:
            head = _sha(head)
            protection = self.protection()
            if protection.get('status') != 'qualified':
                return None
            ci = self._ci(head, protection['checks'])
        except (GitHubError, OSError, TimeoutError):
            return None
        if ci.get('status') == 'held' and ci.get('reason') == 'ci_failed' and ci.get('failed_checks'):
            return ci['failed_checks']
        return None

    def _confirmed_merge(self, pr):
        merge_sha = _sha(pr.get('merge_commit_sha'))
        main = self.base_sha()
        if main != merge_sha:
            status, compare = self._request('GET', f'/repos/{self.repo}/compare/{merge_sha}...{main}')
            if status != 200 or compare.get('status') not in {'ahead', 'identical'}:
                return {'status': 'held', 'reason': 'merge_not_confirmed', 'merge_sha': merge_sha}
        return {'status': 'merged', 'merge_sha': merge_sha, 'main_sha': main, 'confirmed_main': True,
                'pr': self._pr_result(pr)}

    def prune_branch(self, attempt_id):
        """Delete one factory branch, only when its pull request was closed without a merge."""
        if not isinstance(attempt_id, str) or not re.fullmatch('[0-9a-f]{24,64}', attempt_id):
            raise GitHubError('invalid_attempt')
        if self.dry_run:
            return {'status': 'held', 'reason': 'dry_run'}
        branch = branch_name(attempt_id)
        pr = self.find_pull_request(branch)
        if not isinstance(pr, dict) or pr.get('state') != 'closed' or pr.get('merged_at'):
            return {'status': 'held', 'reason': 'pull_request_not_closed_unmerged'}
        status, _ = self._request('DELETE', f'/repos/{self.repo}/git/refs/heads/' + quote(branch, safe='/'))
        if status == 204:
            return {'status': 'deleted'}
        if status in (404, 422):
            return {'status': 'absent'}
        return {'status': 'held', 'reason': 'branch_delete_failed:' + str(status)}

    def merge(self, number, *, expected_head, expected_base):
        head, base = _sha(expected_head), _sha(expected_base)
        if type(number) is not int or number < 1 or not self.allow_merge:
            raise GitHubError('merge_requires_release_role')
        if self.dry_run:
            return {'status': 'dry_run'}
        path = f'/repos/{self.repo}/pulls/{number}'
        status, pr = self._request('GET', path)
        if status != 200:
            return {'status': 'held', 'reason': 'pr_unreadable'}
        if ((pr.get('head') or {}).get('sha') != head
                or ((pr.get('head') or {}).get('repo') or {}).get('full_name') != self.repo
                or ((pr.get('base') or {}).get('repo') or {}).get('full_name') != self.repo
                or (pr.get('base') or {}).get('ref') != self.base_branch):
            return {'status': 'held', 'reason': 'stale_head'}
        if pr.get('merged') is True:
            return self._confirmed_merge(pr)
        if (pr.get('base') or {}).get('sha') != base or self.base_sha() != base:
            return {'status': 'held', 'reason': 'stale_base'}
        protection = self.protection()
        if protection['status'] != 'qualified':
            return protection
        ci = self._ci(head, protection['checks'])
        if ci['status'] != 'passed':
            return ci
        if pr.get('state') != 'open' or pr.get('mergeable') is not True or pr.get('mergeable_state') != 'clean':
            return {'status': 'pending', 'reason': 'mergeability_pending'}
        # Re-read immediately before the effect. Strict protected checks also enforce base freshness.
        status, current = self._request('GET', path)
        if status != 200 or (current.get('head') or {}).get('sha') != head or self.base_sha() != base:
            return {'status': 'held', 'reason': 'stale_head_or_base'}
        status, result = self._request('PUT', path + '/merge', {'merge_method': 'squash', 'sha': head})
        if status != 200 or result.get('merged') is not True:
            # Do not repeat a potentially accepted merge; the next call only reads until reconciled.
            return {'status': 'pending', 'reason': 'merge_reconciliation_required'}
        status, final = self._request('GET', path)
        if status != 200 or final.get('merged') is not True:
            return {'status': 'pending', 'reason': 'merge_reconciliation_required'}
        return self._confirmed_merge(final)

    def reconcile(self, attempt_id):
        try:
            pr = self.find_pull_request(branch_name(attempt_id))
            return {'status': 'published', 'pr': self._pr_result(pr)} if pr else {'status': 'absent'}
        except (GitHubError, OSError, TimeoutError):
            return {'status': 'unknown', 'reason': 'forge_reconciliation_unavailable'}
