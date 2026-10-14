"""PRKE v1.5 scientific evidence envelope and conservative draft synthesis.
No language model is hidden in this module: semantic judgments must be supplied with
source references and verified by a host agent/researcher. All outputs remain drafts.
"""
from __future__ import annotations
import hashlib,json,re,uuid
from datetime import datetime,timezone
from pathlib import Path

class ScienceError(ValueError):pass
MODES={'TOPIC_INCREMENTAL','FOCUSED_SYNTHESIS','SYSTEMATIC_REVIEW'}
ACCESS={'PEER_REVIEWED_FULLTEXT','ABSTRACT_ONLY','METADATA_ONLY','PREPRINT','INTERNAL_EXPERIMENT'}
STANCES={'SUPPORTS','CHALLENGES','CONTEXT_ONLY','UNCLEAR'}
EVENTS={'EVIDENCE_ADDED','COUNTEREVIDENCE_FOUND','SCOPE_REFINED','HYPOTHESIS_REVISED','SPLIT','MERGE','PRIOR_WORK_RESOLVED','RESEARCHER_DECISION','NO_MATERIAL_CHANGE'}
WORKFLOW={'CANDIDATE','NEEDS_VERIFICATION','PENDING_HUMAN','APPROVED','ARCHIVED'}
EVIDENCE={'SUPPORTING','MIXED','INSUFFICIENT','CHALLENGED','RESOLVED_BY_PRIOR_WORK'}
NOVELTY={'NOT_SEARCHED','PARTIAL','BOUNDED_CHECK_COMPLETED'}

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(o):return hashlib.sha256(canonical(o).encode('utf-8')).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write_new(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
def require(x,k,cls=str):
    value=x.get(k)
    if not isinstance(value,cls) or (cls==str and not value.strip()):raise ScienceError('缺少或非法字段: '+k)
    return value

def validate_packet(p):
    if not isinstance(p,dict):raise ScienceError('科研输入需为 JSON 对象')
    require(p,'topic_id');require(p,'research_question');mode=require(p,'mode')
    if mode not in MODES:raise ScienceError('错误综合模式')
    papers=require(p,'papers',list)
    if not papers:raise ScienceError('无可分析文献，禁止生成综合')
    ids=set();allclaims=set();data=[]
    for paper in papers:
        uid=require(paper,'paper_uid');access=require(paper,'source_type')
        if uid in ids:raise ScienceError('重复 Paper UID: '+uid)
        ids.add(uid)
        if access not in ACCESS:raise ScienceError('来源类型未知: '+access)
        claims=require(paper,'claims',list)
        if access in ('METADATA_ONLY','ABSTRACT_ONLY') and any(c.get('evidence_kind') in ('FULLTEXT_FIGURE','FULLTEXT_TABLE') for c in claims):
            raise ScienceError('摘要或元数据来源不得冒充已核验原始图表')
        for c in claims:
            cid=require(c,'claim_id');require(c,'statement');require(c,'source_locator');require(c,'question_dimension');require(c,'study_context');require(c,'study_design');
            kind=require(c,'evidence_kind');stance=require(c,'stance')
            if (uid,cid) in allclaims:raise ScienceError('重复 Claim ID')
            allclaims.add((uid,cid))
            if stance not in STANCES:raise ScienceError('无效证据方向: '+stance)
            if access=='INTERNAL_EXPERIMENT' and not paper.get('experiment_run_id'):raise ScienceError('内部实验缺实验 Run ID')
            data.append({'paper_uid':uid,'claim_id':cid,'claim_ref':uid+'#'+cid,'source_locator':c['source_locator'],'source_type':access,'source_hash':paper.get('source_sha256'),'source_independence_key':paper.get('source_independence_key'),'study_design':c['study_design'],'study_context':c['study_context'],'question_dimension':c['question_dimension'],'evidence_kind':kind,'stance':stance,'statement':c['statement'],'limitations':c.get('limitations',[]),'estimate_target':c.get('estimate_target','NOT_SPECIFIED'),'spatiotemporal_support':c.get('spatiotemporal_support','NOT_SPECIFIED'),'verification_level':c.get('verification_level','REPORTED_NOT_INDEPENDENTLY_VERIFIED')})
    for f in p.get('scientific_findings',[]):
        require(f,'finding_id');require(f,'statement');require(f,'evidence_refs',list);require(f,'boundary');require(f,'epistemic_label')
        if not f['evidence_refs'] or any(ref not in {r['claim_ref'] for r in data} for ref in f['evidence_refs']):raise ScienceError('科学综合结论缺有来源的 Claim Ref')
        if f['epistemic_label'] not in ('AGENT_SYNTHESIS_DRAFT','EVIDENCE_INSUFFICIENT'):
            raise ScienceError('未经独立审查，综合结论不得直接标人类确认或已证实共识')
    for d in p.get('disagreements',[]):
        require(d,'question_dimension');require(d,'evidence_refs',list);require(d,'interpretation')
        if any(ref not in {r['claim_ref'] for r in data} for ref in d['evidence_refs']):raise ScienceError('分歧分析引用无效')
    for g in p.get('candidate_gaps',[]):
        require(g,'gap_id');require(g,'statement');refs=require(g,'evidence_refs',list)
        change=g.get('evidence_change',{})
        if change:
            if not isinstance(change,dict) or change.get('kind') not in ('COUNTEREVIDENCE_FOUND','EVIDENCE_ADDED'):
                raise ScienceError('不支持的明确证据事件')
            if change['kind']=='COUNTEREVIDENCE_FOUND':
                chosen=change.get('evidence_refs',[])
                stances={r['claim_ref']:r['stance'] for r in data}
                if (not isinstance(chosen,list) or not chosen or not set(chosen).issubset(set(refs)) or
                    not all(stances.get(ref)=='CHALLENGES' for ref in chosen) or
                    not isinstance(change.get('reason'),str) or len(change['reason'].strip())<20):
                    raise ScienceError('反证必须引用已经注册的 CHALLENGES Claim 并给出科学理由')
        if not refs or any(ref not in {r['claim_ref'] for r in data} for ref in refs):raise ScienceError('Gap 无效证据引用')
        if 'first' in g['statement'].lower() or '首次' in g['statement'] or '无人研究' in g['statement']:raise ScienceError('禁止在候选 Gap 中自动宣称首次/无人研究')
    return data

def build(p):
    rows=validate_packet(p)
    bydim={}
    for r in rows:bydim.setdefault(r['question_dimension'],[]).append(r)
    findings=[]
    for dim,rr in sorted(bydim.items()):
        studies=len({r['paper_uid'] for r in rr});ind={r['source_independence_key'] for r in rr if r['source_independence_key']}
        stance={s:sum(r['stance']==s for r in rr) for s in sorted(STANCES)}
        unique_context=len({(r['study_context'],r['study_design'],r['estimate_target'],r['spatiotemporal_support']) for r in rr})
        findings.append({'question_dimension':dim,'unique_papers':studies,'known_independent_source_groups':len(ind),
                         'evidence_direction_counts':stance,'unique_comparability_contexts':unique_context,
                         'judgment':'NEEDS_SCIENTIFIC_APPRAISAL',
                         'note':'证据方向只按声明统计；不可由计数推断共识、因果效应或研究独立性。'})
    gaps=[];blocked=[]
    for g in p.get('candidate_gaps',[])[:3]:
        record=g.get('verification',{});searches=record.get('searches',[])
        complete=bool(searches) and all(x.get('database') and x.get('date') and x.get('query') and x.get('status')=='COMPLETED' for x in searches)
        gaps.append({'gap_id':g['gap_id'],'statement':g['statement'],'evidence_refs':g['evidence_refs'],'closest_prior_work':record.get('closest_prior_work',[]),
                    'verification_status':'BOUNDED_CHECK_COMPLETED' if complete else 'PARTIAL',
                    'human_approval_required':True,'evidence_change':g.get('evidence_change',{}),'hypothesis':g.get('hypothesis'),'falsifier':g.get('falsifier'),
                    'failure_modes':g.get('failure_modes',[]),'verification_record':record})
        if not complete:blocked.append('Gap '+g['gap_id']+' 尚未提供完整有界反证检索记录')
    if not p.get('scientific_findings'):
        blocked.append('尚未形成按原始来源核验、包含成立边界的跨论文科学综合判断')
    if any(r['study_context']=='NOT_ASSESSED' or r['study_design']=='NOT_ASSESSED' or r['question_dimension']=='REQUIRES_SCIENTIFIC_ALIGNMENT' or r['stance']=='UNCLEAR' for r in rows):
        blocked.append('存在尚未经科研 Agent 对齐、独立核验或缺少证据方向判断的原始主张，不能宣称形成可靠综合')
    if len(p.get('candidate_gaps',[]))>3:blocked.append('超过默认 1–3 个高优先级 Gap，本次只交接前三个候选')
    if p['mode']=='SYSTEMATIC_REVIEW':
        protocol=p.get('review_protocol',{})
        for key in ('inclusion_criteria','exclusion_criteria','databases','search_strategy','screening_log'):
            if not protocol.get(key):blocked.append('发表级综述缺预注册/明确的 '+key)
    output={'schema_version':'1.0','run_id':'syn-'+uuid.uuid4().hex[:12],'created_at':now(),'topic_id':p['topic_id'],'research_question':p['research_question'],'mode':p['mode'],'input_digest':digest(p),'source_coverage':{'unique_papers':len(p['papers']),'claims':len(rows),'internal_experiments':sum(x['source_type']=='INTERNAL_EXPERIMENT' for x in p['papers']),
                           'source_type_counts':{s:sum(x['source_type']==s for x in p['papers']) for s in sorted(ACCESS)}},
            'evidence_matrix':rows,'evidence_group_overview':findings,'scientific_findings':p.get('scientific_findings',[]),
            'disagreements':p.get('disagreements',[]),'candidate_gaps':gaps,
            'unresolved_checks':blocked,'epistemic_status':'AI_SYNTHESIS_DRAFT',
            'audit':{'status':'PARTIAL' if blocked else 'COMPLETED','content_verdict':'SCIENTIFIC_REVIEW_REQUIRED',
                      'caution':'结构与来源一致性检查通过，并不代表完成科研内容独立核验或证实创新性。',
                      'must_review':['主张原文证据支持度','文献覆盖与选择偏差','可比性和共享数据','统计/因果推断边界','Gap 反证检索完整性']}}
    return output

def markdown(report):
    a=['---','asset_type: synthesis_draft','cssclasses: [prke-academic]','topic_id: '+json.dumps(report['topic_id'],ensure_ascii=False),'epistemic_status: AI_SYNTHESIS_DRAFT','---','','# 科学综合草稿｜'+report['research_question'],'',
       '> [!warning] 科研证据边界','> 本报告是结构化来源汇总及**待科研审查的 AI 综合底稿**，并不自动建立领域共识、因果效应或创新性。','',
       '## 文献范围与来源','',f'- 模式：`{report["mode"]}`',f'- 唯一论文：{report["source_coverage"]["unique_papers"]}；证据条目：{report["source_coverage"]["claims"]}',
       f'- 内部实验来源：{report["source_coverage"]["internal_experiments"]}（与文献证据区分）','','## 按科学问题维度对齐的证据','']
    for group in report['evidence_group_overview']:
        a.extend(['### '+group['question_dimension'],f'- 已收录 {group["unique_papers"]} 篇论文；已知独立来源组 {group["known_independent_source_groups"]}；可比性背景组合 {group["unique_comparability_contexts"]}',
                  '- **仅统计方向，不据此投票判断共识。**',''])
        for r in report['evidence_matrix']:
            if r['question_dimension']==group['question_dimension']:
                a.append(f'- `{r["claim_ref"]}` [{r["source_type"]} / {r["stance"]}] {r["statement"]}；定位：`{r["source_locator"]}`；研究背景：{r["study_context"]}')
        a.append('')
    a.extend(['## 具有原始证据来源的阶段性科学综合（Agent 草稿）',''])
    for f in report.get('scientific_findings',[]):
        a.extend(['### '+f['finding_id'],f['statement'],f'- 原始证据：{", ".join(f["evidence_refs"])}',f'- 成立范围与不确定性：{f["boundary"]}',f'- 认知来源：`{f["epistemic_label"]}`',''])
    if not report.get('scientific_findings'):a.append('尚未提交经过跨论文对齐的阶段性综合论证；仅展示证据索引。')
    a.extend(['','## 研究分歧与证据异质性',''])
    for d in report.get('disagreements',[]):a.extend(['### '+d['question_dimension'],d['interpretation'],'- 涉及来源：'+', '.join(d['evidence_refs']),''])
    if not report.get('disagreements'):a.append('本次尚无经过证据核验的独立分歧判断；不意味着领域不存在分歧。')
    a.extend(['','## 待核验的 Research Gaps',''])
    if not report['candidate_gaps']:a.append('本轮没有经支持的候选 Gap，不为凑数生成。')
    for g in report['candidate_gaps']:
        a.extend(['### '+g['gap_id'],g['statement'],f'- 关联原始证据：{", ".join(g["evidence_refs"])}',f'- 反证核验状态：`{g["verification_status"]}`；未经用户批准不得正式生成 Idea。',''])
    a.extend(['## 科学核验与限制','',f'- 结构审计状态：`{report["audit"]["status"]}`；独立科学评估：`{report["audit"]["content_verdict"]}`'])
    a.extend(['- '+x for x in (report['unresolved_checks'] or ['无结构阻断项；仍需科研判断。'])]);a.append('')
    return '\n'.join(a)
