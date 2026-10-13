"""Evidence-first synthesis staging CLI; scientific judgments require an external reviewer."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from synthesize_engine import ScienceError,build,read,write_new,markdown,digest
ROOT=Path(__file__).resolve().parents[1]
def doctor(_):
    for rel in ('routes/synthesize.md','references/synthesize/evidence-and-gap-gates.md','schemas/synthesize/synthesis_input.schema.json'):
        if not (ROOT/rel).is_file():raise ScienceError('缺少 '+rel)
    import jsonschema
    jsonschema.Draft202012Validator.check_schema(read(ROOT/'schemas/synthesize/synthesis_input.schema.json'))
    print('PASS: Synthesize installed (no external search or independent scientific review implied)')
def stage(a):
    inp=Path(a.input).expanduser().resolve();out=Path(a.output).expanduser().resolve()
    if out.exists():raise ScienceError('输出目录已存在，禁止覆写: '+str(out))
    if inp==out or inp in out.parents:raise ScienceError('输出不得覆盖输入路径')
    packet=read(inp)
    import jsonschema
    jsonschema.validate(packet,read(ROOT/'schemas/synthesize/synthesis_input.schema.json'))
    r=build(packet)
    out.mkdir(parents=True,exist_ok=False)
    write_new(out/'synthesis_result.json',r)
    (out/'Synthesis_Report_DRAFT.md').write_text(markdown(r),encoding='utf-8')
    write_new(out/'input_manifest.json',{'input_path':str(inp),'input_sha256':__import__('hashlib').sha256(inp.read_bytes()).hexdigest(),'input_digest':digest(packet)})
    print('STAGED:',out,'\nAUDIT:',r['audit']['status'],'\nCLAIMS:',len(r['evidence_matrix']),'\nGAPS:',len(r['candidate_gaps']),'\nNO VAULT WRITES')
def main(argv=None):
    ap=argparse.ArgumentParser(description='PRKE Synthesize v1.5 - conservative scientific evidence staging')
    subs=ap.add_subparsers(dest='command',required=True)
    p=subs.add_parser('doctor');p.set_defaults(f=doctor)
    p=subs.add_parser('stage');p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.set_defaults(f=stage)
    args=ap.parse_args(argv)
    try:args.f(args);return 0
    except (ScienceError,OSError,KeyError,ValueError,ImportError) as e:print('ERROR:',str(e),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
