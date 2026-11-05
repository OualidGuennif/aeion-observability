"""Candidate tests get their own disposable PostgreSQL, never the graded product's DB.

Spec: knowledge/components/factory-flue.md
The generated fixture administrator is deliberately available only to candidate tests,
so their test resource can initialize schemas without affecting a separately graded app.
"""
from .postgres import PostgresCheckRunner, DATABASE, USERNAME


class ProductUnitRunner(PostgresCheckRunner):
    def _flags(self, workspace, image=None, name=None):
        flags=super()._flags(workspace,image=image,name=name)
        if self._database is not None:
            flags[-1:-1]=['-e','AEION_TEST_POSTGRES_JDBC_URL=jdbc:postgresql://127.0.0.1:5432/'+DATABASE,
                '-e','AEION_TEST_POSTGRES_USERNAME='+USERNAME,
                '-e','AEION_TEST_POSTGRES_PASSWORD='+self._database.passwords['admin'],
                '-e','AGORA_DATABASE_ENABLED=true']
        return flags
