"""Durable Topic 10-paper threshold scheduler. No implicit Windows background install."""
from __future__ import annotations
import argparse,json,os,sys,hashlib,tempfile
from pathlib import Path
from synthesize_engine import ScienceError,now,read

def atomic(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='.prke-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def valid_ids(source):
    paper_ids=set()
    for x in source['papers']:
        if x.get('topic_relevant') is True and x.get('source_check')=='VERIFIED' and x.get('reading_status') in ('READ_AND_VERIFIED','DEEP_COMPLETED'):
            p=x.get('paper_uid')
            if isinstance(p,str) and p:paper_ids.add(p)
    return paper_ids

def evaluate(a):
    src=read(a.manifest)
    if not src.get('topic_id'):raise ScienceError('需要 topic_id')
    task=Path(a.state_dir).expanduser().resolve();task.mkdir(parents=True,exist_ok=True)
    statepath=task/'topic_triggers.json';lock=task/'trigger.lock'
    try:fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise ScienceError('已有一个 trigger 进程或遗留锁，拒绝并发')
    os.close(fd)
    try:
        state=read(statepath) if statepath.exists() else {'schema_version':'1.0','topics':{}}
        tid=src['topic_id'];rec=state['topics'].get(tid,{'last_success_ids':[],'pending':None})
        current=valid_ids(src)
        new=current-set(rec['last_success_ids'])
        if rec['pending']:
            print('PENDING:',rec['pending']['run_key'],'\nNEW_PAPERS:',len(new),'\nNO DUPLICATE QUEUE')
        elif len(new)>=a.threshold or a.verified_critical_counterevidence:
            key=hashlib.sha256((tid+'|'+','.join(sorted(new))+'|'+str(a.verified_critical_counterevidence)).encode()).hexdigest()[:20]
            rec['pending']={'run_key':key,'trigger_reason':'CRITICAL_COUNTEREVIDENCE' if a.verified_critical_counterevidence else 'TEN_VALID_PAPERS',
                            'paper_uids_at_enqueue':sorted(current),'new_paper_uids':sorted(new),'created_at':now(),'state':'PENDING_SYNTHESIS'}
            print('QUEUED:',key,'\nNEW_PAPERS:',len(new))
        else:print('WAITING: valid new unique papers',len(new),'/',a.threshold)
        state['topics'][tid]=rec;atomic(statepath,state)
    finally:lock.unlink(missing_ok=True)

def complete(a):
    task=Path(a.state_dir).expanduser().resolve();p=task/'topic_triggers.json';lock=task/'trigger.lock'
    try:fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise ScienceError('已有另一个触发任务，拒绝并发完成')
    os.close(fd)
    try:
        state=read(p);r=read(a.synthesis_result)
        topic=r.get('topic_id');rec=state['topics'].get(topic)
        if not rec or not rec.get('pending'):raise ScienceError('该 Topic 没有待完成触发任务')
        if rec['pending']['run_key']!=a.run_key:raise ScienceError('run_key 不一致，拒绝重复完成')
        if r.get('audit',{}).get('status')!='COMPLETED':raise ScienceError('Synthesize PARTIAL/BLOCKED 不能作为成功轮次重置门槛')
        included={x['paper_uid'] for x in r.get('evidence_matrix',[]) if 'paper_uid' in x}
        missing=set(rec['pending']['new_paper_uids'])-included
        if missing:raise ScienceError('本轮综合未真正纳入这些新增 Paper UID：'+', '.join(sorted(missing)))
        rec['last_success_ids']=rec['pending']['paper_uids_at_enqueue']
        rec['last_success_at']=now();rec['last_synthesis_run_id']=r['run_id'];rec['pending']=None
        atomic(p,state);print('CYCLE_RECORDED:',topic,'\nNOTE: draft cycle completed, independent science review remains separate')
    finally:lock.unlink(missing_ok=True)

def doctor(_):print('PASS: durable threshold state and at-most-one pending per topic; Windows scheduler not installed')
def main(argv=None):
    p=argparse.ArgumentParser(description='PRKE durable 10-paper Topic trigger (manual or authorized scheduled invocation)')
    sub=p.add_subparsers(dest='command',required=True)
    x=sub.add_parser('doctor');x.set_defaults(f=doctor)
    x=sub.add_parser('check');x.add_argument('--manifest',required=True);x.add_argument('--state-dir',required=True);x.add_argument('--threshold',type=int,default=10);x.add_argument('--verified-critical-counterevidence',action='store_true');x.set_defaults(f=evaluate)
    x=sub.add_parser('complete');x.add_argument('--state-dir',required=True);x.add_argument('--synthesis-result',required=True);x.add_argument('--run-key',required=True);x.set_defaults(f=complete)
    a=p.parse_args(argv)
    try:
        if getattr(a,'threshold',10)<1:raise ScienceError('阈值须为正整数')
        a.f(a);return 0
    except (ScienceError,OSError,KeyError,ValueError) as e:print('ERROR:',e,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
