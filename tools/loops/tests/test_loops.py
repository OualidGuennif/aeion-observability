#!/usr/bin/env python3
"""Exercise disabled/dry runs, native arguments, severity routing and real timeout behavior."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import time

ROOT=Path(__file__).resolve().parents[3]

# The read-only allowlist every non-writing job starts from, exactly as loops/orchestrator.sh spells it.
READ_ONLY=("Read,Grep,Glob,Write(.aeion/loop-bodies/**),Bash(git log -5 --oneline),"
           "Bash(git diff --stat),Bash(git diff --check),Bash(git status --short),"
           "Bash(tools/knowledge/knowledge-check),Bash(tools/knowledge/doc-links),"
           "Bash(tools/knowledge/doc-links --for *),Bash(tools/repo-health/repo-health),"
           "Bash(gh issue list *),Bash(gh issue view *),Bash(gh issue create *),Bash(gh issue comment *)")

# One golden per job: the settings --dry-run prints and the exact argv the native runner receives.
# setUp's fake gh answers severity:high, so inner's real run routes to opus/high while its dry run
# prints the label-free default; both are recorded, because both are what the script really builds.
GOLDEN={
    'inner': dict(prompt='inner.md',extra=('--issue','42'),issue=42,
                  dry=('sonnet','medium','acceptEdits'),run=('opus','high','acceptEdits'),
                  tools="Read,Grep,Glob,Edit,Write,Agent,Bash(git *),Bash(gh issue *),Bash(gh pr *),Bash(tools/*),Bash(python3 *)"),
    'middle': dict(prompt='middle.md',extra=(),dry=('sonnet','medium','dontAsk'),run=('sonnet','medium','dontAsk'),
                   tools=READ_ONLY+",Agent,Bash(gh pr list *),Bash(gh pr view *),Bash(gh pr checks *),Bash(gh pr diff *),Bash(gh pr comment *)"),
    'outer': dict(prompt='outer.md',extra=(),dry=('haiku','low','dontAsk'),run=('haiku','low','dontAsk'),
                  tools=READ_ONLY+",Bash(gh issue *),Bash(gh run list *)"),
    'docs': dict(prompt='docs.md',extra=(),dry=('haiku','low','dontAsk'),run=('haiku','low','dontAsk'),
                 tools=READ_ONLY+",Bash(gh issue *)"),
    'security': dict(prompt='security.md',extra=(),dry=('opus','high','dontAsk'),run=('opus','high','dontAsk'),
                     tools=READ_ONLY+",Agent,Skill,Bash(gh issue *)"),
    'watch': dict(prompt='watch.md',extra=(),dry=('sonnet','medium','acceptEdits'),run=('sonnet','medium','acceptEdits'),
                  tools=READ_ONLY+",WebSearch,WebFetch,Write(tech-watch/**),Edit(tech-watch/**),Bash(git *),Bash(gh pr create *)"),
    'retro': dict(prompt='retro.md',extra=(),dry=('sonnet','medium','acceptEdits'),run=('sonnet','medium','acceptEdits'),
                  tools=READ_ONLY+",Agent,Write(knowledge/**),Edit(knowledge/**),Write(.claude/**),Edit(.claude/**),Bash(git *),Bash(gh pr *),Bash(gh api *)"),
}


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        shutil.copytree(ROOT/'loops',self.root/'loops')
        shutil.copytree(ROOT/'tools/loops',self.root/'tools/loops')
        shutil.copytree(ROOT/'tools/architecture',self.root/'tools/architecture')
        (self.root/'tools/context').mkdir(parents=True)
        native=self.root/'tools/context/run'
        native.write_text('#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\nPath("invocation.json").write_text(json.dumps(sys.argv[1:]))\n')
        native.chmod(0o755)
        gh=self.root/'gh';gh.write_text('#!/bin/sh\nprintf "%s\\n" agent-ready severity:high\n');gh.chmod(0o755)
        self.env={**os.environ,'PATH':str(self.root)+os.pathsep+os.environ['PATH']}

    def call(self,*args):
        return subprocess.run(['bash',str(self.root/'loops/orchestrator.sh'),*args],cwd=self.root,
                              env=self.env,capture_output=True,text=True,timeout=10)

    def configure(self,extra=''):
        (self.root/'env.local').write_text('LOOPS_ENABLED=true\n'+extra)

    def golden(self,job):
        # The dry-run settings, then the exact native argv, in the order the script builds them.
        spec=GOLDEN[job]
        self.configure()
        dry=self.call(job,*spec['extra'],'--dry-run')
        self.assertEqual(dry.returncode,0,dry.stderr)
        model,effort,mode=spec['dry']
        self.assertEqual(dry.stderr.splitlines(),[
            f'job={job} model={model} effort={effort} mode={mode} budget=none max_turns=30 timeout=900',
            f'tools={spec["tools"]}','dry run: nothing executed'],job)
        self.assertFalse((self.root/'invocation.json').exists(),f'{job}: --dry-run launched the native runner')
        real=self.call(job,*spec['extra'])
        self.assertEqual(real.returncode,0,real.stderr)
        prompt=(ROOT/'loops/prompts'/spec['prompt']).read_text().rstrip('\n')
        if spec.get('issue'):
            prompt+=f"\n\nThe issue to fix: #{spec['issue']}."
        model,effort,mode=spec['run']
        self.assertEqual(json.loads((self.root/'invocation.json').read_text()),
                         ['-p',prompt,'--model',model,'--effort',effort,'--permission-mode',mode,
                          '--allowedTools',spec['tools'],'--output-format','text','--max-turns','30'],job)

    def test_golden_command_inner(self):self.golden('inner')

    def test_golden_command_middle(self):self.golden('middle')

    def test_golden_command_outer(self):self.golden('outer')

    def test_golden_command_docs(self):self.golden('docs')

    def test_golden_command_security(self):self.golden('security')

    def test_golden_command_watch(self):self.golden('watch')

    def test_golden_command_retro(self):self.golden('retro')

    def test_kill_switch_runs_nothing_for_every_job_and_argument(self):
        (self.root/'env.local').write_text('LOOPS_ENABLED=false\n')
        for job,extra in (('inner',('--issue','42')),('middle',()),('outer',()),('docs',()),
                          ('security',()),('watch',()),('retro',())):
            result=self.call(job,*extra)
            self.assertEqual(result.returncode,0,f'{job}: {result.stderr}')
            self.assertIn('LOOPS_ENABLED is not true',result.stderr,job)
            self.assertFalse((self.root/'invocation.json').exists(),f'{job} launched the native runner')

    def test_disabled_and_dry_runs_never_launch_agent(self):
        self.assertEqual(self.call('outer').returncode,0)
        self.configure()
        self.assertEqual(self.call('outer','--dry-run').returncode,0)
        self.assertFalse((self.root/'invocation.json').exists())

    def test_read_only_jobs_write_only_their_body_files(self):
        for job in ('outer','docs','security','middle'):
            tools=[line for line in self.call(job,'--dry-run').stderr.splitlines() if line.startswith('tools=')][0]
            writes=[tool for tool in tools[6:].split(',') if tool.startswith(('Write','Edit'))]
            self.assertEqual(writes,['Write(.aeion/loop-bodies/**)'],job)
            self.assertIn('Bash(tools/knowledge/doc-links --for *)',tools)

    def test_enabled_high_severity_routes_model_and_supplies_turn_cap(self):
        self.configure()
        result=self.call('inner','--issue','42')
        self.assertEqual(result.returncode,0,result.stderr)
        args=json.loads((self.root/'invocation.json').read_text())
        self.assertEqual(args[args.index('--model')+1],'opus')
        self.assertEqual(args[args.index('--effort')+1],'high')
        self.assertEqual(args[args.index('--max-turns')+1],'30')

    def test_explicit_model_override_wins_and_bad_limits_refuse(self):
        self.configure('INNER_LOOP_MODEL=chosen-model\nLOOP_MAX_TURNS=7\n')
        self.assertEqual(self.call('inner','--issue','42').returncode,0)
        args=json.loads((self.root/'invocation.json').read_text())
        self.assertEqual(args[args.index('--model')+1],'chosen-model')
        self.assertEqual(args[args.index('--max-turns')+1],'7')
        self.configure('LOOP_TIMEOUT_SECONDS=0\n')
        self.assertNotEqual(self.call('outer').returncode,0)

    def test_deadline_stops_a_real_sleeping_job(self):
        result=subprocess.run(['python3',str(ROOT/'tools/loops/run'),'--timeout','1','--',
                               'python3','-c','import time; time.sleep(30)'],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,124)

    def test_terminating_wrapper_cancels_its_native_child(self):
        marker=self.root/'child-completed'
        ready=self.root/'child-ready'
        command=f'from pathlib import Path; import time; Path({str(ready)!r}).touch(); time.sleep(1); Path({str(marker)!r}).touch()'
        process=subprocess.Popen(['python3',str(ROOT/'tools/loops/run'),'--timeout','20','--','python3','-c',command],
                                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for _ in range(50):
                if ready.exists():break
                time.sleep(0.02)
            self.assertTrue(ready.exists())
            process.terminate()
            self.assertEqual(process.wait(timeout=3),130)
            time.sleep(1.1)
            self.assertFalse(marker.exists())
        finally:
            if process.poll() is None:process.kill();process.wait()


if __name__=='__main__':unittest.main()
