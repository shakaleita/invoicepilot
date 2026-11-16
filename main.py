import os, sqlite3
from contextlib import contextmanager
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

DB = os.getenv('DATABASE_PATH', 'app.db')
app = FastAPI(title='InvoicePilot API', version='1.0.0')
@contextmanager
def conn():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
with conn() as db:
    db.executescript("""CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY,customer_id INTEGER NOT NULL REFERENCES customers(id),status TEXT NOT NULL DEFAULT 'draft',tax_percent TEXT NOT NULL DEFAULT '0',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS lines(id INTEGER PRIMARY KEY,invoice_id INTEGER NOT NULL REFERENCES invoices(id),description TEXT NOT NULL,quantity INTEGER NOT NULL,unit_price_cents INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS invoice_events(id INTEGER PRIMARY KEY,invoice_id INTEGER NOT NULL REFERENCES invoices(id),from_status TEXT NOT NULL,to_status TEXT NOT NULL,changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);""")
class Customer(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)
class Line(BaseModel):
    description: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=10000)
    unit_price_cents: int = Field(ge=0, le=100000000)
class Invoice(BaseModel):
    customer_id: int
    tax_percent: Decimal = Field(default=Decimal('0'),ge=0,le=100)
    lines: list[Line] = Field(min_length=1, max_length=200)
class Status(BaseModel):
    status: str

def detail(db, invoice_id):
    row=db.execute('SELECT i.*,c.name customer_name FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.id=?',(invoice_id,)).fetchone()
    if not row: raise HTTPException(404,'Invoice not found')
    lines=[dict(x) for x in db.execute('SELECT description,quantity,unit_price_cents FROM lines WHERE invoice_id=?',(invoice_id,))]
    subtotal=sum(x['quantity']*x['unit_price_cents'] for x in lines)
    tax=int((Decimal(subtotal)*Decimal(row['tax_percent'])/100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    return {**dict(row),'lines':lines,'subtotal_cents':subtotal,'tax_cents':tax,'total_cents':subtotal+tax}
@app.get('/api/customers')
def customers():
    with conn() as db:return [dict(r) for r in db.execute('SELECT * FROM customers ORDER BY id DESC')]
@app.post('/api/customers',status_code=201)
def create_customer(customer:Customer):
    with conn() as db:
        cur=db.execute('INSERT INTO customers(name,email) VALUES(?,?)',(customer.name,customer.email))
        return {'id':cur.lastrowid,**customer.model_dump()}
@app.get('/api/invoices')
def invoices():
    with conn() as db:
        return [detail(db,r['id']) for r in db.execute('SELECT id FROM invoices ORDER BY id DESC').fetchall()]
@app.get('/api/collections')
def collections():
    """Age outstanding *sent* invoices by creation date (not a contractual due date)."""
    with conn() as db:
        pending=db.execute("""SELECT id,CAST(julianday('now')-julianday(created_at) AS INTEGER) age_days
            FROM invoices WHERE status='sent' ORDER BY id""").fetchall()
        buckets={'0_30':{'invoices':0,'total_cents':0},
                 '31_60':{'invoices':0,'total_cents':0},
                 '61_plus':{'invoices':0,'total_cents':0}}
        for invoice in pending:
            days=max(0,invoice['age_days'] or 0)
            key='0_30' if days<=30 else '31_60' if days<=60 else '61_plus'
            buckets[key]['invoices']+=1
            buckets[key]['total_cents']+=detail(db,invoice['id'])['total_cents']
        return {'method':'invoice_creation_age_not_due_date',
                'outstanding_invoices':len(pending),'buckets':buckets}

@app.get('/api/invoices/{invoice_id}')
def get_invoice(invoice_id:int):
    with conn() as db:return detail(db,invoice_id)
@app.post('/api/invoices',status_code=201)
def create_invoice(invoice:Invoice):
    with conn() as db:
        if not db.execute('SELECT 1 FROM customers WHERE id=?',(invoice.customer_id,)).fetchone():raise HTTPException(404,'Customer not found')
        cur=db.execute('INSERT INTO invoices(customer_id,tax_percent) VALUES(?,?)',(invoice.customer_id,str(invoice.tax_percent)))
        db.executemany('INSERT INTO lines(invoice_id,description,quantity,unit_price_cents) VALUES(?,?,?,?)',[(cur.lastrowid,x.description,x.quantity,x.unit_price_cents) for x in invoice.lines])
        return detail(db,cur.lastrowid)
@app.patch('/api/invoices/{invoice_id}/status')
def update_status(invoice_id:int,payload:Status):
    if payload.status not in ('draft','sent','paid','void'):raise HTTPException(422,'Invalid status')
    with conn() as db:
        old=detail(db,invoice_id)['status']
        if old in ('paid','void') and payload.status!=old:raise HTTPException(409,'Finalised invoice cannot be changed')
        if old != payload.status:
            db.execute('UPDATE invoices SET status=? WHERE id=?',(payload.status,invoice_id))
            db.execute('INSERT INTO invoice_events(invoice_id,from_status,to_status) VALUES(?,?,?)',(invoice_id,old,payload.status))
        return detail(db,invoice_id)
@app.get('/api/invoices/{invoice_id}/events')
def invoice_events(invoice_id:int):
    """Return an immutable, chronological audit trail of invoice status changes."""
    with conn() as db:
        detail(db,invoice_id)
        return [dict(row) for row in db.execute(
            'SELECT id,invoice_id,from_status,to_status,changed_at FROM invoice_events WHERE invoice_id=? ORDER BY id',
            (invoice_id,)).fetchall()]

@app.get('/',response_class=HTMLResponse)
def home():return Path(__file__).with_name('index.html').read_text(encoding='utf8')

@app.get('/api/health')
def health():
    return {'status':'ok'}
@app.get('/api/insights')
def insights():
    with conn() as db:
        data=[detail(db,r['id']) for r in db.execute('SELECT id FROM invoices').fetchall()]
        return {'customers':db.execute('SELECT COUNT(*) FROM customers').fetchone()[0],'invoices_by_status':{k:sum(x['status']==k for x in data) for k in ('draft','sent','paid','void')},'paid_revenue_cents':sum(x['total_cents'] for x in data if x['status']=='paid'),'outstanding_cents':sum(x['total_cents'] for x in data if x['status']=='sent')}

@app.middleware('http')
async def security_headers(request,call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    return response

# Local demos work without credentials. Production APIs require an explicit token.
import hmac
from fastapi.responses import JSONResponse

@app.middleware('http')
async def require_api_auth(request, call_next):
    path = request.url.path
    if path.startswith('/api/') and path != '/api/health':
        token = os.getenv('API_TOKEN')
        if os.getenv('APP_ENV') == 'production' or token:
            if not token:
                return JSONResponse({'error': 'API authentication must be configured in production'}, status_code=503)
            if not hmac.compare_digest(request.headers.get('x-api-token', ''), token):
                return JSONResponse({'error': 'Unauthorized'}, status_code=401)
    return await call_next(request)



@app.get('/api/export/invoices.csv')
def export_invoices_csv():
    """Download a read-only snapshot of the local demo dataset."""
    from fastapi.responses import Response
    from data_export import serialize_csv
    with conn() as connection:
        cursor = connection.execute("SELECT id,customer_id,status,tax_percent,created_at FROM invoices ORDER BY id")
        columns = [column[0] for column in cursor.description]
        content = serialize_csv(cursor.fetchall(), columns)
    return Response(content=content, media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition':'attachment; filename="invoices.csv"',
                             'Cache-Control':'no-store'})
