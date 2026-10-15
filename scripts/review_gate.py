"""Scientific critic review packet gate, intentionally not a science-truth oracle.

Strictly distinguishes self-check, separately scoped reviewer, and human-verified
reference. Reviews are declarations with traceable source anchors, never proof of
independence merely because reviewer_id differs.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from execution_core import safe_workspace, atomic_new, digest

class ReviewError(ValueError):pass
RISK={'LOW','MODERATE','HIGH','CRITICAL'}
VERDICTS={'SUPPORT','QUALIFY','DEFER','WITHDRAW'}
METHOD={'SELF_CHECK','SEPARATE_CONTEXT_AGENT','HUMAN_EXPERT'}

def validate(p):
    if p.get('schema_version')!='1.0' or p.get('risk') not in RISK:raise ReviewError('必须提供风险等级与 schema_version=1.0')
    for k in ('main_claim','main_evidence_refs','counterarguments','reviewer_verdict','review_method','review_evidence_refs'):
        if k not in p:raise ReviewError('缺少 '+k)
    if not isinstance(p['main_claim'],str) or len(p['main_claim'].strip())<15:raise ReviewError('主要科学主张不完整')
    if (not isinstance(p['main_evidence_refs'],list) or not p['main_evidence_refs'] or
        any(not isinstance(x,str) or not x.strip() for x in p['main_evidence_refs'])):
        raise ReviewError('主分析证据必须为非空来源引用列表')
    if p['reviewer_verdict'] not in VERDICTS or p['review_method'] not in METHOD:raise ReviewError('不支持的复核类型或结论')
    if not isinstance(p['counterarguments'],list) or not p['counterarguments'] or any(not isinstance(a,dict) or not isinstance(a.get('reason'),str) or not a['reason'].strip() for a in p['counterarguments']):
        raise ReviewError('反方审查必须有实际挑战或说明为何无法发现挑战')
    if not isinstance(p['review_evidence_refs'],list) or any(not isinstance(x,str) or not x.strip() for x in p['review_evidence_refs']):raise ReviewError('review_evidence_refs 必须为来源字符串列表')
    if p['review_method']=='SEPARATE_CONTEXT_AGENT':
        if not p.get('reviewer_execution_receipt') or not p.get('reviewer_source_access'):
            raise ReviewError('声称不同上下文子 Agent 审查必须有执行记录与独立来源访问声明')
    if p['review_method']=='HUMAN_EXPERT' and not p.get('human_review_ref'):
        raise ReviewError('人类专家复核必须有外部可验证审查记录引用')
    if p['risk'] in ('HIGH','CRITICAL') and p['review_method']=='SELF_CHECK':
        status='INDEPENDENT_REVIEW_NOT_PERFORMED'
    elif p['risk'] in ('HIGH','CRITICAL') and not p['review_evidence_refs']:
        status='REVIEW_EVIDENCE_INCOMPLETE'
    elif p['reviewer_verdict']=='DEFER':status='SCIENTIFIC_JUDGMENT_DEFERRED'
    else:status='REVIEW_RECORDED_NOT_TRUTH_VERIFIED'
    return {'schema_version':'1.0','review_status':status,'risk':p['risk'],
        'verdict':p['reviewer_verdict'],'review_method':p['review_method'],
        'independence_assurance':'DECLARED_NOT_CRYPTOGRAPHICALLY_ATTESTED',
        'warning':'本程序核验声明及必要关联项，不证明科学判断真实或评审身份不可伪造。'}

def process(a):
    p=json.loads(Path(a.input).read_text(encoding='utf-8-sig'))
    r=validate(p)
    if a.output:
        o=safe_workspace(a.output)
        if o.exists():raise ReviewError('审查目录已存在，拒绝覆盖')
        o.mkdir(parents=True,exist_ok=False)
        atomic_new(o/'review_packet.json',p);atomic_new(o/'review_gate.json',{**r,'packet_digest':digest(p)})
        r['output']=str(o)
    print(json.dumps(r,ensure_ascii=False,indent=2))

def main(argv=None):
    x=argparse.ArgumentParser(description='Scientific critic review provenance gate, NOT automated peer review')
    s=x.add_subparsers(dest='command',required=True)
    p=s.add_parser('validate');p.add_argument('--input',required=True);p.add_argument('--output');p.set_defaults(run=process)
    s.add_parser('doctor').set_defaults(run=lambda _:print('PASS: review contracts; independent scientific truth NOT validated'))
    try:a=x.parse_args(argv);a.run(a);return 0
    except (ReviewError,OSError,ValueError,TypeError) as e:print('ERROR:',e,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
