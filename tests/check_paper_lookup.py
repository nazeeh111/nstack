"""Offline regressions against the actual patched JATS and API-walker sources."""
import contextlib,hashlib,importlib.util,io,json,pathlib,subprocess,sys,tempfile,types
P=pathlib.Path;root=P(sys.argv[1]).resolve();scripts=root/'scripts';sys.path.insert(0,str(scripts));checks=0

def run(name,args,input=None):return subprocess.run([sys.executable,str(scripts/name),*args],input=input,text=True,capture_output=True)
front='<front><article-meta><title-group><article-title>Fixture</article-title></title-group><permissions><license xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://licenses.example.test/terms?api_key=fixture-key"><license-p>CC BY fixture notice</license-p></license></permissions></article-meta></front>'
variants=[('',False),('<body/>',False),('<body> \n <!-- comment --> </body>',False),('<body><sec><title>Methods</title></sec></body>',False),('<body><xref>1</xref><graphic>image</graphic></body>',False),('<body/>outside tail is not body text',False),('<body><p>Measured evidence is present.</p></body>',True),('<body><sec sec-type="methods"><title>Methods</title><sec><p>Nested measured evidence.</p></sec></sec></body>',True)]
with tempfile.TemporaryDirectory() as tmp:
 tmp=P(tmp);xml=tmp/'article.xml'
 for body,full in variants:
  raw=('<pmc-articleset><article>'+front+body+'</article></pmc-articleset>').encode();xml.write_bytes(raw)
  for mode in [[],['--text-only']]:
   result=run('jats_to_text.py',[str(xml),*mode]);assert result.returncode==(0 if full else 2),(body,mode,result.stderr)
   if not full:
    payload=json.loads(result.stdout);assert payload['full_text_available'] is False;assert payload['provenance']['access_level']=='metadata_only'
   elif not mode:
    payload=json.loads(result.stdout);assert payload['full_text_available'] is True;assert payload['provenance']['input_sha256']==hashlib.sha256(raw).hexdigest();assert payload['metadata']['rights']['status']=='stated_not_independently_verified';assert 'fixture-key' not in result.stdout
   checks+=1
  if not full:
   result=run('jats_to_text.py',[str(xml),'--allow-metadata-only']);assert result.returncode==0 and not json.loads(result.stdout)['full_text_available'];checks+=1
 # A real body lacking the requested section is a selection failure, not metadata-only success.
 raw=('<article>'+front+'<body><sec><title>Methods</title><p>Observed text.</p></sec></body></article>').encode();xml.write_bytes(raw)
 result=run('jats_to_text.py',[str(xml),'--sections','RESULTS']);assert result.returncode==1 and 'no section matched' in result.stderr;checks+=1
 result=run('jats_to_text.py',[str(xml),'--source-locator','https://source.example.test/paper?api_key=fixture-key','--query','search=room&api_key=fixture-key','--retrieved-at','2026-01-01T00:00:00Z']);payload=json.loads(result.stdout);assert 'fixture-key' not in result.stdout;assert payload['provenance']['retrieval']['retrieved_at']=='2026-01-01T00:00:00Z';assert payload['provenance']['source_span']['section_selectors']==['./body/sec[1]'];checks+=1
 # Adjacent parser controls, including the shared read_input default path.
 error='<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/api/errors#bad-query</id><title>Error</title><summary>Invalid fixture query</summary></entry></feed>';xml.write_text(error);result=run('arxiv_atom.py',[str(xml)]);assert result.returncode!=0 and 'error' in result.stderr.lower();checks+=1

spec=importlib.util.spec_from_file_location('nstack_walk_fixture',scripts/'paginate.py');walker=importlib.util.module_from_spec(spec);sys.modules[spec.name]=walker;spec.loader.exec_module(walker);walker.time=types.SimpleNamespace(sleep=lambda _:None)
walker.os=types.SimpleNamespace(environ={});calls=[];walker.fetch=lambda url:calls.append(url)
for key in [None,'','   ']:
 walker.os=types.SimpleNamespace(environ={} if key is None else {'OPENALEX_API_KEY':key})
 with contextlib.redirect_stderr(io.StringIO()):
  try:walker.walk(walker.APIS['openalex'],'search=fixture',page_size=100,max_records=10,max_calls=5,verbose=False)
  except SystemExit as exc:assert exc.code!=0
  else:raise AssertionError('missing/blank key accepted')
 assert not calls;checks+=1
walker.os=types.SimpleNamespace(environ={'OPENALEX_API_KEY':'fixture-key'})

def walk(pages,records=10,calls_limit=5):
 count=[0]
 def fetch(url):
  assert 'api_key=fixture-key' in url;page=pages[count[0]];count[0]+=1;return page
 walker.fetch=fetch
 result=walker.walk(walker.APIS['openalex'],'search=fixture',page_size=100,max_records=records,max_calls=calls_limit,verbose=False)
 assert 'fixture-key' not in json.dumps(result[2]);return (*result,count[0])

def page(id,next,total=2):return {'meta':{'count':total,'next_cursor':next},'results':[{'id':id}]}
records,recon,urls,count=walk([page('W1','two'),page('W2',None)]);assert len(records)==2 and recon.complete and recon.ok and count==2;checks+=1
records,recon,urls,count=walk([page('W1','*',3)]);assert len(records)==1 and not recon.complete and not recon.ok and recon.stopped_for_repetition and count==1;checks+=1
records,recon,urls,count=walk([page('W1','two',4),page('W1','three',4)]);assert len(records)==1 and recon.pages==2 and recon.stopped_for_repetition and not recon.ok;checks+=1
records,recon,urls,count=walk([page('W1',None,3)]);assert len(records)==1 and not recon.complete and not recon.ok and not recon.stopped_for_repetition;checks+=1
records,recon,urls,count=walk([page('W1','two',5)],records=1);assert len(records)==1 and recon.stopped_at_limit and not recon.complete and recon.ok;checks+=1
# The dry-run request is also credential-free in its output.
walker.fetch=lambda _:(_ for _ in ()).throw(AssertionError('dry run fetched'))
output=io.StringIO()
with contextlib.redirect_stdout(output):assert walker.main(['--api','openalex','--query','search=fixture','--dry-run'])==0
assert 'fixture-key' not in output.getvalue();checks+=1
print(json.dumps({'offline_checks':checks,'empty_JATS_metadata_only':True,'license_and_input_provenance':True,'missing_key_zero_fetches':True,'repeated_pages_not_recounted':True,'source_entitlement_or_live_API_calls':False}))
