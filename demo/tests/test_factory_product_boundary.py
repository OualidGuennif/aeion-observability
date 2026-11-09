"""Security regressions at the untrusted product export boundary."""
from pathlib import Path
import sys
import base64
import subprocess
import tempfile
import unittest
from unittest.mock import patch
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1]/'app')]
from factory.agent_files import parse_files, BuilderError
from factory.artifact import _path_problem

class ProductBoundaryTests(unittest.TestCase):
    def test_candidate_unit_tests_cannot_rewrite_the_graded_production_workspace(self):
        from factory.product_checks import ProductCheckRunner, APP
        from factory.isolation import DockerCheckRunner
        from factory.target import Target,ProtectedCheck
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';app=source/APP;app.mkdir(parents=True)
            (app/'build.gradle').write_text('// Public fixed build\n')
            (app/'settings.gradle').write_text('// Public settings\n')
            (app/'public.txt').write_text('original production source')
            for args in (['init','-q'],['config','user.name','Fixture'],['config','user.email','fixture@example.invalid'],
                         ['add','.'],['commit','-qm','public source']):
                subprocess.run(['git','-C',str(source),*args],check=True,capture_output=True)
            sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
            contract=root/'acceptance.mjs';contract.write_text('// Public fixture\n')
            target=Target('workspace-fixture','099','o/r',root,source,sha,[APP],contract,
                ProtectedCheck('prepared_product',[],{},contract,'EXTERNAL.mjs',60))
            calls=[]
            def gradle(_runner,command,cwd,**_kwargs):
                cwd=Path(cwd);calls.append((command,cwd))
                if 'quarkusBuild' in command:
                    self.assertNotIn('test',command)
                    package=cwd/(APP+'build/quarkus-app');package.mkdir(parents=True)
                    (package/'quarkus-run.jar').write_bytes(b'immutable-compiled-product')
                else:
                    self.assertEqual(len(calls),2)
                    self.assertNotEqual(cwd,calls[0][1])
                    (cwd/(APP+'public.txt')).write_text('mutated by candidate unit test')
                    package=cwd/(APP+'build/quarkus-app');package.mkdir(parents=True)
                    (package/'quarkus-run.jar').write_bytes(b'forged test artifact')
                return subprocess.CompletedProcess(command,0,stdout='',stderr='')
            class Database:
                name='owned-public-fixture'
                def __init__(self,*_):pass
                def __enter__(self):return self
                def __exit__(self,*_):pass
            def verify(_target,_database):
                production=calls[0][1]
                self.assertEqual((production/(APP+'public.txt')).read_text(),'original production source')
                self.assertEqual((production/(APP+'build/quarkus-app/quarkus-run.jar')).read_bytes(),b'immutable-compiled-product')
                return True,{'reason':'passed'}
            runner=ProductCheckRunner(root)
            with patch.object(DockerCheckRunner,'__call__',gradle), \
                    patch.object(runner,'qualification',return_value={'status':'qualified'}), \
                    patch('factory.product_checks.DisposablePostgres',Database), \
                    patch.object(runner,'_call',return_value=subprocess.CompletedProcess([],0,stdout='',stderr='')), \
                    patch.object(runner,'_kill'),patch.object(runner,'_verify',side_effect=verify):
                passed,detail=runner.check_target(target,source)
            self.assertTrue(passed)
            self.assertTrue(detail['isolation']['production_packaged_before_tests'])
            self.assertEqual(len(calls),2)

    def test_startup_refusals_never_probe_a_port_owned_by_the_main_app(self):
        from factory.product_checks import ProductCheckRunner, APP
        from factory.isolation import DockerCheckRunner
        from factory.target import Target, ProtectedCheck
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';app=source/APP;app.mkdir(parents=True)
            for filename in ('build.gradle','settings.gradle'):(app/filename).write_text('// Public fixture\n')
            for args in (['init','-q'],['config','user.name','Fixture'],['config','user.email','fixture@example.invalid'],
                         ['add','.'],['commit','-qm','fixture']):
                subprocess.run(['git','-C',str(source),*args],check=True,capture_output=True)
            sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
            contract=root/'acceptance.mjs';contract.write_text('// Public fixture\n')
            target=Target('startup-port-fixture','001','o/r',root,source,sha,[APP],contract,
                ProtectedCheck('prepared_product',[],{},contract,'EXTERNAL.mjs',60))
            state={'main_app_running':False,'startup_checked':False}
            def gradle(_runner,command,cwd,**_kwargs):
                if 'quarkusBuild' in command:
                    package=Path(cwd)/(APP+'build/quarkus-app');package.mkdir(parents=True)
                    (package/'quarkus-run.jar').write_bytes(b'fixture')
                return subprocess.CompletedProcess(command,0,stdout='',stderr='')
            class Database:
                name='owned-fixture'
                def __init__(self,*_):pass
                def __enter__(self):return self
                def __exit__(self,*_):pass
            def call(args,**_kwargs):
                if 'run' in args:state['main_app_running']=True
                return subprocess.CompletedProcess(args,0,stdout='',stderr='')
            def refusals(*_args):
                self.assertFalse(state['main_app_running'], 'Refusal probes would read another app on port8080')
                state['startup_checked']=True
                return True,'passed'
            runner=ProductCheckRunner(root)
            with patch.object(DockerCheckRunner,'__call__',gradle), \
                    patch.object(runner,'qualification',return_value={'status':'qualified'}), \
                    patch('factory.product_checks.DisposablePostgres',Database), \
                    patch.object(runner,'_call',side_effect=call),patch.object(runner,'_kill'), \
                    patch('factory.product_startup.startup_refusals',side_effect=refusals), \
                    patch.object(runner,'_verify',return_value=(True,{'reason':'passed'})):
                passed,_detail=runner.check_target(target,source)
            self.assertTrue(passed)
            self.assertTrue(state['startup_checked'])

    def test_checker_teardown_requires_confirmed_absence(self):
        from factory.product_checks import ProductCheckRunner
        from factory.isolation import DockerCheckRunner,IsolationError
        runner=ProductCheckRunner('/public-fixture')
        for code,output in ((0,''),(0,'still-running-id'),(1,'')):
            with self.subTest(code=code,output=output),patch.object(DockerCheckRunner,'_kill'), \
                    patch('factory.product_checks.subprocess.run',return_value=subprocess.CompletedProcess([],code,stdout=output,stderr='')):
                if code or output:
                    with self.assertRaisesRegex(IsolationError,'teardown_unconfirmed'):runner._kill('aeion-owned-fixture')
                else:runner._kill('aeion-owned-fixture')

    def test_nested_git_configuration_cannot_hide_unreviewed_product_files(self):
        for name in ('.gitignore', '.gitattributes', '.gitmodules', '.GITignore'):
            with self.subTest(name=name), self.assertRaises(BuilderError):
                parse_files({'files':[{'path':'demo/forum-app/'+name,'content':'*\n'}]}, ['demo/forum-app/'])
            with self.subTest(artifact=name):
                self.assertEqual(_path_problem('demo/forum-app/'+name, Path('/tmp'), ['demo/forum-app/']), 'git_metadata')

    def test_preexisting_gitignore_cannot_hide_an_exported_environment_file(self):
        from factory.flue_builder import scoped_changes
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            subprocess.run(['git','init','-q',str(repo)],check=True,capture_output=True)
            (repo/'.gitignore').write_text('.env\n')
            seeded={'demo/forum-docs/input.md':b'public input'}
            exported={'workspace/'+name:base64.b64encode(value).decode() for name,value in seeded.items()}
            exported['workspace/demo/forum-docs/.env']=base64.b64encode(b'UNREVIEWED=1\n').decode()
            with self.assertRaisesRegex(BuilderError,'ignored_path'):
                scoped_changes(exported,seeded,['demo/forum-docs/'],repo)

    def test_scoped_changes_refuses_a_changed_file_whose_spec_doc_is_outside_write_scopes(self):
        from factory.flue_builder import scoped_changes
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True, capture_output=True)
            filter_path = 'demo/forum-app/RequestValidationFilter.java'
            seeded = {filter_path: b'// Spec: knowledge/components/request-validation.md\nclass R {}\n'}
            scopes = ['demo/forum-app/', 'knowledge/components/agora-product.md']
            for candidate in (b'// Spec: knowledge/components/request-validation.md\nclass R { int x; }\n',
                              b'// Spec: knowledge/components/agora-product.md\nclass R { int x; }\n'):
                exported = {'workspace/' + filter_path: base64.b64encode(candidate).decode()}
                with self.assertRaisesRegex(BuilderError, 'knowledge_doc_outside_scope') as ctx:
                    scoped_changes(exported, seeded, scopes, repo)
                self.assertEqual(ctx.exception.blocked_files,
                                 [filter_path + ' -> knowledge/components/request-validation.md'])
            reverted = {'workspace/' + filter_path: base64.b64encode(seeded[filter_path]).decode(),
                        'workspace/demo/forum-app/ForumSettings.java':
                        base64.b64encode(b'// Spec: knowledge/components/agora-product.md\nclass S {}\n').decode()}
            self.assertEqual(list(scoped_changes(reverted, seeded, scopes, repo)),
                             ['demo/forum-app/ForumSettings.java'])

if __name__ == '__main__': unittest.main()
