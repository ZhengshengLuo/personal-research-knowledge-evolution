"""PRKE host handoff and deterministic receipt ledger (no provider SDK / no auth).

This tool NEVER invokes a claimed external scientific provider. Host Agents execute
using their real tools and hand back output. All host statements stay HOST_REPORTED;
only local artifact byte integrity can be checked deterministically.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, tempfile, uuid, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'router/interfaces/capability-registry.json'
TERMINAL={'HOST_REPORTED_SUCCESS','HOST_REPORTED_FAILURE','BLOCKED','UNKNOWN_OUTCOME'}
SAFE_ID=re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$')
class ExecutionError(ValueError):pass

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def digest(data):return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for blob in iter(lambda:f.read(1024*1024),b''):h.update(blob)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def atomic_new(path,obj):
    """Exclusive JSON creation without os.link (Windows-safe).

    O_EXCL prevents overwrites; this is not a cross-file transaction or an
    unforgeable receipt. A process killed during writing may leave an incomplete
    file, so callers validate JSON on inspection and never infer success from
    mere path existence.
    """
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(str(p),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(obj,f,ensure_ascii=False,sort_keys=True,indent=2)
            f.write('\n');f.flush();os.fsync(f.fileno())
    except BaseException:
        p.unlink(missing_ok=True)
        raise

def receipt_digest(data):
    """Detect accidental receipt edits, NOT a digital signature/authentication."""
    return digest({k:v for k,v in data.items() if k!='receipt_digest'})

def safe_workspace(base):
    p=Path(base).expanduser().resolve()
    if p==Path(p.anchor):raise ExecutionError('工作区不可使用磁盘根目录')
    for candidate in (p,*p.parents):
        if (candidate/'.obsidian').exists() or (candidate/'.research-kb').exists():raise ExecutionError('工作区必须位于正式 Vault 外')
    return p

def capabilities():
    reg=read(REGISTRY)
    names=[x['capability_id'] for x in reg['capabilities']]
    if len(names)!=len(set(names)):raise ExecutionError('重复 capability_id')
    return reg

def prepare(a):
    reg=capabilities(); item=next((x for x in reg['capabilities'] if x['capability_id']==a.capability),None)
    if not item:raise ExecutionError('未注册的实际能力：'+a.capability)
    if not SAFE_ID.fullmatch(a.task_id):raise ExecutionError('非法 task_id')
    workspace=safe_workspace(a.workspace)
    packet=read(a.input)
    if not isinstance(packet,dict) or not packet:raise ExecutionError('工具输入必须为非空 JSON 对象')
    if a.requested_permission not in ('P0','P1'):raise ExecutionError('Host Handoff 仅允许 P0/P1；正式写入必须经过独立授权')
    if a.requested_permission not in item['allowed_permissions']:raise ExecutionError('该能力不允许请求的权限')
    uid=a.action_id or 'action-'+uuid.uuid4().hex[:16]
    if not SAFE_ID.fullmatch(uid):raise ExecutionError('非法 action_id')
    action=workspace/'actions'/uid
    if action.exists():raise ExecutionError('action 已存在，必须先 inspect，不得重复启动')
    if a.provider and a.provider not in item['providers']:raise ExecutionError('provider 未在此能力的允许清单内')
    doc={'schema_version':'1.0','task_id':a.task_id,'action_id':uid,'capability_id':a.capability,
         'requested_provider':a.provider,'requested_permission':a.requested_permission,
         'input_digest':digest(packet),'inputs':packet,'status':'AWAITING_HOST_EXECUTION',
         'created_at':now(),'executor_provenance':'PRKE_REQUEST_ONLY',
         'note':'准备调用的记录并非实际工具调用；不得声称已执行。'}
    # Prepare a complete request outside its public action path.  A failure
    # before publication leaves no broken action ID; an existing action is
    # never overwritten.  The final same-parent directory rename is atomic on
    # ordinary local filesystems, not a distributed transactional guarantee.
    actions=workspace/'actions';actions.mkdir(parents=True,exist_ok=True)
    staging=actions/('.prepare-'+uid+'-'+uuid.uuid4().hex)
    staging.mkdir(exist_ok=False)
    try:
        atomic_new(staging/'request.json',doc)
        if action.exists():raise ExecutionError('action 已存在，不能覆盖')
        os.rename(staging,action)
    finally:
        if staging.exists():shutil.rmtree(staging)
    print(json.dumps({'status':'AWAITING_HOST_EXECUTION','action_id':uid,'request':str(action/'request.json'),
                       'next':'宿主必须真实调用工具，然后提供 host-result.json 并执行 finalize'},ensure_ascii=False))

def finalize(a):
    workspace=safe_workspace(a.workspace)
    if not SAFE_ID.fullmatch(a.action_id):raise ExecutionError('非法 action_id')
    action=workspace/'actions'/a.action_id
    req=read(action/'request.json')
    if (action/'receipt.json').exists():raise ExecutionError('已有最终回执，不能覆盖；请 inspect')
    result=read(a.result)
    if result.get('schema_version')!='1.0' or result.get('action_id')!=a.action_id:raise ExecutionError('结果与请求身份不匹配')
    if result.get('status') not in TERMINAL:raise ExecutionError('不接受不存在或过度宣称的执行状态')
    cap=next(x for x in capabilities()['capabilities'] if x['capability_id']==req['capability_id'])
    provider=result.get('provider')
    if provider not in cap['providers']:raise ExecutionError('真实 provider 不在允许清单')
    if req['requested_provider'] and provider!=req['requested_provider']:raise ExecutionError('provider 与申请不一致')
    output=result.get('output',{})
    if not isinstance(output,dict):raise ExecutionError('output 必须为对象')
    files=[]
    for name in result.get('artifacts',[]):
        path=Path(name).expanduser().resolve()
        if not path.is_file():raise ExecutionError('回执引用的产物不存在：'+str(path))
        if path.stat().st_size>500*1024*1024:raise ExecutionError('产物超出默认 500 MB 审计上限')
        files.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size})
    if result['status']=='HOST_REPORTED_SUCCESS' and not result.get('provider_result_ref') and not files:
        raise ExecutionError('声称成功必须提供可核对的 provider_result_ref 或实际产物')
    provenance=result.get('source_provenance',[])
    if (not isinstance(provenance,list) or
        any(not isinstance(x,(str,dict)) for x in provenance)):
        raise ExecutionError('source_provenance 必须是列表，元素为来源字符串或对象')
    receipt={'schema_version':'1.0','action_id':a.action_id,'task_id':req['task_id'],
        'capability_id':req['capability_id'],'provider':provider,'input_digest':req['input_digest'],
        'result_digest':digest(output),'status':result['status'],'artifacts':files,
        'provider_result_ref':result.get('provider_result_ref'),
        'source_provenance':provenance, 'finished_at':now(),
        'execution_assurance':'HOST_REPORTED_UNVERIFIED',
        'local_artifact_integrity':'CHECKED' if files else 'NOT_AVAILABLE',
        'scientific_verification':'NOT_ASSESSED',
        'warning':'宿主结果由调用方报告，非不可伪造证明；产物 SHA 仅核验本地字节。'}
    receipt['receipt_digest']=receipt_digest(receipt)
    atomic_new(action/'receipt.json',receipt)
    print(json.dumps({'action_id':a.action_id,'status':receipt['status'],'execution_assurance':receipt['execution_assurance'],
                      'artifact_integrity':receipt['local_artifact_integrity'],'receipt':str(action/'receipt.json')},ensure_ascii=False))

def inspect(a):
    workspace=safe_workspace(a.workspace)
    if not SAFE_ID.fullmatch(a.action_id):raise ExecutionError('非法 action_id')
    action=workspace/'actions'/a.action_id
    p=action/'receipt.json'
    if not p.exists():
        doc=read(action/'request.json');print(json.dumps({'action_id':a.action_id,'status':doc['status'],
          'instruction':'检查宿主外部 job 后再 finalize；不要盲目重试有副作用的动作'},ensure_ascii=False));return
    r=read(p)
    bad=[f['path'] for f in r['artifacts'] if not Path(f['path']).is_file() or sha(f['path'])!=f['sha256']]
    stored_digest=r.get('receipt_digest')
    receipt_check='LOCAL_DIGEST_MATCH' if stored_digest and stored_digest==receipt_digest(r) else 'MISMATCH_OR_LEGACY'
    print(json.dumps({'action_id':a.action_id,'status':r['status'],'execution_assurance':r['execution_assurance'],
       'artifact_integrity':'MISMATCH' if bad else r['local_artifact_integrity'],'bad_artifacts':bad,
       'receipt_integrity':receipt_check,'receipt_authentication':'NOT_AUTHENTICATED',
       'scientific_verification':r['scientific_verification']},ensure_ascii=False))

def main(argv=None):
    p=argparse.ArgumentParser(description='PRKE host handoff ledger: P0/P1 only; never executes the provider itself')
    sub=p.add_subparsers(dest='command',required=True)
    x=sub.add_parser('capabilities');x.set_defaults(func=lambda _:print(json.dumps(capabilities(),ensure_ascii=False,indent=2)))
    x=sub.add_parser('doctor');x.set_defaults(func=lambda _: (capabilities(),print('PASS: registry parsed; provider execution NOT tested')))
    x=sub.add_parser('prepare');x.add_argument('--workspace',required=True);x.add_argument('--task-id',required=True);x.add_argument('--capability',required=True)
    x.add_argument('--provider');x.add_argument('--input',required=True);x.add_argument('--requested-permission',default='P0');x.add_argument('--action-id');x.set_defaults(func=prepare)
    x=sub.add_parser('finalize');x.add_argument('--workspace',required=True);x.add_argument('--action-id',required=True);x.add_argument('--result',required=True);x.set_defaults(func=finalize)
    x=sub.add_parser('inspect');x.add_argument('--workspace',required=True);x.add_argument('--action-id',required=True);x.set_defaults(func=inspect)
    try:a=p.parse_args(argv);a.func(a);return 0
    except (ExecutionError,OSError,KeyError,ValueError,TypeError) as e:print('ERROR:',e,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
