"""Evidence-grounded, candidate-only Claim/Relation packet validation.

No embedding similarity can confirm a scientific relationship. This module checks
provenance and comparability *declarations*, not truth of the underlying science.
Writes only to an external task directory (no Vault mutations).
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from execution_core import safe_workspace, atomic_new, digest

class SemanticsError(ValueError):pass
TYPES={'SUPPORTS','CHALLENGES','REFINES','ADDRESSES','USES_METHOD','USES_DATA','SHARES_EVIDENCE','RELATED_TO'}
STUDY_REL={'SUPPORTS','CHALLENGES','REFINES'}
ACCESS={'METADATA_ONLY','ABSTRACT_READ','FULLTEXT_ACCESSED','INTERNAL_EXPERIMENT'}
EVIDENCE_KIND={'FULLTEXT_TEXT','FULLTEXT_FIGURE','FULLTEXT_TABLE','ABSTRACT','METADATA','EXPERIMENT'}
CLAIM_KINDS={'AUTHOR_RESULT','AUTHOR_INTERPRETATION','AGENT_INFERENCE','RESEARCHER_JUDGMENT'}
ID=re.compile(r'^[A-Za-z0-9][\w.:-]{1,127}$')

def require_id(x,key):
    v=x.get(key)
    if not isinstance(v,str) or not ID.fullmatch(v):raise SemanticsError('非法或缺少 '+key)
    return v

def validate(packet):
    if packet.get('schema_version')!='1.0':raise SemanticsError('schema_version 必须为 1.0')
    papers={};claims={};evidence={};relations={};problems=[]
    for p in packet.get('papers',[]):
        uid=require_id(p,'paper_uid')
        if uid in papers:raise SemanticsError('重复 Paper UID '+uid)
        if p.get('access_scope') not in ACCESS:raise SemanticsError('来源访问等级非法')
        identity=p.get('identity',{})
        if not isinstance(identity,dict):raise SemanticsError('论文身份必须为对象')
        # External identifiers are alternate lookup keys, not internal UID.
        if not identity.get('doi') and not identity.get('arxiv_id') and not identity.get('pdf_sha256') and not identity.get('zotero'):
            raise SemanticsError('缺少任何可追踪的外部身份（允许无 DOI）')
        papers[uid]=p
    for e in packet.get('evidence',[]):
        eid=require_id(e,'evidence_id');uid=require_id(e,'paper_uid')
        if eid in evidence:raise SemanticsError('重复 evidence ID')
        if uid not in papers:raise SemanticsError('证据引用不存在的 Paper UID')
        kind=e.get('evidence_kind')
        if kind not in EVIDENCE_KIND:raise SemanticsError('非法 evidence_kind')
        if not isinstance(e.get('source_locator'),str) or not e['source_locator'].strip():raise SemanticsError('证据缺少精确来源定位')
        access=papers[uid]['access_scope']
        if kind.startswith('FULLTEXT') and access!='FULLTEXT_ACCESSED':raise SemanticsError('没有实际全文访问权限，不能声称图表/正文证据')
        if kind=='EXPERIMENT' and access!='INTERNAL_EXPERIMENT':raise SemanticsError('内部实验来源类型不匹配')
        if kind in {'METADATA','ABSTRACT'} and access=='INTERNAL_EXPERIMENT':raise SemanticsError('实验证据不能包装成论文元数据')
        if not isinstance(e.get('source_version'),str) or not e['source_version'].strip():raise SemanticsError('证据必须记录来源版本/文件哈希')
        evidence[eid]=e
    context_keys=('population','measurement','time_support','space_support','study_design','estimate_target')
    for c in packet.get('claims',[]):
        cid=require_id(c,'claim_id')
        if cid in claims:raise SemanticsError('重复 Claim ID')
        if c.get('claim_kind') not in CLAIM_KINDS:raise SemanticsError('不支持的 Claim 来源类型')
        if not isinstance(c.get('statement'),str) or len(c['statement'].strip())<10:raise SemanticsError('缺少充分的 Claim 表述')
        refs=c.get('evidence_refs',[])
        if not refs or any(ref not in evidence for ref in refs):raise SemanticsError('Claim 没有真实注册的证据引用')
        # An author's result/interpretation cannot silently merge sources from
        # different papers into one paper-attributed claim.  Agent synthesis is
        # allowed to use multiple papers but remains an inference.
        source_uids={evidence[ref]['paper_uid'] for ref in refs}
        declared=c.get('paper_uid')
        if declared is not None and declared not in papers:
            raise SemanticsError('Claim paper_uid 指向不存在的 Paper')
        if c['claim_kind'].startswith('AUTHOR_') and len(source_uids)!=1:
            raise SemanticsError('作者原始主张不能混合多篇论文的 Evidence')
        if declared is not None and c['claim_kind'].startswith('AUTHOR_') and declared not in source_uids:
            raise SemanticsError('Claim 所属论文与 Evidence 所属论文不一致')
        context=c.get('study_context',{})
        if not isinstance(context,dict) or any(not isinstance(context.get(k),str) or not context[k].strip() for k in context_keys):
            raise SemanticsError('Claim 缺少研究对象、测量、时空支持、设计与估计目标')
        claims[cid]=c
    for r in packet.get('relations',[]):
        rid=require_id(r,'relation_id');src=require_id(r,'source_claim_id')
        if rid in relations:raise SemanticsError('重复 Relation ID')
        if src not in claims:raise SemanticsError('Relation source 不存在')
        typ=r.get('relation_type')
        if typ not in TYPES:raise SemanticsError('非法关系类型')
        dst=r.get('target_claim_id') if typ in STUDY_REL else r.get('target_id')
        if not isinstance(dst,str) or not dst:raise SemanticsError('关系没有目标')
        if typ in STUDY_REL:
            if dst not in claims or dst==src:raise SemanticsError('支持/挑战/限定必须指向不同且存在的 Claim')
            compare=r.get('comparability')
            if not isinstance(compare,dict) or compare.get('status') not in ('COMPARABLE','CONDITIONALLY_COMPARABLE','NOT_COMPARABLE','NOT_ASSESSED'):
                raise SemanticsError('解释性科学关系缺少可比性判断')
            if not isinstance(compare.get('rationale'),str) or len(compare['rationale'].strip())<20:
                raise SemanticsError('科学关系需给出实质可比性理由')
            if not isinstance(r.get('scientific_warrant'),str) or len(r['scientific_warrant'].strip())<20:
                raise SemanticsError('解释性关系必须说明为什么证据支持此关联')
            if compare['status']=='NOT_COMPARABLE':
                problems.append({'relation_id':rid,'issue':'NOT_COMPARABLE','decision':'HOLD_CANDIDATE'})
            if compare['status']=='NOT_ASSESSED':
                problems.append({'relation_id':rid,'issue':'COMPARABILITY_UNASSESSED','decision':'HOLD_CANDIDATE'})
            if typ in {'SUPPORTS','CHALLENGES'} and not r.get('evidence_refs'):
                raise SemanticsError('解释性关系需要具体 evidence refs')
        if not isinstance(r.get('evidence_refs',[]),list) or any(x not in evidence for x in r.get('evidence_refs',[])):
            raise SemanticsError('关系引用未注册 Evidence')
        # Unlike Claim edges, Method/Data/external targets may live in a
        # separate long-term index. Never treat an unregistered external ID as
        # verified merely because a nonblank string was supplied.
        if typ not in STUDY_REL:
            target_registry=packet.get('external_targets',[])
            known={item.get('target_id') for item in target_registry if isinstance(item,dict)} if isinstance(target_registry,list) else set()
            if dst not in claims and dst not in papers and dst not in evidence and dst not in known:
                problems.append({'relation_id':rid,'issue':'EXTERNAL_TARGET_NOT_RESOLVED','decision':'HOLD_CANDIDATE'})
        if r.get('review_status') not in ('CANDIDATE','SOURCE_CHECKED','SCIENTIFIC_REVIEWED','REJECTED'):
            raise SemanticsError('非法复核状态')
        # A JSON label is not independent scientific validation.
        if r['review_status']=='SCIENTIFIC_REVIEWED' and not r.get('review_record_ref'):
            raise SemanticsError('已审查关系必须有可检查的外部审查回执')
        relations[rid]=r
    return {'schema_version':'1.0','paper_count':len(papers),'claim_count':len(claims),'evidence_count':len(evidence),
      'relation_count':len(relations),'held_relations':problems,'epistemic_status':'STRUCTURE_AND_REFERENCES_CHECKED_ONLY',
      'warning':'本程序没有读取论文原文；非本包注册表中的外部目标将暂缓，填写科学审查标签不等于实际验证。'}

def run(a):
    packet=json.loads(Path(a.input).read_text(encoding='utf-8-sig'))
    result=validate(packet)
    if a.output:
        out=safe_workspace(a.output)
        if out.exists():raise SemanticsError('拒绝覆盖已存在的语义结果目录')
        out.mkdir(parents=True,exist_ok=False)
        atomic_new(out/'semantic_packet.json',packet)
        atomic_new(out/'validation_report.json',{**result,'input_digest':digest(packet)})
        result['output']=str(out)
    print(json.dumps(result,ensure_ascii=False,indent=2))

def main(argv=None):
    p=argparse.ArgumentParser(description='PRKE candidate scientific semantic packet; no science truth assertion')
    sub=p.add_subparsers(dest='command',required=True)
    x=sub.add_parser('doctor');x.set_defaults(func=lambda _:print('PASS: candidate-only scientific relations; no remote or Vault execution'))
    x=sub.add_parser('validate');x.add_argument('--input',required=True);x.add_argument('--output');x.set_defaults(func=run)
    try:args=p.parse_args(argv);args.func(args);return 0
    except (SemanticsError,OSError,ValueError,TypeError,KeyError) as e:print('ERROR:',e,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
