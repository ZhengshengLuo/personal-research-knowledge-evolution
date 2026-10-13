"""PRKE router local validation and task checkpoints.
Acquire, Understand and Organize are instruction-ready; actual host tools checked at runtime; this CLI
does no literature search, formal Vault commits, or authentication.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / 'schemas' / 'router'
ROUTES = ('acquire', 'understand', 'organize', 'synthesize')
FILES = ['SKILL.md', 'router/intake.md', 'router/workspace.md', 'router/planning.md',
         'router/dispatch.md', 'router/governance.md', 'router/checkpoints.md',
         'router/interfaces/module-contract.md', 'router/interfaces/module-registry.json',
         'tests/ROUTING_SCENARIOS.md']

class PRKEError(Exception): pass

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def js_module():
    try: import jsonschema
    except ImportError as e: raise PRKEError('请先安装依赖: python -m pip install -r requirements.txt') from e
    return jsonschema

def read(path):
    try: return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as e: raise PRKEError(f'无法读取 JSON: {path}: {e}') from e

def validate(name, data):
    f = SCHEMA_DIR / (name + '.schema.json')
    if not f.exists(): raise PRKEError('不存在的 schema: ' + name)
    js = js_module(); schema = read(f)
    js.Draft202012Validator.check_schema(schema)
    problems = list(js.Draft202012Validator(schema, format_checker=js.FormatChecker()).iter_errors(data))
    if problems:
        e=problems[0]; where='.'.join(str(p) for p in e.path)
        raise PRKEError(f'格式不合法: {where}: {e.message}（共{len(problems)}处）')
    if name == 'task_contract': guard(data)

def guard(task):
    p=task['permissions']
    if p['formal_commit'] or p['destructive']:
        raise PRKEError('Router MVP 禁止 P2/P3 正式知识库操作')
    if task['primary_route'] in task['support_routes']:
        raise PRKEError('主路由不能与辅助路由重复')
    if task['readiness'] == 'READY' and any('待澄清' in d for d in task['deliverables']):
        raise PRKEError('交付物尚待澄清，不可标 READY')
    if task['readiness'] == 'CLARIFYING' and task['task_state'] in ('RUNNING','COMPLETED'):
        raise PRKEError('任务尚未通过需求准入门槛')
    for key in ('search_calls','fulltext_papers','deep_search_calls'):
        limit = task['budget']['limits'][key]
        if limit is not None and task['budget']['usage'][key] > limit:
            raise PRKEError('超出硬预算: '+key)

def safe_folder(folder, protected=None):
    folder = Path(folder).expanduser().resolve()
    if protected:
        protected=Path(protected).expanduser().resolve()
        if folder==protected or protected in folder.parents:
            raise PRKEError('指定输出目录位于受保护目录内')
    if folder == Path(folder.anchor): raise PRKEError('不可在磁盘根目录写暂存任务')
    for parent in (folder, *folder.parents):
        if (parent/'.obsidian').exists() or (parent/'.research-kb').exists():
            raise PRKEError('检测到 Obsidian/PRKE 正式知识库，暂存必须在库外')
    return folder

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2);f.write('\n')

def doctor(_):
    missing = [p for p in FILES if not (ROOT/p).is_file()]
    skillfiles=[p for p in ROOT.rglob('*') if p.is_file() and p.name.lower()=='skill.md']
    if len(skillfiles)!=1: missing.append('需要恰好一个 SKILL.md')
    if not (ROOT/'SKILL.md').read_text(encoding='utf-8').startswith('---\nname: personal-research-knowledge-evolution\n'):
        missing.append('SKILL.md name/frontmatter 不正确')
    if not re.search(r'^description:\s*\S+', (ROOT/'SKILL.md').read_text(encoding='utf-8'), re.M):
        missing.append('缺少 description')
    for folder in ('router','routes','references','adapters','schemas','scripts','tests'):
        if not (ROOT/folder).is_dir(): missing.append('缺少统一结构目录: '+folder)
    registry=read(ROOT/'router/interfaces/module-registry.json')
    for route in ('acquire','understand','organize','synthesize'):
        entry=registry.get('modules',{}).get(route,{})
        path=ROOT/'routes'/(route+'.md')
        if entry.get('status')=='INSTRUCTION_READY':
            if entry.get('implementation_ref')!=f'routes/{route}.md' or not path.is_file():
                missing.append('模块声明就绪但缺协议: '+route)
        elif entry.get('status')=='NOT_CONNECTED':
            if path.exists() or entry.get('implementation_ref') is not None:
                missing.append('模块未接入但文件/引用存在: '+route)
        else: missing.append('未识别模块状态: '+route)
    if not (ROOT/'routes'/'acquire.md').is_file(): missing.append('Acquire 业务协议缺失')
    if missing: raise PRKEError('缺失或错误: '+', '.join(missing))
    names=[p.name[:-12] for p in SCHEMA_DIR.glob('*.schema.json')]
    for name in names:
        js_module().Draft202012Validator.check_schema(read(SCHEMA_DIR/(name+'.schema.json')))
    validate('task_contract',read(ROOT/'examples/task_contract.example.json'))
    reg=read(ROOT/'router/interfaces/module-registry.json')
    if sorted(reg.get('modules',{})) != sorted(ROUTES): raise PRKEError('模块注册表缺少四个标准路由')
    acq=reg['modules']['acquire']
    if acq.get('status')!='INSTRUCTION_READY' or acq.get('implementation_ref')!='routes/acquire.md':
        raise PRKEError('Acquire 指令模块尚未正确注册')
    if reg['modules']['understand'].get('status')!='INSTRUCTION_READY' or reg['modules']['understand'].get('implementation_ref')!='routes/understand.md':
        raise PRKEError('Understand 指令模块尚未正确注册')
    if reg['modules']['organize'].get('status')!='INSTRUCTION_READY' or reg['modules']['organize'].get('implementation_ref')!='routes/organize.md':
        raise PRKEError('Organize 尚未正确注册')
    if reg['modules']['synthesize'].get('status')!='INSTRUCTION_READY' or reg['modules']['synthesize'].get('implementation_ref')!='routes/synthesize.md':
        raise PRKEError('Synthesize 指令和科学综合证据工具尚未正确注册')
    print(f'PASS: {len(names)} Router Schemas、统一入口与模块注册有效；Acquire/Understand/Organize/Synthesize INSTRUCTION_READY (external and scientific live checks pending)')

def init_task(a):
    base=safe_folder(a.output_dir,a.protected_path)
    data=read(ROOT/'examples/task_contract.example.json')
    data['task_id']='task-'+uuid.uuid4().hex[:16]
    data['user_request']=a.objective
    data['objective']={'value':a.objective,'source':'USER_CONFIRMED'}
    data['deliverables']=a.deliverable or ['待澄清：预期交付物']
    data['scope']={'topic':{'value':a.objective,'source':'ASSUMED','rationale':'候选主题，不代表用户确认全部研究边界'},'inclusions':[],'exclusions':[]}
    data['primary_route']=a.route;data['support_routes']=[]
    data['readiness']='CLARIFYING';data['task_state']='CLARIFYING'
    data['open_questions']=['尚需确认成果及关键范围条件']
    data['workspace_links']=[];data['research_mode']='QUICK'
    data['planning']={'mission':a.objective,'stages':[],'current_stage':None}
    data['permissions']={'read':True,'staging_write':True,'formal_commit':False,'destructive':False,'external_transfer':False}
    data['budget']={'limits':{'search_calls':None,'fulltext_papers':None,'deep_search_calls':None,'wall_time_minutes':None},'usage':{'search_calls':0,'fulltext_papers':0,'deep_search_calls':0}}
    data['created_at']=now();data['updated_at']=now()
    validate('task_contract',data)
    folder=base/data['task_id'];(folder/'checkpoints').mkdir(parents=True,exist_ok=False)
    write_new(folder/'task_contract.json',data)
    print(f'CREATED: {folder / "task_contract.json"}\nSTATE: CLARIFYING; 无正式库写入')

def checkpoint(a):
    f=Path(a.task_file).expanduser().resolve()
    if f.name!='task_contract.json': raise PRKEError('只接受 task_contract.json')
    safe_folder(f.parent,a.protected_path)
    data=read(f);validate('task_contract',data)
    snapshot={'task_id':data['task_id'],'recorded_at':now(),'task_state':data['task_state'],
              'plan_revision':data['plan_revision'],'current_stage':data['planning']['current_stage'],
              'contract_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
              'budget_usage':data['budget']['usage'],'open_questions':data['open_questions'],
              'note':a.note or '', 'external_job_refs':[],
              'resume_hint':'恢复前核对合同、已有成果与异步任务，不重复提交'}
    name='ckpt-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
    out=f.parent/'checkpoints'/name;write_new(out,snapshot)
    print('CHECKPOINT:',out)

def run(argv=None):
    p=argparse.ArgumentParser(description='PRKE PRKE v1.5 Router: all 4 instruction routes ready; task CLI P2/P3 blocked, writing handled only by separately approved Organize/Knowledge commit')
    sub=p.add_subparsers(dest='op',required=True)
    a=sub.add_parser('doctor');a.set_defaults(fn=doctor)
    a=sub.add_parser('capabilities');a.set_defaults(fn=lambda x: print(json.dumps(read(ROOT/'router/interfaces/module-registry.json')['modules'], ensure_ascii=False, indent=2)))
    a=sub.add_parser('validate');a.add_argument('--schema',required=True,choices=sorted(p.name[:-12] for p in SCHEMA_DIR.glob('*.schema.json')));a.add_argument('--file',required=True)
    a.set_defaults(fn=lambda x: (validate(x.schema,read(x.file)),print('PASS:',x.schema,x.file)))
    a=sub.add_parser('init-task');a.add_argument('--output-dir',required=True);a.add_argument('--objective',required=True)
    a.add_argument('--route',choices=ROUTES,required=True);a.add_argument('--deliverable',action='append');a.add_argument('--protected-path');a.set_defaults(fn=init_task)
    a=sub.add_parser('checkpoint');a.add_argument('--task-file',required=True);a.add_argument('--note');a.add_argument('--protected-path');a.set_defaults(fn=checkpoint)
    args=p.parse_args(argv)
    try: args.fn(args);return 0
    except PRKEError as e: print('ERROR:',e,file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(run())
