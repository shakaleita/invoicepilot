import os,sys,importlib,tempfile,unittest
from pathlib import Path
from fastapi.testclient import TestClient
class InsightsTest(unittest.TestCase):
    def test_health_and_analytics(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['DATABASE_PATH']=str(Path(tmp)/'test.db')
            sys.modules.pop('main',None)
            client=TestClient(importlib.import_module('main').app)
            health=client.get('/api/health')
            self.assertEqual(health.json()['status'],'ok')
            self.assertEqual(health.headers['x-content-type-options'],'nosniff')
            insights=client.get('/api/insights')
            self.assertEqual(insights.status_code,200)
            self.assertIsInstance(insights.json(),dict)
