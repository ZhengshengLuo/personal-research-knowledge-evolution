"""Honest wall-clock 24h local soak harness. Never simulates completion."""
from __future__ import annotations
import argparse,json,os,sys,time,uuid
from datetime import datetime,timezone
from pathlib import Path

def save(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def run(a):
    root=Path(a.output).expanduser().resolve()
    if root.exists():raise ValueError('不覆盖已有 soak 记录')
    root.mkdir(parents=True,exist_ok=False)
    start=time.time();run_id='soak-'+uuid.uuid4().hex[:12]
    save(root/'config.json',{'run_id':run_id,'hours_requested':a.hours,'started_utc':now(),'start_unix':start,'hostname':os.getenv('COMPUTERNAME','UNKNOWN'),
                             'goal':'wall clock test; science and security tests remain independent'})
    with (root/'heartbeats.jsonl').open('x',encoding='utf-8') as f:
        while True:
            e={'unix':time.time(),'utc':now(),'pid':os.getpid(),'sequence':int((time.time()-start)//a.interval_seconds)}
            f.write(json.dumps(e)+'\n');f.flush();os.fsync(f.fileno())
            if time.time()-start >= a.hours*3600:break
            time.sleep(min(a.interval_seconds,max(0.01,start+a.hours*3600-time.time())))
    print('FINISHED_WALL_CLOCK:',root)
def verify(a):
    root=Path(a.output).expanduser().resolve();config=json.loads((root/'config.json').read_text(encoding='utf-8'))
    heartbeats=[json.loads(x) for x in (root/'heartbeats.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    if len(heartbeats)<2:raise ValueError('有效心跳太少')
    elapsed=heartbeats[-1]['unix']-config['start_unix']
    min_seconds=24*3600
    if elapsed<min_seconds:
        print(f'NOT_RUN_24H: {elapsed:.1f}s / {min_seconds}s; hearts={len(heartbeats)}');return 2
    if any(heartbeats[i]['unix']<heartbeats[i-1]['unix'] for i in range(1,len(heartbeats))):raise ValueError('心跳时间倒序')
    print(f'WALL_CLOCK_24H_COMPLETED: elapsed={elapsed:.1f}s; heartbeats={len(heartbeats)}; 仍须单独审查任务恢复与断点验证日志')
def main(argv=None):
    p=argparse.ArgumentParser(description='PRKE 24-hour honest elapsed-time harness: not a scheduler installer')
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('run');a.add_argument('--output',required=True);a.add_argument('--hours',type=float,default=24);a.add_argument('--interval-seconds',type=int,default=300);a.set_defaults(f=run)
    a=sub.add_parser('verify');a.add_argument('--output',required=True);a.set_defaults(f=verify)
    x=p.parse_args(argv)
    try:
        if getattr(x,'hours',24)<24:raise ValueError('正式 24h 验收必须要求至少真实 24 小时')
        if getattr(x,'interval_seconds',1)<1:raise ValueError('心跳间隔必须>0')
        code=x.f(x);return code if isinstance(code,int) else 0
    except (ValueError,OSError,KeyError) as e:print('ERROR:',e,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
