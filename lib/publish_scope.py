"""Explicit named-destination gate for selected training templates; local by default."""
import argparse,pathlib,re,sys

def publish_if_authorized(model,artifact,argv=None):
 p=argparse.ArgumentParser(add_help=False)
 p.add_argument('--publish-repository');p.add_argument('--publish-visibility',choices=['private','public']);p.add_argument('--publish-rights');p.add_argument('--publish-artifact')
 args,_=p.parse_known_args(sys.argv[1:] if argv is None else argv)
 fields=[args.publish_repository,args.publish_visibility,args.publish_rights,args.publish_artifact]
 if not any(fields):return None
 if not all(fields):raise ValueError('Publishing needs the named repository, visibility, rights basis and exact saved artifact')
 if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',args.publish_repository):raise ValueError('Require an explicit owner/repository')
 actual=pathlib.Path(artifact).resolve(strict=True)
 if not actual.is_dir() or pathlib.Path(args.publish_artifact).resolve(strict=True)!=actual:raise ValueError('The authorized artifact differs from the saved model')
 return model.push_to_hub(args.publish_repository,private=args.publish_visibility=='private')
