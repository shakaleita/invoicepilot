import os, sys, tempfile, unittest, importlib
from pathlib import Path
from fastapi.testclient import TestClient

class CollectionsReportTest(unittest.TestCase):
    def test_aging_uses_only_sent_invoices_and_cents(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['DATABASE_PATH']=str(Path(tmp)/'test.db')
            sys.modules.pop('main',None)
            client=TestClient(importlib.import_module('main').app)
            customer=client.post('/api/customers',json={'name':'Company','email':'a@example.com'}).json()['id']
            def invoice():
                return client.post('/api/invoices',json={'customer_id':customer,
                    'lines':[{'description':'Service','quantity':2,'unit_price_cents':115}]}).json()['id']
            sent,paid,draft=invoice(),invoice(),invoice()
            assert client.patch(f'/api/invoices/{sent}/status',json={'status':'sent'}).status_code==200
            assert client.patch(f'/api/invoices/{paid}/status',json={'status':'paid'}).status_code==200
            report=client.get('/api/collections')
            self.assertEqual(report.status_code,200)
            self.assertEqual(report.json()['outstanding_invoices'],1)
            self.assertEqual(report.json()['buckets']['0_30']['total_cents'],230)
            invalid=client.post('/api/invoices',json={'customer_id':customer,
                 'lines':[{'description':'Bad','quantity':10001,'unit_price_cents':1}]})
            self.assertEqual(invalid.status_code,422)

    def test_explicit_due_dates_identify_only_outstanding_overdue_invoices(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['DATABASE_PATH']=str(Path(tmp)/'test.db')
            sys.modules.pop('main',None)
            client=TestClient(importlib.import_module('main').app)
            customer=client.post('/api/customers',json={'name':'Due Date Co','email':'billing@example.test'}).json()['id']
            def make(due):
                r=client.post('/api/invoices',json={
                    'customer_id':customer,'due_date':due,
                    'lines':[{'description':'Work','quantity':1,'unit_price_cents':399}]})
                self.assertEqual(r.status_code,201)
                return r.json()['id']
            overdue=make('2020-01-01')
            future=make('2099-12-31')
            paid=make('2020-01-01')
            for ident in (overdue,future):
                self.assertEqual(client.patch(f'/api/invoices/{ident}/status',json={'status':'sent'}).status_code,200)
            self.assertEqual(client.patch(f'/api/invoices/{paid}/status',json={'status':'paid'}).status_code,200)
            report=client.get('/api/collections').json()
            self.assertEqual(report['overdue_invoices'],1)
            self.assertEqual(report['overdue_cents'],399)
            self.assertEqual(report['outstanding_invoices'],2)
            self.assertEqual(client.post('/api/invoices',json={'customer_id':customer,'due_date':'nonsense',
                   'lines':[{'description':'X','quantity':1,'unit_price_cents':1}]}).status_code,422)
