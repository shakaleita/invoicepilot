import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

class ProductionAccessTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_rejects_requests_without_valid_token(self):
        with patch.dict(os.environ, {'APP_ENV': 'production', 'API_TOKEN': 'test-token'}):
            self.assertEqual(self.client.get('/api/does-not-exist').status_code, 401)
            self.assertEqual(self.client.get('/api/does-not-exist', headers={'X-API-Token': 'wrong'}).status_code, 401)
            self.assertEqual(self.client.get('/api/does-not-exist', headers={'X-API-Token': 'test-token'}).status_code, 404)

    def test_fails_closed_when_token_missing(self):
        with patch.dict(os.environ, {'APP_ENV': 'production', 'API_TOKEN': ''}):
            self.assertEqual(self.client.get('/api/does-not-exist').status_code, 503)
