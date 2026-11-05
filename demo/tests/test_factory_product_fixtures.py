"""Public migration fixture fidelity; no operator database or credentials are used."""
import hashlib
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.product_postgres import sqlite_fixture,expected_rows,TABLES

class ProductFixtureTests(unittest.TestCase):
    def test_sqlite_import_fixture_preserves_every_nanosecond_identifier_and_null(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fixture.sqlite';digest=sqlite_fixture(path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
            self.assertEqual(path.stat().st_mode & 0o222,0)
            with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:
                result={name:[dict(zip(columns,row)) for row in db.execute('SELECT '+','.join(columns)+' FROM '+name)]
                    for name,columns in TABLES.items()}
            self.assertEqual(result,expected_rows())
            self.assertEqual(result['threads'][0]['created_ns'],1700000000000000001)
            self.assertIsNone(result['sessions'][0]['revoked_ns'])

if __name__=='__main__':unittest.main()
