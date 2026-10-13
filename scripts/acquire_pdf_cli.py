"""Explicit P1 task staging workflow for Acquire PDFs."""
import argparse
import json
import sys
from pathlib import Path
import pdf_acquisition as pdf


def run(argv=None):
    parser=argparse.ArgumentParser(description='PRKE Acquire PDF: task staging ONLY. No campus-login, Zotero or Obsidian writes.')
    sub=parser.add_subparsers(dest='cmd',required=True)
    for cmd in ('prepare','manual-queue','manual-import','auto-fetch'):
        a=sub.add_parser(cmd)
        a.add_argument('--task-dir',required=True,help='Explicit task staging directory outside long-term library')
        a.add_argument('--candidates',required=True,help='Validated Acquire CandidateSet JSON')
        if cmd=='auto-fetch':
            a.add_argument('--execute',action='store_true',help='Enable real authorized public / publisher API HTTP calls; otherwise preview only')
            a.add_argument('--limit',type=int,default=10)
            a.add_argument('--env-file',help='Optional user private .env location; default is user home .env')
    sub.add_parser('doctor')
    a=parser.parse_args(argv)
    try:
        if a.cmd=='doctor':
            from inspect import signature
            assert 'paper' in signature(pdf.match_paper).parameters
            print('PASS: PDF acquisition adapter installed. Default network behavior: OFF. No credentials were accessed.')
            return 0
        p=pdf.safe_task_dir(a.task_dir)
        # Keep a validated source from original Acquire stage. Import from local scripts, not via agent inference.
        from acquire_cli import validate
        candidates=pdf.read_candidates(a.candidates);validate('candidate_set',candidates)
        if a.cmd=='prepare':
            pdf.ensure_task_dirs(p)
            print('PREPARED:',p/'pdf/manual_inbox');return 0
        elif a.cmd=='manual-queue': out,r=pdf.manual_queue(p,candidates)
        elif a.cmd=='manual-import':out,r=pdf.scan_manual(p,candidates)
        elif a.cmd=='auto-fetch':
            if a.limit<1 or a.limit>300:raise pdf.PDFError('limit 必须为 1–300')
            out,r=pdf.auto_fetch(p,candidates,limit=a.limit,execute=a.execute,env_file=a.env_file)
        print('REPORT:',out)
        print('COUNTS:',json.dumps({'total':len(r['items']), 'by_status':{k:sum(x.get('status')==k for x in r['items']) for k in sorted(set(x.get('status') for x in r['items']))}},ensure_ascii=False))
        return 0
    except (pdf.PDFError,ValueError,OSError) as e:
        print('ERROR:',str(e),file=sys.stderr);return 2
    except Exception as e:
        # Do not print network exception messages, which can contain API credentials in URLs.
        print('ERROR:',type(e).__name__,file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(run())
