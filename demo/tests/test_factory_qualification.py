"""Java-only or synthetic receipts cannot activate the complete product factory."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.flue_qualification import ready


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name)
        self.marker=self.root/'demo/.local/data/factory-flue-qualification.json'
        self.marker.parent.mkdir(parents=True)
        self.java={'protocol_sha256':'a'*64,'runtime':'flue-openshell','sandbox':'openshell',
            'protected_check':'passed','teardown_confirmed':True,'automatic_preparation':'qualified',
            'publication_state_machine':'qualified','routing_persistence':'qualified','expires_ns':1000}

    def admitted(self,proof):
        self.marker.write_text(json.dumps(proof))
        with patch('factory.flue_qualification.protocol_hash',return_value='a'*64):
            return ready(self.root,now_ns=100)

    def full(self):
        return {**self.java,'postgres_migration_restore':'qualified','postgres_least_privilege':'qualified',
            'react_browser_api':'qualified','protected_main':{'confirmed_main':True,'merge_sha':'b'*40,
                'main_sha':'b'*40,'synthetic':False}}

    def test_java_pipeline_alone_cannot_activate_postgres_react(self):
        self.assertFalse(self.admitted(self.java))

    def test_unconfirmed_or_synthetic_publication_cannot_activate(self):
        for field,value in (('confirmed_main',False),('synthetic',True),('merge_sha','invalid'),('main_sha',None)):
            proof=self.full();proof['protected_main'][field]=value
            with self.subTest(field=field):self.assertFalse(self.admitted(proof))

    def test_all_architecture_boundaries_and_current_protocol_are_required(self):
        self.assertTrue(self.admitted(self.full()))
        for field in ('postgres_migration_restore','postgres_least_privilege','react_browser_api','protected_main'):
            proof=self.full();del proof[field]
            with self.subTest(field=field):self.assertFalse(self.admitted(proof))

    def test_tool_admission_does_not_require_the_product_to_already_exist(self):
        proof={'schema_version':2,'protocol_sha256':'a'*64,'expires_ns':1000,
            'kind':'native_execution_capabilities','product_check':'prepared_product',
            'product_delivery_claimed':False,'capabilities':{name:{'status':'passed','evidence_sha256':'c'*64}
                for name in ('flue_openshell','external_acceptance','postgres_fixture',
                             'chromium_sandbox','preparation_and_publication','routing_persistence')}}
        self.assertTrue(self.admitted(proof))
        for name in proof['capabilities']:
            changed={**proof,'capabilities':{k:v for k,v in proof['capabilities'].items() if k!=name}}
            self.assertFalse(self.admitted(changed))
        self.assertFalse(self.admitted({**proof,'product_delivery_claimed':True}))
        self.assertFalse(self.admitted({**proof,'product_check':'prepared_gradle'}))

    def test_malformed_receipt_or_noninteger_expiry_holds_instead_of_crashing(self):
        for value in (None,[],"invalid",{**self.full(),'expires_ns':float('inf')},
                      {**self.full(),'expires_ns':True}):
            with self.subTest(shape=type(value).__name__):self.assertFalse(self.admitted(value))
        for field,value in (('protocol_sha256','c'*64),('expires_ns',99)):
            proof=self.full();proof[field]=value
            with self.subTest(field=field):self.assertFalse(self.admitted(proof))


if __name__=='__main__':unittest.main()
