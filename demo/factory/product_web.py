"""Fixed offline React tools. Candidate configs/scripts never select the checker."""
from pathlib import Path
from .isolation import DockerCheckRunner,IsolationError
from .product_checks import CHECKER_IMAGE


def prepare_web(web):
    modules=Path(web)/'node_modules'
    if modules.exists() or modules.is_symlink():raise IsolationError('web_dependencies_already_present')
    modules.symlink_to('/opt/aeion-checker/node_modules')


class FrozenWebRunner(DockerCheckRunner):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,image=CHECKER_IMAGE,**kwargs)

    def _flags(self,workspace,image=None,name=None):
        flags=super()._flags(workspace,image=image,name=name)
        tools=self.controller/'demo/factory/checker-tools'
        for file in ('build-web.mjs','vitest.config.mjs','tsconfig.web.json'):
            flags[-1:-1]=['-v',str(tools/file)+':/opt/aeion-checker/'+file+':ro']
        return flags
