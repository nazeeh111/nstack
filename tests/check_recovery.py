"""Real loopback capture/restart exercise. This is not a production sender."""
import argparse,hashlib,http.client,http.server,json,os,pathlib,socket,sqlite3,subprocess,sys,tempfile,time,urllib.error,urllib.parse,urllib.request
P=pathlib.Path
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'))
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def connect(path):
 db=sqlite3.connect(path);db.row_factory=sqlite3.Row;return db
def receiver(path,drop):
 with connect(path) as db:
  db.executescript('CREATE TABLE IF NOT EXISTS effects(business_id TEXT PRIMARY KEY, account TEXT, recipient TEXT, operation TEXT, payload_sha256 TEXT, receipt TEXT); CREATE TABLE IF NOT EXISTS requests(request_key TEXT PRIMARY KEY,business_id TEXT); CREATE TABLE IF NOT EXISTS suppression(recipient TEXT PRIMARY KEY);')
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def reply(self,status,value):
   raw=canonical(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def do_GET(self):
   u=urllib.parse.urlsplit(self.path)
   if u.path!='/receipt':return self.reply(404,{'error':'unknown fixture path'})
   key=urllib.parse.parse_qs(u.query).get('business_id',[''])[0]
   with connect(path) as db:row=db.execute('SELECT * FROM effects WHERE business_id=?',(key,)).fetchone()
   return self.reply(200,dict(row)) if row else self.reply(404,{'state':'absent'})
  def do_POST(self):
   if self.path!='/capture':return self.reply(404,{'error':'unknown fixture path'})
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<10000:return self.reply(400,{'error':'bounded fixture body required'})
   value=json.loads(self.rfile.read(size));key=self.headers.get('Idempotency-Key','')
   required={'business_id','account','recipient','operation','payload','payload_sha256','expires_at'}
   if set(value)!=required or value['operation']!='capture_fixture' or not value['recipient'].endswith('@example.test') or not key or digest(value['payload'])!=value['payload_sha256']:return self.reply(400,{'error':'fixture binding mismatch'})
   if value['expires_at']<=time.time():return self.reply(410,{'error':'expired'})
   bindings=('business_id','account','recipient','operation','payload_sha256')
   with connect(path) as db:
    if db.execute('SELECT 1 FROM suppression WHERE recipient=?',(value['recipient'],)).fetchone():return self.reply(403,{'error':'suppressed'})
    prior=db.execute('SELECT e.* FROM effects e LEFT JOIN requests r ON r.business_id=e.business_id WHERE e.business_id=? OR r.request_key=?',(value['business_id'],key)).fetchone()
    if prior:
     if any(prior[k]!=value[k] for k in bindings):return self.reply(409,{'error':'identity/payload mismatch'})
     result=dict(prior)
    else:
     result={k:value[k] for k in bindings};result['receipt']='capture:'+digest(result)
     db.execute('INSERT INTO effects VALUES(?,?,?,?,?,?)',tuple(result[k] for k in (*bindings,'receipt')))
    db.execute('INSERT OR IGNORE INTO requests VALUES(?,?)',(key,value['business_id']))
   # Commit is durable before deliberately losing acknowledgement.
   if self.server.drop:
    self.server.drop=False;self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
   return self.reply(200,result)
 server=http.server.HTTPServer(('127.0.0.1',0),Handler);server.drop=drop
 print(canonical({'endpoint':'http://127.0.0.1:'+str(server.server_port)}),flush=True);server.serve_forever()

def fetch(endpoint,path,body=None,key=None):
 u=urllib.parse.urlsplit(endpoint)
 if u.scheme!='http' or u.hostname!='127.0.0.1' or not u.port or u.username or u.password or u.path or u.query or u.fragment:raise ValueError('Only an explicit loopback fixture receiver is allowed')
 headers={'Content-Type':'application/json'}
 if key:headers['Idempotency-Key']=key
 request=urllib.request.Request(endpoint+path,data=canonical(body).encode() if body is not None else None,headers=headers)
 class NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*args,**kwargs):return None
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
 try:
  with opener.open(request,timeout=3) as response:return response.status,json.load(response)
 except urllib.error.HTTPError as exc:return exc.code,json.load(exc)

def dispatch(dbpath,intentpath,endpoint,stop):
 body=json.loads(P(intentpath).read_text());identity=body['business_id'];frozen=canonical(body)
 if digest(body['payload'])!=body['payload_sha256']:raise ValueError('Payload digest mismatch')
 with connect(dbpath) as db:
  db.execute('CREATE TABLE IF NOT EXISTS intents(business_id TEXT PRIMARY KEY,body TEXT,phase TEXT,receipt TEXT)')
  old=db.execute('SELECT * FROM intents WHERE business_id=?',(identity,)).fetchone()
  if old and old['body']!=frozen:raise ValueError('Immutable identity, payload or expiry changed')
  if not old:db.execute('INSERT INTO intents VALUES(?,?,?,NULL)',(identity,frozen,'prepared'))
 if stop:return 75
 code,receipt=fetch(endpoint,'/receipt?'+urllib.parse.urlencode({'business_id':identity}))
 if code==200:
  if any(receipt[k]!=body[k] for k in ('business_id','account','recipient','operation','payload_sha256')):raise ValueError('Receiver receipt does not bind this exact intent')
  phase='confirmed'
 elif code!=404:raise ValueError('Authoritative reconciliation unavailable; no dispatch')
 elif old and old['phase']=='blocked':return 76
 elif body['expires_at']<=time.time():phase='blocked';receipt={'error':'expired without reconciled receipt'}
 else:
  try:code,receipt=fetch(endpoint,'/capture',body,digest({k:body[k] for k in ('business_id','account','recipient','operation')}))
  except (OSError,http.client.RemoteDisconnected):phase='unknown';receipt=None
  else:phase='confirmed' if code==200 else 'blocked' if code in (400,403,409,410) else 'unknown'
 with connect(dbpath) as db:db.execute('UPDATE intents SET phase=?,receipt=? WHERE business_id=?',(phase,canonical(receipt),identity))
 return 0 if phase=='confirmed' else 75 if phase=='unknown' else 76

def check(root):
 root=P(root);root.mkdir(parents=True,exist_ok=True);run=root/('run-'+str(time.time_ns()));run.mkdir(mode=0o700);serverdb=run/'receiver.sqlite';clientdb=run/'dispatcher.sqlite';script=P(__file__).resolve();server=None
 def start(drop=False):
  command=[sys.executable,str(script),'receiver','--db',str(serverdb)]+(['--drop-first-ack'] if drop else [])
  process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);line=process.stdout.readline()
  if not line:raise RuntimeError('Capture receiver failed to start: '+process.stderr.read())
  return process,json.loads(line)['endpoint']
 def client(body,endpoint,stop=False):
  path=run/(body['business_id']+'.json');path.write_text(canonical(body));command=[sys.executable,str(script),'dispatch','--db',str(clientdb),'--intent',str(path),'--endpoint',endpoint]+(['--stop-before-send'] if stop else [])
  return subprocess.run(command,capture_output=True,text=True).returncode
 def intent(id):
  payload={'candidate':'synthetic-candidate','requisition':id,'text':'capture only'}
  return {'business_id':id,'account':'local-fixture-account','recipient':'fixture@example.test','operation':'capture_fixture','payload':payload,'payload_sha256':digest(payload),'expires_at':time.time()+120}
 def count():
  with connect(serverdb) as db:return db.execute('SELECT count(*) FROM effects').fetchone()[0]
 try:
  server,endpoint=start(True);body=intent('lost-ack')
  assert client(body,endpoint)==75 and count()==1
  server.terminate();server.wait(timeout=5);server,endpoint=start()
  assert client(body,endpoint)==0 and client(body,endpoint)==0 and count()==1
  # A different request key still cannot duplicate one business effect.
  status,_=fetch(endpoint,'/capture',body,'different-transport-key');assert status==200 and count()==1
  changed=dict(body);changed['payload']={'text':'changed'};changed['payload_sha256']=digest(changed['payload']);assert client(changed,endpoint)!=0 and count()==1
  status,_=fetch(endpoint,'/capture',changed,'another-key');assert status==409 and count()==1
  wrong=dict(body,account='another-account');status,_=fetch(endpoint,'/capture',wrong,'foreign-account-key');assert status==409 and count()==1
  expired=intent('expired');expired['expires_at']=time.time()-1;assert client(expired,endpoint)==76 and count()==1
  suppressed=intent('suppressed')
  with connect(serverdb) as db:db.execute('INSERT INTO suppression VALUES(?)',(suppressed['recipient'],))
  assert client(suppressed,endpoint)==76 and client(suppressed,endpoint)==76 and count()==1
  with connect(serverdb) as db:db.execute('DELETE FROM suppression')
  before=intent('before-send');assert client(before,endpoint,True)==75 and count()==1;assert client(before,endpoint)==0 and count()==2
  with connect(serverdb) as db:counts={r['business_id']:r['n'] for r in db.execute('SELECT business_id,count(*) n FROM effects GROUP BY business_id')}
  with connect(clientdb) as db:phases={r['business_id']:r['phase'] for r in db.execute('SELECT business_id,phase FROM intents')}
  result={'actual_http_capture':True,'receiver_and_dispatcher_restarted':True,'committed_write_lost_ack_exactly_one_effect':counts['lost-ack']==1,'before_send_interruption_recovered_once':counts['before-send']==1,'business_identity_duplicate_key_safe':True,'changed_payload_account_rejected':True,'expiry_and_suppression_stop':True,'phases':phases,'observed_effects':counts,'artifacts':str(run),'source_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'limits':'Loopback synthetic receiver only. No real message, application, upload, account, scheduler or production provider acceptance is implied.'}
  target=root/'capture-recovery.json';temporary=root/'capture-recovery.new.json';temporary.write_text(json.dumps(result,indent=2)+'\n');os.replace(temporary,target);print(json.dumps(result,indent=2));return result
 finally:
  if server is not None and server.poll() is None:server.terminate();server.wait(timeout=5)

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
 r=sub.add_parser('receiver');r.add_argument('--db',required=True);r.add_argument('--drop-first-ack',action='store_true')
 d=sub.add_parser('dispatch');d.add_argument('--db',required=True);d.add_argument('--intent',required=True);d.add_argument('--endpoint',required=True);d.add_argument('--stop-before-send',action='store_true')
 c=sub.add_parser('check');c.add_argument('--output',required=True);a=parser.parse_args()
 if a.command=='receiver':receiver(a.db,a.drop_first_ack)
 elif a.command=='dispatch':raise SystemExit(dispatch(a.db,a.intent,a.endpoint,a.stop_before_send))
 else:check(a.output)
