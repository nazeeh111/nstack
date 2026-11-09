"""Exercise the patched real finalized reader/assessment; counts are inert doubles."""
import importlib.util,pathlib,tempfile,json,sys
from unittest.mock import patch
P=pathlib.Path
file=P(sys.argv[1])/'scripts/check_db_quality.py';spec=importlib.util.spec_from_file_location('actual_codeql_quality',file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
with tempfile.TemporaryDirectory() as temp:
 db=P(temp)
 with patch.object(m,'baseline_lines_of_code',return_value=20),patch.object(m,'project_file_count',return_value=2),patch.object(m,'extractor_error_count',return_value=0),patch.object(m,'archive_file_count',return_value=2):
  for value in ('true','false',None):
   (db/'codeql-database.yml').write_text('language: python\n'+('finalised: '+value+'\n' if value else ''))
   try:result=m.assess(db);accepted=True
   except m.QualityFailure:accepted=False
   assert accepted==(value=='true'),(value,accepted)
   checks.append({'finalised_value':value,'accepted':accepted})
print(json.dumps({'checks':checks,'limits':'Actual patched reader and assess gate; source-count functions doubled. A real CodeQL extraction and query suite remain target commissioning.'},indent=2))
