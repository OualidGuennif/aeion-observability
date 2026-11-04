"""Reading a spec is bounded, path-confined and never starts work."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.api import FactoryApp,ApiError


class SpecPreviewTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)
  self.raw={'schema_version':2,'count':1,'features':[{'id':'001','title':'One','area':'foundation',
   'size':'S','parallel':False,'phase':'P0','tier':3,'write_paths':['demo/forum-app/'],
   'depends_on':[],'file':'001.md'}]}
  self.manifest=self.root/'MANIFEST.json';self.manifest.write_text(json.dumps(self.raw))
  self.spec=self.root/'001.md';self.spec.write_text('# One\n<script>untrusted text</script>')
  self.app=FactoryApp(self.manifest,self.root/'state',bootstrap_token='synthetic-only')

 def test_read_returns_literal_text_and_digest_without_admitting_work(self):
  code,body,_=self.app.spec_view(None,'001')
  self.assertEqual(code,200);self.assertEqual(body['markdown'],self.spec.read_text())
  self.assertEqual(body['sha256'],hashlib.sha256(self.spec.read_bytes()).hexdigest())
  self.assertEqual(self.app.store.board(),[])

 def test_unknown_oversize_and_symlink_specs_are_refused(self):
  with self.assertRaises(ApiError):self.app.spec_view(None,'../../outside')
  self.spec.write_bytes(b'x'*65537)
  with self.assertRaises(ApiError):self.app.spec_view(None,'001')
  self.spec.unlink();self.spec.symlink_to(self.manifest)
  with self.assertRaises(ApiError):self.app.spec_view(None,'001')

 def test_manifest_cannot_redirect_preview_outside_spec_directory(self):
  self.app.catalog.by_id['001']['file']='../outside.md'
  with self.assertRaises(ApiError):self.app.spec_view(None,'001')


if __name__=='__main__':unittest.main()
