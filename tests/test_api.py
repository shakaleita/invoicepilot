import os, tempfile, unittest, importlib, sys
from pathlib import Path
from fastapi.testclient import TestClient
class InvoicePilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        os.environ['DATABASE_PATH']=str(Path(cls.tmp.name)/'test.db')
        sys.modules.pop('main',None)
        cls.client=TestClient(importlib.import_module('main').app)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def test_totals_and_finalization(self):
        customer=self.client.post('/api/customers',json={'name':'Example','email':'invoice@example.com'})
        self.assertEqual(customer.status_code,201)
        i=self.client.post('/api/invoices',json={'customer_id':customer.json()['id'],'tax_percent':'20','lines':[{'description':'Design','quantity':2,'unit_price_cents':1250}]})
        self.assertEqual(i.status_code,201)
        self.assertEqual(i.json()['subtotal_cents'],2500)
        self.assertEqual(i.json()['tax_cents'],500)
        self.assertEqual(i.json()['total_cents'],3000)
        ident=i.json()['id']
        self.assertEqual(self.client.patch(f'/api/invoices/{ident}/status',json={'status':'paid'}).status_code,200)
        self.assertEqual(self.client.patch(f'/api/invoices/{ident}/status',json={'status':'draft'}).status_code,409)
    def test_bad_customer(self):
        self.assertEqual(self.client.post('/api/invoices',json={'customer_id':100000,'lines':[{'description':'A','quantity':1,'unit_price_cents':100}]}).status_code,404)
