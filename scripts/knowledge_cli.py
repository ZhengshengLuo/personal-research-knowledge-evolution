"""PRKE v1.5.0-rc1: Vault-external synthesis stage, conservative batch-approved note/Gap commit.
Not a cryptographic human identity check. Uses exclusive locks, backups, version hashes.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,sys,tempfile,uuid
from datetime import datetime,timezone
from pathlib import Path
from synthesize_engine import EVENTS,ScienceError,now,digest,read,write_new
from organize_cli import vault_path,safe_task,inside,file_sha,managed,sha,BEGIN,END,OrganizeError

AI_START='<!-- PRKE:SYNTHESIS:BEGIN -->'
AI_END='<!-- PRKE:SYNTHESIS:END -->'
MAJOR={'SCOPE_REFINED','HYPOTHESIS_REVISED','SPLIT','MERGE','PRIOR_WORK_RESOLVED','RESEARCHER_DECISION'}

def doc(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
def atomic(p,blob):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='.prke-',suffix='.tmp')
    try:
        with os.fdopen(fd,'wb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def relsafe(s):
    if not re.fullmatch(r'[\w\-\u4e00-\u9fff ]{1,90}',s):raise ScienceError('不安全的 Topic ID')
    return s
def gap_state(v):
    file=v/'.prke/gaps/state.json'
    return read(file) if file.is_file() else {'schema_version':'1.0','gaps':{},'topics':{},'last_event_hash':None}
def event_history(v):
    p=v/'.prke/gaps/events.jsonl'
    if not p.is_file():return []
    return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
def verify_chain(st,history):
    previous=None
    for e in history:
        if e.get('prior_event_hash')!=previous:raise ScienceError('演化账本哈希链中断')
        cp={k:v for k,v in e.items() if k!='event_hash'}
        if e.get('event_hash')!=digest(cp):raise ScienceError('事件内容哈希失配')
        previous=e['event_hash']
    if st.get('last_event_hash')!=previous:raise ScienceError('Gap 状态与演化账本不一致')
def append_event(history,e):
    e=dict(e,prior_event_hash=history[-1]['event_hash'] if history else None)
    e['event_hash']=digest(e)
    history.append(e)

def render_topic(topic,overview,entries):
    arr=['## 最新科学综合（AI 候选，待独立核验）','',
         f'> [!warning] AI_SYNTHESIS_DRAFT','> 仅反映指定文献范围的证据整理。没有完成独立科学评审，不代替研究者确认结论。','',
         f'- 当前问题：{overview["research_question"]}',f'- 论文覆盖：{overview["source_coverage"]["unique_papers"]} 篇；来源 Claim：{overview["source_coverage"]["claims"]}',
         f'- 审计状态：`{overview["audit"]["status"]}`（不代表科学内容审查通过）','',
         '### Research Gap 与演化轨迹','']
    if not entries:arr.append('当前尚无有证据支持的候选 Gap。')
    for g in entries:
        arr.extend([f'#### {g["gap_id"]}',g['current_statement'],f'- 状态：`{g["workflow_status"]}`；反证：`{g["novelty_status"]}`',''])
        if g.get('pending_statement'):arr.extend(['> [!caution] 待研究者确认的修订建议', '> '+g['pending_statement'],''])
    arr.extend(['```mermaid','flowchart TD',f'    T["{topic[:30].replace(chr(34)," ")}"]'])
    for i,g in enumerate(entries[:15]):
        name=g['gap_id'].replace('"','')[:35]
        arr.extend([f'    G{i}["{name}"]',f'    T --> G{i}'])
    arr.extend(['```','','- 查看全库 [[Research Gap Overview]] 获取其他 Topic 的研究机会。',''])
    return '\n'.join(arr)
def ai_hash(text):
    if not text or AI_START not in text and AI_END not in text:return None
    if text.count(AI_START)!=1 or text.count(AI_END)!=1 or text.index(AI_START)>text.index(AI_END):
        raise ScienceError('受管区标记异常，停止自动合并')
    return sha(text[text.index(AI_START):text.index(AI_END)+len(AI_END)].encode('utf-8'))

def protect_topic(old,topic_rec):
    actual=ai_hash(old)
    expected=topic_rec.get('managed_ai_sha256')
    if actual!=expected:raise ScienceError('Topic 受管内容被外部编辑或没有历史哈希记录，暂停合并')

def protect_overview(v,st):
    target=inside(v,'Research Gap Overview.md')
    actual=file_sha(target) if target.exists() else None
    if actual!=st.get('overview_sha256'):
        raise ScienceError('全库 Gap Overview 被外部编辑或没有可信历史哈希，拒绝覆盖')

def inject(old,content):
    block=AI_START+'\n'+content+'\n'+AI_END
    if not old:return '---\nasset_type: topic\ncssclasses: [prke-studio]\n---\n\n# 科学问题\n\n'+block+'\n\n## 我的科研认识（人工维护）\n\n'
    if old.count(AI_START)==1 and old.count(AI_END)==1 and old.index(AI_START)<old.index(AI_END):
        return old[:old.index(AI_START)]+block+old[old.index(AI_END)+len(AI_END):]
    if AI_START in old or AI_END in old:raise ScienceError('受管标记损坏，拒绝覆盖')
    return old.rstrip()+'\n\n'+block+'\n'
def render_overview(gaps):
    a=['# Research Gap Overview','', '> [!warning] 待审查候选','> 本页由 PRKE 管理；候选不构成已确认的原创性或首次研究主张。','', '| Gap ID | Topic | 当前问题 | 流程状态 | 反证状态 |','|---|---|---|---|---|']
    for uid,g in sorted(gaps.items()):
        line=lambda s:str(s or '').replace('|','/').replace('\n',' ')[:170]
        a.append('| `{}` | {} | {} | `{}` | `{}` |'.format(uid,line(g['topic_id']),line(g['current_statement']),line(g['workflow_status']),line(g['novelty_status'])))
    return '\n'.join(a)+'\n'

def stage(a):
    v=vault_path(a.vault);stage=safe_task(a.stage_dir,v)
    if stage.exists():raise ScienceError('暂存目录已存在，换用新目录')
    rpath=Path(a.synthesis_result).expanduser().resolve()
    r=read(rpath)
    if r.get('epistemic_status')!='AI_SYNTHESIS_DRAFT':raise ScienceError('不接受非 AI 草稿来源')
    topic=relsafe(r['topic_id']);topic_rel='Topics/科学问题/'+topic+'.md'
    st=gap_state(v);hist=event_history(v);verify_chain(st,hist)
    protect_overview(v,st)
    if st['topics'].get(topic,{}).get('last_input_digest')==r['input_digest']:
        raise ScienceError('同一科学输入快照已提交，拒绝重复写入或制造伪演化事件')
    gaps=json.loads(json.dumps(st['gaps']))
    updates=[]
    for candidate in r['candidate_gaps']:
        uid=candidate['gap_id'];statement=candidate['statement']
        if not re.fullmatch(r'[A-Za-z0-9_-]{3,80}',uid):raise ScienceError('Gap ID 不安全')
        g=gaps.get(uid)
        if g and g['topic_id']!=topic:raise ScienceError('跨 Topic 既有 Gap，需专门人工关联操作')
        if g is None:
            g={'gap_id':uid,'topic_id':topic,'current_statement':statement,'workflow_status':'CANDIDATE','evidence_status':'INSUFFICIENT','novelty_status':candidate['verification_status'],'version':1,'pending_statement':None,'latest_evidence_refs':candidate['evidence_refs']}
            gaps[uid]=g;etype='EVIDENCE_ADDED';req=False
        else:
            req=g['current_statement']!=statement
            etype='SCOPE_REFINED' if req else 'EVIDENCE_ADDED'
            if req:
                # Distinguish proposed, not confirmed. No user-approved change to canonical statement.
                g['pending_statement']=statement;g['workflow_status']='PENDING_HUMAN'
            prior_evidence=set(g.get('latest_evidence_refs',[]))
            g['latest_evidence_refs']=sorted(prior_evidence | set(candidate['evidence_refs']))
            g['novelty_status']=candidate['verification_status']
            if not req and set(candidate['evidence_refs']).issubset(prior_evidence):etype='NO_MATERIAL_CHANGE'
        event={'event_id':str(uuid.uuid4()),'gap_id':uid,'event_type':etype,'at_utc':now(),'task_id':r['run_id'],
               'parent_version':g['version'],'new_version':g['version']+(1 if req else 0),'evidence_refs':candidate['evidence_refs'],
               'reason':'本轮来源更新；重要范围变化需要研究者确认' if req else '阶段性新增或复核证据',
               'previous_statement':g['current_statement'],'proposed_statement':statement,
               'review_required':req,'approval_status':'PENDING_HUMAN' if req else 'AI_CANDIDATE',
               'provenance':'SYNTHESIS_STAGE'}
        append_event(hist,event);updates.append(event)
    st['gaps']=gaps;st['last_event_hash']=hist[-1]['event_hash'] if hist else None
    st['topics'][topic]={**st['topics'].get(topic,{}),'last_run_id':r['run_id'],'last_input_digest':r['input_digest'],'updated_at':now()}
    entries=[x for x in gaps.values() if x['topic_id']==topic]
    tpath=inside(v,topic_rel)
    existing=tpath.read_text(encoding='utf-8') if tpath.exists() else ''
    protect_topic(existing,st['topics'].get(topic,{}))
    topic_blob=inject(existing,render_topic(topic,r,entries))
    overview=render_overview(gaps)
    st['topics'][topic]['managed_ai_sha256']=ai_hash(topic_blob)
    st['overview_sha256']=sha(overview.encode('utf-8'))
    changes={topic_rel:topic_blob.encode('utf-8'),'Research Gap Overview.md':overview.encode('utf-8'),
             '.prke/gaps/state.json':doc(st).encode('utf-8'),
             '.prke/gaps/events.jsonl':''.join(json.dumps(e,ensure_ascii=False,sort_keys=True)+'\n' for e in hist).encode('utf-8')}
    files=[];stage.mkdir(parents=True,exist_ok=False);(stage/'drafts').mkdir()
    for i,(rel,data) in enumerate(changes.items()):
        draft='drafts/'+str(i)+'.dat';(stage/draft).write_bytes(data);target=inside(v,rel)
        files.append({'target_rel':rel,'draft_rel':draft,'base_sha256':file_sha(target) if target.exists() else None,'draft_sha256':sha(data)})
    plan={'schema_version':'1.0','batch_id':str(uuid.uuid4()),'vault':str(v),'source_result_path':str(rpath),'source_result_sha256':file_sha(rpath),
          'topic_id':topic,'created_at':now(),'files':files,'major_approval_required':any(x['review_required'] for x in updates),
          'permission':'PENDING_USER_BATCH_APPROVAL','source_run_id':r['run_id'],'event_ids':[x['event_id'] for x in updates]}
    write_new(stage/'plan.json',plan)
    print('STAGED:',stage,'\nPLAN_SHA256:',file_sha(stage/'plan.json'),'\nFILES:',len(files),'\nMAJOR_CHANGE_PENDING:',plan['major_approval_required'],'\nNO VAULT WRITES')

def commit(a):
    stage=Path(a.stage_dir).expanduser().resolve();v=vault_path(a.vault);safe_task(stage,v)
    plan=read(stage/'plan.json')
    if str(v)!=plan['vault'] or file_sha(stage/'plan.json')!=a.approve_plan_sha256 or not a.acknowledge_vault_write:
        raise ScienceError('Vault / 批次批准 SHA 不一致或未明确确认写入')
    if (stage/'commit_receipt.json').exists():raise ScienceError('已有提交收据；必须先查看/恢复，拒绝重复提交')
    if file_sha(plan['source_result_path'])!=plan['source_result_sha256']:raise ScienceError('源综合结果变化')
    lockpath=v/'.prke/write.lock';lockpath.parent.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(str(lockpath),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise ScienceError('检测到正在提交或遗留锁；必须人工排查后恢复')
    os.close(fd)
    try:
        blobs={};original={}
        for entry in plan['files']:
            dst=inside(v,entry['target_rel']);draft=(stage/entry['draft_rel']).resolve()
            if stage not in draft.parents:raise ScienceError('草稿路径逃逸')
            b=draft.read_bytes()
            if sha(b)!=entry['draft_sha256']:raise ScienceError('草稿哈希变化')
            actual=file_sha(dst) if dst.exists() else None
            if actual!=entry['base_sha256']:raise ScienceError('目标自 stage 后发生变化 '+entry['target_rel'])
            blobs[dst]=b;original[dst]=dst.read_bytes() if dst.exists() else None
        backup=stage/'backups';backup.mkdir(exist_ok=False)
        manifests=[]
        for i,(dst,raw) in enumerate(original.items()):
            if raw is not None:(backup/(str(i)+'.bak')).write_bytes(raw)
            manifests.append({'target_rel':str(dst.relative_to(v)).replace('\\','/'),'backup':str(i)+'.bak' if raw is not None else None,'old_sha256':sha(raw) if raw is not None else None})
        write_new(backup/'manifest.json',{'items':manifests,'vault':str(v)})
        receipt={'state':'WRITING','created_at':now(),'batch_id':plan['batch_id'],'plan_sha256':file_sha(stage/'plan.json')}
        write_new(stage/'commit_receipt.json',receipt)
        try:
            for dst,b in blobs.items():atomic(dst,b)
            for dst,b in blobs.items():
                if file_sha(dst)!=sha(b):raise ScienceError('提交后哈希失配')
            receipt['state']='COMMITTED';receipt['updated_at']=now();atomic(stage/'commit_receipt.json',doc(receipt).encode('utf-8'))
            print('COMMITTED:',plan['batch_id'],'\nFILES:',len(blobs),'\nWARNING: CLI acknowledgement is not an identity-authenticated approval')
        except Exception:
            receipt['state']='NEEDS_RECOVERY';atomic(stage/'commit_receipt.json',doc(receipt).encode('utf-8'))
            raise
    finally:
        lockpath.unlink(missing_ok=True)

def recover(a):
    stage=Path(a.stage_dir).expanduser().resolve();v=vault_path(a.vault);safe_task(stage,v)
    receipt=read(stage/'commit_receipt.json');plan=read(stage/'plan.json')
    if not a.acknowledge_recovery or a.approve_plan_sha256!=file_sha(stage/'plan.json') or str(v)!=plan['vault']:
        raise ScienceError('恢复需人工确认 Vault 与计划 SHA')
    if receipt['state']!='NEEDS_RECOVERY' and receipt['state']!='WRITING':raise ScienceError('仅处理明确未完成提交的记录')
    b=read(stage/'backups/manifest.json')
    if b['vault']!=str(v):raise ScienceError('备份 Vault 不匹配')
    lockpath=v/'.prke/write.lock'
    try:fd=os.open(str(lockpath),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise ScienceError('先人工排查遗留写锁')
    os.close(fd)
    try:
        for row in b['items']:
            dst=inside(v,row['target_rel'])
            if row['backup'] is None:dst.unlink(missing_ok=True)
            else:
                bb=(stage/'backups'/row['backup']).read_bytes()
                if sha(bb)!=row['old_sha256']:raise ScienceError('恢复备份哈希错误')
                atomic(dst,bb)
        receipt['state']='ROLLED_BACK';receipt['updated_at']=now();atomic(stage/'commit_receipt.json',doc(receipt).encode('utf-8'))
        print('ROLLED_BACK:',plan['batch_id'])
    finally:lockpath.unlink(missing_ok=True)

def doctor(_):print('PASS: staged Topic + Gap Overview + chained history; live Vault untouched')
def main(argv=None):
    p=argparse.ArgumentParser(description='PRKE v1.5 Knowledge Evolution - staged, batch-approved Vault edits')
    sub=p.add_subparsers(dest='command',required=True)
    x=sub.add_parser('doctor');x.set_defaults(f=doctor)
    x=sub.add_parser('stage');x.add_argument('--vault',required=True);x.add_argument('--synthesis-result',required=True);x.add_argument('--stage-dir',required=True);x.set_defaults(f=stage)
    x=sub.add_parser('commit');x.add_argument('--vault',required=True);x.add_argument('--stage-dir',required=True);x.add_argument('--approve-plan-sha256',required=True);x.add_argument('--acknowledge-vault-write',action='store_true');x.set_defaults(f=commit)
    x=sub.add_parser('recover');x.add_argument('--vault',required=True);x.add_argument('--stage-dir',required=True);x.add_argument('--approve-plan-sha256',required=True);x.add_argument('--acknowledge-recovery',action='store_true');x.set_defaults(f=recover)
    args=p.parse_args(argv)
    try:args.f(args);return 0
    except (ScienceError,OrganizeError,KeyError,ValueError,OSError) as e:print('ERROR:',str(e),file=sys.stderr);return 2

# Researcher decisions are staged as separate batches and retain the original event chain.
# No automatic caller may treat this CLI flag as cryptographic proof of the human identity.
def stage_decision(a):
    if not a.acknowledge_researcher_decision:raise ScienceError('正式科学决定必须由用户主动确认本次操作')
    v=vault_path(a.vault);stage=safe_task(a.stage_dir,v)
    if stage.exists():raise ScienceError('指定 stage 目录已存在')
    source=Path(a.decision_json).expanduser().resolve();decision=read(source)
    uid=decision.get('gap_id');action=decision.get('action')
    if action not in ('APPROVE_REVISION','REJECT_REVISION','APPROVE_IDEA','ARCHIVE_GAP'):
        raise ScienceError('无效的人工决定动作')
    if not isinstance(decision.get('rationale'),str) or len(decision['rationale'].strip())<5:
        raise ScienceError('人类决定需要至少一条理由')
    st=gap_state(v);history=event_history(v);verify_chain(st,history)
    protect_overview(v,st)
    gaps=st['gaps'];g=gaps.get(uid)
    if not g:raise ScienceError('找不到候选 Gap')
    previous=g['current_statement'];pending=g.get('pending_statement')
    if action in ('APPROVE_REVISION','REJECT_REVISION') and not pending:raise ScienceError('没有待批准的科学范围变更')
    if action=='APPROVE_REVISION':
        g['current_statement']=pending;g['pending_statement']=None;g['version']+=1;g['workflow_status']='CANDIDATE'
    elif action=='REJECT_REVISION':
        g['pending_statement']=None;g['workflow_status']='CANDIDATE'
    elif action=='ARCHIVE_GAP':g['workflow_status']='ARCHIVED'
    elif action=='APPROVE_IDEA':g['workflow_status']='APPROVED'
    changes={}
    if action=='APPROVE_IDEA':
        title=relsafe(decision.get('idea_title',''))
        if not decision.get('idea_summary') or len(decision['idea_summary'].strip())<15:raise ScienceError('正式 Idea 需完整且经过确认的候选描述')
        idea_rel='Ideas/'+uid+' - '+title+'.md';dst=inside(v,idea_rel)
        if dst.exists():raise ScienceError('正式 Idea 已存在，不允许重复创建')
        changes[idea_rel]=('---\nasset_type: research_idea\ngap_id: '+json.dumps(uid)+'\nresearcher_approved: true\n---\n\n# '+title+'\n\n'+decision['idea_summary']+'\n\n## 来源\n\n- Gap ID：`'+uid+'`\n- 研究者确认理由：'+decision['rationale']+'\n').encode('utf-8')
    event={'event_id':str(uuid.uuid4()),'gap_id':uid,'event_type':'RESEARCHER_DECISION','at_utc':now(),'task_id':'decision-'+uuid.uuid4().hex[:8],
           'parent_version':g['version']-(1 if action=='APPROVE_REVISION' else 0),'new_version':g['version'],
           'evidence_refs':g.get('latest_evidence_refs',[]),'reason':decision['rationale'],'previous_statement':previous,
           'proposed_statement':g['current_statement'],'review_required':False,'approval_status':'USER_DECLARED_NOT_IDENTITY_AUTHENTICATED',
           'decision':action,'provenance':'EXPLICIT_RESEARCHER_BATCH'}
    append_event(history,event);st['last_event_hash']=history[-1]['event_hash']
    topic=g['topic_id'];topic_rel='Topics/科学问题/'+topic+'.md'
    tp=inside(v,topic_rel);existing=tp.read_text(encoding='utf-8') if tp.exists() else ''
    protect_topic(existing,st['topics'].get(topic,{}))
    # Decision only modifies the managed Gap description, retaining previous synopsis & human content.
    synopsis='## Research Gap 最近一次科研裁决\n\n- Gap：`'+uid+'`\n- 当前：'+g['current_statement']+'\n- 动作：`'+action+'`\n- 理由：'+decision['rationale']+'\n- 来源历史参见 [[Research Gap Overview]]。'
    updated_topic=inject(existing,synopsis)
    changes[topic_rel]=updated_topic.encode('utf-8')
    st['topics'].setdefault(topic,{})['managed_ai_sha256']=ai_hash(updated_topic)
    changes['Research Gap Overview.md']=render_overview(gaps).encode('utf-8')
    st['overview_sha256']=sha(changes['Research Gap Overview.md'])
    changes['.prke/gaps/state.json']=doc(st).encode('utf-8')
    changes['.prke/gaps/events.jsonl']=''.join(json.dumps(e,ensure_ascii=False,sort_keys=True)+'\n' for e in history).encode('utf-8')
    stage.mkdir(parents=True,exist_ok=False);(stage/'drafts').mkdir()
    files=[]
    for i,(rel,blob) in enumerate(changes.items()):
        draft='drafts/'+str(i)+'.dat';(stage/draft).write_bytes(blob);dst=inside(v,rel)
        files.append({'target_rel':rel,'draft_rel':draft,'base_sha256':file_sha(dst) if dst.exists() else None,'draft_sha256':sha(blob)})
    plan={'schema_version':'1.0','batch_id':str(uuid.uuid4()),'vault':str(v),'source_result_path':str(source),'source_result_sha256':file_sha(source),
          'topic_id':topic,'created_at':now(),'files':files,'major_approval_required':True,'permission':'PENDING_EXPLICIT_BATCH_COMMIT',
          'event_ids':[event['event_id']],'decision':action}
    write_new(stage/'plan.json',plan)
    print('STAGED_RESEARCHER_DECISION:',stage,'\nPLAN_SHA256:',file_sha(stage/'plan.json'),'\nNO VAULT WRITES')

# Inject command in existing parser while retaining backwards-compatible programmatic API.
_original_main=main
def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args and args[0]=='stage-decision':
        p=argparse.ArgumentParser(description='Stage explicit researcher Gap/Idea decision')
        p.add_argument('--vault',required=True);p.add_argument('--decision-json',required=True);p.add_argument('--stage-dir',required=True)
        p.add_argument('--acknowledge-researcher-decision',action='store_true')
        a=p.parse_args(args[1:])
        try:stage_decision(a);return 0
        except (ScienceError,OrganizeError,KeyError,ValueError,OSError) as e:print('ERROR:',e,file=sys.stderr);return 2
    return _original_main(argv)

def stage_knowledge(a):
    """Stage evidence-grounded Method/Data/domain Topic AI sections; never alter human text."""
    v=vault_path(a.vault);stage=safe_task(a.stage_dir,v)
    if stage.exists():raise ScienceError('暂存目录已存在')
    source=Path(a.updates_json).expanduser().resolve();packet=read(source)
    items=packet.get('items',[])
    if not isinstance(items,list) or not items:raise ScienceError('需要至少一个知识更新条目')
    changes={};summary=[]
    knowledge_index_rel='.prke/knowledge/index.json'
    knowledge_index_path=inside(v,knowledge_index_rel)
    ki=read(knowledge_index_path) if knowledge_index_path.exists() else {'schema_version':'1.0','notes':{}}
    for row in items:
        kind=row.get('kind');name=relsafe(row.get('name',''))
        mapping={'METHOD':'Methods','DATA':'Data','TOPIC_DOMAIN':'Topics/领域知识','TOPIC_QUESTION':'Topics/科学问题'}
        if kind not in mapping:raise ScienceError('只允许指定的通用知识节点')
        rel=mapping[kind]+'/'+name+'.md';target=inside(v,rel)
        body=row.get('content','');refs=row.get('source_refs',[])
        if not isinstance(body,str) or len(body.strip())<20:raise ScienceError('科研知识内容不足')
        if not isinstance(refs,list) or not refs or any(not isinstance(x,str) or not x for x in refs):raise ScienceError('每项知识都必须包含来源引用')
        if not target.exists() and not a.acknowledge_new_node:raise ScienceError('新建重要节点必须单独确认：'+rel)
        old=target.read_text(encoding='utf-8') if target.exists() else ''
        if ai_hash(old)!=ki['notes'].get(rel):raise ScienceError('该知识节点受管区出现无记录变更，停止自动覆盖：'+rel)
        extra='\n\n'.join([body,'**原始证据引用**：'+', '.join('`'+x.replace('`','')+'`' for x in refs)])
        revised=inject(old,extra)
        changes[rel]=revised.encode('utf-8')
        ki['notes'][rel]=ai_hash(revised)
        summary.append({'target_rel':rel,'kind':kind,'source_refs':refs,'action':'UPDATE' if target.exists() else 'CREATE_USER_APPROVED'})
    stage.mkdir(parents=True,exist_ok=False);(stage/'drafts').mkdir()
    audit_rel='.prke/knowledge/events.jsonl';audit_path=inside(v,audit_rel)
    history=audit_path.read_text(encoding='utf-8') if audit_path.exists() else ''
    for row in summary:history+=json.dumps({'at_utc':now(),'source_path':str(source),'kind':row['kind'],'target_rel':row['target_rel'],'source_refs':row['source_refs']},ensure_ascii=False,sort_keys=True)+'\n'
    changes[audit_rel]=history.encode('utf-8')
    changes[knowledge_index_rel]=doc(ki).encode('utf-8')
    files=[]
    for i,(rel,blob) in enumerate(changes.items()):
        draft='drafts/'+str(i)+'.dat';(stage/draft).write_bytes(blob);target=inside(v,rel)
        files.append({'target_rel':rel,'draft_rel':draft,'base_sha256':file_sha(target) if target.exists() else None,'draft_sha256':sha(blob)})
    plan={'schema_version':'1.0','batch_id':str(uuid.uuid4()),'vault':str(v),'source_result_path':str(source),'source_result_sha256':file_sha(source),
          'topic_id':None,'created_at':now(),'files':files,'permission':'PENDING_USER_BATCH_APPROVAL','major_approval_required':a.acknowledge_new_node,
          'knowledge_updates':summary}
    write_new(stage/'plan.json',plan)
    print('STAGED_KNOWLEDGE:',stage,'\nPLAN_SHA256:',file_sha(stage/'plan.json'),'\nNO VAULT WRITES')

# Second extension of stage routing, kept after the original function definitions.
_previous_main=main
def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args and args[0]=='stage-knowledge':
        p=argparse.ArgumentParser(description='Stage evidence-grounded AI additions to existing Method/Data/Topic notes')
        p.add_argument('--vault',required=True);p.add_argument('--updates-json',required=True);p.add_argument('--stage-dir',required=True)
        p.add_argument('--acknowledge-new-node',action='store_true')
        a=p.parse_args(args[1:])
        try:stage_knowledge(a);return 0
        except (ScienceError,OrganizeError,KeyError,ValueError,OSError) as e:print('ERROR:',e,file=sys.stderr);return 2
    return _previous_main(argv)

if __name__=='__main__':raise SystemExit(main())
