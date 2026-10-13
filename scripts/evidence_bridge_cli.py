"""Read-only, actual Understand => Synthesize envelope; leaves scientific interpretation unset."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from organize_cli import get_understand,paper_uid,OrganizeError
from synthesize_engine import ScienceError,write_new

def run(a):
    dest=Path(a.output).expanduser().resolve()
    if dest.exists():raise ScienceError('输出已存在，禁止覆盖')
    papers=[];uids=set()
    for location in a.paper_dir:
        path,src,rec,audit,fig,claims=get_understand(location)
        if audit['status']!='COMPLETED' and not a.allow_partial:raise ScienceError('需要 DEEP/FOCUSED 完整审读审计；'+str(path)+' 为 '+audit['status'])
        uid=paper_uid(src)
        if uid in uids:continue
        uids.add(uid)
        rows=[]
        for c in claims['claims']:
            refs=[]
            for z in c['source_refs']:
                kind=z['source_kind'];pg=z.get('page');loc=z.get('figure_id') or z.get('locator') or ''
                refs.append(f'{kind} PDF p.{pg}' + (' '+loc if loc else '') if pg else (f'{kind} '+loc if loc else f'{kind} UNLOCATED'))
            if not refs:raise ScienceError('已有 Claim 缺来源定位：'+c['claim_id'])
            rows.append({'claim_id':c['claim_id'],'statement':c['claim'],'source_locator':'; '.join(refs),
                         'question_dimension':'REQUIRES_SCIENTIFIC_ALIGNMENT','study_context':'NOT_ASSESSED','study_design':'NOT_ASSESSED',
                         'estimate_target':'NOT_SPECIFIED','spatiotemporal_support':'NOT_SPECIFIED',
                         'evidence_kind':'FULLTEXT_FIGURE' if any(z['source_kind']=='PDF_IMAGE' for z in c['source_refs']) else 'FULLTEXT_TEXT',
                         'stance':'UNCLEAR','verification_level':'UNDERSTAND_'+audit['status'],
                         'claim_role':c['role'],'source_assessment':c['assessment'],'reasoning':c.get('reasoning','')})
        if not rows:raise ScienceError('论文 Claim-Evidence Matrix 为空，不能构造科研综合输入')
        papers.append({'paper_uid':uid,'doi':src['source'].get('doi'),'source_type':'PEER_REVIEWED_FULLTEXT',
                       'source_sha256':src['source']['sha256'],'source_independence_key':None,
                       'primary_type':rec['primary_type'],'reading_audit':audit['status'],'source_paper_id':src['paper_id'],'claims':rows})
    packet={'schema_version':'1.0','topic_id':a.topic_id,'research_question':a.research_question,'mode':a.mode,
            'papers':papers,'candidate_gaps':[],
            'scientific_alignment_required':True,
            'host_instruction':'科研 Agent 必须逐条复核并填写 question_dimension、study_context、study_design、stance、时空支持、估计目标、独立性；未核验前不得把此 envelope 当作已完成科研综合。'}
    write_new(dest,packet)
    print('BRIDGE_DRAFT:',dest,'\nUNIQUE_PAPERS:',len(papers),'\nCLAIMS:',sum(len(p['claims']) for p in papers),'\nNO EXTERNAL REQUESTS; NO VAULT WRITES')
def main(argv=None):
    p=argparse.ArgumentParser(description='Read-only bridge from actual Understand evidence to a draft Synthesize packet')
    p.add_argument('--paper-dir',action='append',required=True);p.add_argument('--topic-id',required=True);p.add_argument('--research-question',required=True)
    p.add_argument('--mode',choices=['TOPIC_INCREMENTAL','FOCUSED_SYNTHESIS','SYSTEMATIC_REVIEW'],default='FOCUSED_SYNTHESIS');p.add_argument('--output',required=True)
    p.add_argument('--allow-partial',action='store_true')
    a=p.parse_args(argv)
    try:run(a);return 0
    except (ScienceError,OrganizeError,KeyError,ValueError,OSError) as e:print('ERROR:',e,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
