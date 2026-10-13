"""Local, offline and conservative PDF evidence preparation/auditing for PRKE.

Important: rendering or text extraction is NOT visual scientific inspection.
Only the host reading agent may record actual visual observations. Automated
checks validate traceability/completeness of those receipts, not their truth.
Never writes to an Obsidian vault. No network traffic or document upload.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TYPE_FIELDS = {
    'REVIEW': ('scope', 'classification_logic', 'research_routes', 'representative_studies', 'consensus_vs_author_view', 'gaps_and_limits'),
    'SCIENTIFIC': ('scientific_question', 'hypotheses', 'study_design', 'direct_observations', 'mechanism_interpretation', 'causal_and_scope_limits'),
    'METHOD': ('prior_bottleneck', 'design_idea', 'components_and_equations', 'baselines', 'ablation_and_robustness', 'reproducibility_limits'),
    'DATA_RESOURCE': ('data_need', 'original_observations', 'construction_pipeline', 'variables_and_coverage', 'independent_validation', 'uncertainty_and_appropriate_use'),
}
FIG_PATTERN = re.compile(r'\b(?:(Fig(?:ure)?)[.\s]*([1-9]\d*[A-Za-z]?)|(Table)[.\s]*([1-9]\d*[A-Za-z]?))\b', re.IGNORECASE)

class UnderstandError(Exception):
    pass

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def read(path):
    try: return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError,ValueError) as exc: raise UnderstandError(f'无法读取 JSON {path}: {exc}') from exc

def new_file(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as out:json.dump(data,out,ensure_ascii=False,indent=2);out.write('\n')

def new_text(path, content):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as out:out.write(content)

def checksum(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def task_dir_safe(path):
    path=Path(path).expanduser().resolve()
    if path==Path(path.anchor):raise UnderstandError('不得把磁盘根目录作为任务暂存区')
    for parent in (path,*path.parents):
        if (parent/'.obsidian').exists() or (parent/'.research-kb').exists():
            raise UnderstandError('任务暂存路径位于知识库内：禁止直接入库')
    return path

def safe_id(text):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}',text) or text in ('.','..'):
        raise UnderstandError('paper-id 只允许英文、数字、点、短横线、下划线，且不得为路径')
    return text

def validate(kind, obj):
    try:import jsonschema
    except ImportError as exc:raise UnderstandError('需要 jsonschema: pip install -r requirements.txt') from exc
    schema=read(ROOT/'schemas'/'understand'/(kind+'.schema.json'))
    jsonschema.Draft202012Validator.check_schema(schema)
    errors=list(jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).iter_errors(obj))
    if errors:
        e=errors[0];loc='.'.join(str(x) for x in e.path)
        raise UnderstandError(f'{kind} schema 不匹配: {loc}: {e.message}; 共{len(errors)}项')

def path_inside(base,rel):
    p=(Path(base)/rel).resolve()
    if Path(base).resolve()!=p and Path(base).resolve() not in p.parents:
        raise UnderstandError(f'文件路径越界: {rel}')
    return p

def prepare(pdf_path,task_dir,paper_id,depth,interaction,primary_type,goal,doi='',title='',dpi=144,max_pages=250,supplements=None):
    import fitz
    pdf=Path(pdf_path).expanduser().resolve()
    if not pdf.is_file() or pdf.suffix.lower()!='.pdf':raise UnderstandError('需要现有 PDF 文件；本工具不自动获取或上传论文')
    if pdf.stat().st_size>150*1024*1024:raise UnderstandError('PDF 超过本版 150MB 限制')
    if depth not in ('SCAN','FOCUSED','DEEP'):raise UnderstandError('非法深度')
    if interaction not in ('SILENT','INTERACTIVE'):raise UnderstandError('非法交互模式')
    if primary_type not in TYPE_FIELDS:raise UnderstandError('非法论文类型')
    task=task_dir_safe(task_dir); paper_id=safe_id(paper_id)
    dest=task/'understand'/paper_id
    if dest.exists():raise UnderstandError('该任务下论文 ID 已存在。请复用已有核验记录，不覆盖原记录')
    doc=fitz.open(pdf)
    try:
        if doc.needs_pass:raise UnderstandError('加密 PDF 无法解析，请提供授权的可读版本')
        if not 1<=len(doc)<=max_pages:raise UnderstandError(f'页数超过限制（1..{max_pages}）')
        # Read first without creating persistent files. No OCR or synthetic figures.
        pages=[];counts={}; text_chars=0
        for i,p in enumerate(doc):
            txt=p.get_text('text')
            text_chars+=len(txt)
            pages.append({'page':i+1,'text':txt,'width':round(p.rect.width,2),'height':round(p.rect.height,2)})
            for m in FIG_PATTERN.finditer(txt):
                kind='FIGURE' if m.group(1) else 'TABLE';number=(m.group(2) if m.group(1) else m.group(4)).upper()
                key=f'{kind}:{number}'
                counts.setdefault(key,{'figure_id':f'{kind.lower()}-{number.lower()}','kind':kind,'label':f'{"Figure" if kind=="FIGURE" else "Table"} {number}', 'candidate_pages':[],'page':None,'status':'PENDING_VISUAL','rendered_asset':None,'visual_observation':'','claim_ids':[],'checked_by':None,'checked_at':None})
                if i+1 not in counts[key]['candidate_pages']:counts[key]['candidate_pages'].append(i+1)
        # The text search is only a candidate index; visual reconciliation is required.
        entries=list(counts.values())
        source_sha=checksum(pdf)
        source={'schema_version':'1.0','paper_id':paper_id,'source':{'pdf_path':str(pdf),'sha256':source_sha,'page_count':len(doc),'doi':doi,'title':title,'text_chars':text_chars,'text_quality':'TEXT_EXTRACTED' if text_chars>=400 else 'TEXT_LIMITED','created_at':now()},'pages':pages,'supplements':[],'rendered_pages':[],'render_quality':{'dpi':dpi,'status':'NOT_RENDERED'}}
        inventory={'schema_version':'1.0','paper_id':paper_id,'all_main_figures_accounted_for':False,'visual_reconciliation_note':'','items':entries}
        record={'schema_version':'1.0','paper_id':paper_id,'goal':goal,'depth':depth,'interaction':interaction,'primary_type':primary_type,'secondary_types':[],
                'reading_scope':'PDF_FULLTEXT' if text_chars>=400 else 'SOURCE_LIMITED',
                'source_bundle':'source_bundle.json',
                'argument_chain':{k:'' for k in ('problem','prior_limitation','approach','mechanism','results','conclusion')},
                'type_specific':{k:'' for k in TYPE_FIELDS[primary_type]},'critical_appraisal':[],
                'author_limitations':[],'agent_limitations':[],'takeaways':[],'user_annotations':[], 'unresolved_questions':[]}
        claims={'schema_version':'1.0','paper_id':paper_id,'claims':[]}
        # Supplementary PDFs are read-only. Their visible contents require separate inspection.
        supplement_files=[]
        for extra in (supplements or []):
            sp=Path(extra).expanduser().resolve()
            if not sp.is_file() or sp.suffix.lower()!='.pdf' or sp==pdf:
                raise UnderstandError('补充材料必须为独立且存在的 PDF 文件')
            if sp.stat().st_size > 150*1024*1024:raise UnderstandError('补充 PDF 超过150MB')
            with fitz.open(sp) as sd:
                if sd.needs_pass or not (1<=len(sd)<=max_pages):raise UnderstandError('补充 PDF 加密或页数超限')
                source['supplements'].append({'pdf_path':str(sp),'sha256':checksum(sp),'page_count':len(sd),'rendered_pages':[],'relevance_status':'UNASSESSED'})
            supplement_files.append(sp)
        dest.mkdir(parents=True,exist_ok=False)
        if depth in ('DEEP','FOCUSED'):
            imgdir=dest/'rendered_pages';imgdir.mkdir()
            for i,p in enumerate(doc):
                name=f'page_{i+1:04}.png'
                p.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False).save(str(imgdir/name))
                source['rendered_pages'].append({'page':i+1,'path':f'rendered_pages/{name}'})
            source['render_quality']['status']='ALL_PAGES_RENDERED_NOT_VISUALLY_CHECKED'
            for index,sp in enumerate(supplement_files,1):
                supp_out=dest/'rendered_supplements'/f'supp_{index:02d}';supp_out.mkdir(parents=True)
                with fitz.open(sp) as d2:
                    for j,page in enumerate(d2):
                        name=f'page_{j+1:04d}.png';page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False).save(str(supp_out/name))
                        source['supplements'][index-1]['rendered_pages'].append({'page':j+1,'path':f'rendered_supplements/supp_{index:02d}/{name}'})
        new_file(dest/'source_bundle.json',source)
        new_file(dest/'figure_inventory.json',inventory)
        new_file(dest/'reading_record.json',record)
        new_file(dest/'claim_evidence_matrix.json',claims)
        new_file(dest/'reading_audit.json',{'schema_version':'1.0','paper_id':paper_id,'status':'PARTIAL','audited_at':now(),'issues':['PREPARED_ONLY: 没有任何内容被自动标记为已阅读或已核验'], 'checks':{}})
        return dest
    finally:doc.close()

def audit(folder,save=False):
    folder=Path(folder).resolve()
    source=read(folder/'source_bundle.json');fig=read(folder/'figure_inventory.json');record=read(folder/'reading_record.json');claims=read(folder/'claim_evidence_matrix.json')
    for kind,ob in [('source_bundle',source),('figure_inventory',fig),('reading_record',record),('claim_evidence_matrix',claims)]:validate(kind,ob)
    paper_id=source['paper_id'];issues=[];blockers=[];checks={}
    if not (source['paper_id']==fig['paper_id']==record['paper_id']==claims['paper_id']):blockers.append('论文身份在各记录之间不一致')
    f=Path(source['source']['pdf_path'])
    if not f.is_file() or checksum(f)!=source['source']['sha256']:blockers.append('原始 PDF 不存在或已变更，所有来源定位失效')
    checks['source_same_version']=not blockers
    page_count=source['source']['page_count'];deep=record['depth']=='DEEP'
    for sp in source.get('supplements',[]):
        sx=Path(sp['pdf_path'])
        if not sx.is_file() or checksum(sx)!=sp['sha256']:blockers.append('补充 PDF 不存在或文件哈希已变化')
        if deep and sp['relevance_status']=='UNASSESSED':issues.append('存在补充材料但没有明确与核心结论的相关性/检查范围')
    if deep and source['render_quality']['status']!='ALL_PAGES_RENDERED_NOT_VISUALLY_CHECKED':issues.append('DEEP 必须渲染并检查 PDF 页面')
    page_assets={p['page']:p['path'] for p in source['rendered_pages']}
    fig_ids=set();checked=0
    for item in fig['items']:
        key=item['figure_id']
        if key in fig_ids:blockers.append('重复 figure_id: '+key)
        fig_ids.add(key)
        if item['status']=='VISUALLY_CHECKED':
            p=item['page'];rel=item['rendered_asset'];s=item['visual_observation'].strip()
            if (not isinstance(p,int) or p not in page_assets or rel!=page_assets.get(p) or not path_inside(folder,rel).is_file() or not s or item['checked_by']!='AGENT_VISUAL_INSPECTION' or not item['checked_at']):
                issues.append(f'{key}: VISUALLY_CHECKED 缺真实渲染来源或视觉观察记录')
            else:checked+=1
        elif deep: issues.append(f'{key}: 尚未完成原始图像核验 ({item["status"]})')
        if item['page'] is not None and not 1<=item['page']<=page_count:issues.append(f'{key}: 页码超出 PDF 范围')
    if deep and not fig['all_main_figures_accounted_for']:issues.append('未确认所有正文主 Figure/Table 都已纳入图表目录')
    if deep and not fig['visual_reconciliation_note'].strip():issues.append('缺少逐页核对图表目录的过程说明')
    checks['visual_verified_count']=checked;checks['visual_entries_total']=len(fig['items'])
    central_count=0; claim_ids=set()
    for c in claims['claims']:
        if c['claim_id'] in claim_ids:blockers.append('重复 claim_id: '+c['claim_id'])
        claim_ids.add(c['claim_id'])
        if c['central']: central_count+=1
        if not c['reasoning'].strip() or not c['evidence_summary'].strip():issues.append(f'{c["claim_id"]}: 缺少科学解释或证据内容')
        if deep and c['central'] and c['assessment']=='NOT_ASSESSABLE':issues.append(f'{c["claim_id"]}: 核心主张不可核验，完整精读不能 COMPLETED')
        if not c['source_refs']:issues.append(f'{c["claim_id"]}: 缺少可追溯来源')
        for ref in c['source_refs']:
            if ref['source_kind']=='PDF':
                if ref.get('page') is None or not 1<=ref['page']<=page_count:issues.append(f'{c["claim_id"]}: PDF 来源定位页码无效')
            elif ref['source_kind']=='PDF_IMAGE':
                idx=next((x for x in fig['items'] if x['figure_id']==ref.get('figure_id')),None)
                if idx is None or idx['status']!='VISUALLY_CHECKED' or idx['page']!=ref.get('page'):
                    issues.append(f'{c["claim_id"]}: 图像证据并未完成视觉核验')
            elif ref['source_kind']=='SUPPLEMENT':
                supps=source.get('supplements',[])
                if not supps or not ref.get('locator'):issues.append(f'{c["claim_id"]}: 补充材料证据缺可核查文件或位置')
            elif ref['source_kind']=='EXTERNAL' and not ref.get('locator'):
                issues.append(f'{c["claim_id"]}: 外部证据缺来源')
    if deep and central_count==0:issues.append('完整精读必须有至少一项核心科学主张及证据')
    checks['central_claims']=central_count
    if record['primary_type'] not in TYPE_FIELDS:blockers.append('未知学术贡献类型')
    else:
        for key in TYPE_FIELDS[record['primary_type']]:
            if deep and not record['type_specific'].get(key,'').strip():issues.append(f'{record["primary_type"]} 专项阅读内容缺失: {key}')
    if deep:
        covered={claim_id for review in record['critical_appraisal'] for claim_id in review['source_claim_ids']}
        missing_review=[c['claim_id'] for c in claims['claims'] if c['central'] and c['claim_id'] not in covered]
        if missing_review: issues.append('核心主张尚未经批判性检查: '+', '.join(missing_review))
        for key in ('problem','prior_limitation','approach','results','conclusion'):
            if not record['argument_chain'].get(key,'').strip():issues.append(f'未重建研究逻辑: {key}')
        if not record['critical_appraisal']:issues.append('缺少完整精读必须的批判性证据审查')
        else:
            for x in record['critical_appraisal']:
                if not x['source_claim_ids'] or not set(x['source_claim_ids']).issubset(claim_ids):issues.append(f'批判性审查 {x["issue_id"]} 没有指向已有核心主张')
                if not x['reasoning'].strip():issues.append(f'批判性审查 {x["issue_id"]} 缺少论证')
    if record['depth']!='DEEP':
        # Scans or focused reading may complete the stated scope without impersonating deep reading.
        if not record['argument_chain']['problem'].strip() or not record['takeaways']:
            issues.append('初读/定向阅读至少需要研究问题与实质性阅读收获')
    checks['depth']=record['depth']
    status='BLOCKED' if blockers else ('PARTIAL' if issues else 'COMPLETED')
    result={'schema_version':'1.0','paper_id':paper_id,'status':status,'audited_at':now(),'issues':blockers+issues,'checks':checks}
    validate('reading_audit',result)
    if save:
        # Audit status can be recalculated without claiming any new science has been read.
        # A fixed deterministic filename is the sole task-stage generated file updated in place.
        dest=folder/'reading_audit.json';tmp=folder/f'.audit-{uuid.uuid4().hex}.tmp'
        tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(dest)
    return result

def note(folder,allow_partial=False):
    folder=Path(folder).resolve();result=audit(folder,save=True)
    if result['status']=='BLOCKED':raise UnderstandError('存在来源或结构级阻断，不得生成知识草稿')
    if result['status']=='PARTIAL' and not allow_partial:raise UnderstandError('阅读审查未通过；可明确加 --allow-partial 生成标注未核验项的草稿')
    record=read(folder/'reading_record.json');source=read(folder/'source_bundle.json');claims=read(folder/'claim_evidence_matrix.json');fig=read(folder/'figure_inventory.json')
    meta=source['source'];depth=record['depth'];status=result['status'];
    def q(s):return json.dumps(s,ensure_ascii=False)
    front=[f'title: {q(meta.get("title") or record["paper_id"])}',f'paper_id: {q(record["paper_id"])}',f'doi: {q(meta.get("doi", ""))}',f'primary_type: {q(record["primary_type"])}',f'reading_depth: {q(depth)}',f'reading_audit: {q(status)}',f'source_sha256: {q(meta["sha256"])}','tags: [research/paper, research/understand]']
    out=['---',*front,'---','','# '+(meta.get('title') or record['paper_id']),'',f'> 阅读类型：{record["primary_type"]} ｜ 深度：{depth} ｜ 核验状态：{status}',f'> 阅读目标：{record["goal"]}','','## 研究逻辑']
    labels={'problem':'研究问题','prior_limitation':'已有不足','approach':'研究思路','mechanism':'机制或方法逻辑','results':'关键结果','conclusion':'结论及边界'}
    for k,v in record['argument_chain'].items():
        if v.strip():out.extend(['',f'**{labels[k]}**：{v.strip()}'])
    out.extend(['','## 类型专项认知'])
    for k,v in record['type_specific'].items():
        if v.strip():out.extend(['',f'**{k}**：{v.strip()}'])
    out.extend(['','## 核心主张与原文证据'])
    for c in claims['claims']:
        refs=', '.join(f'{r["source_kind"]} p.{r.get("page") or "?"} {r.get("figure_id") or r.get("locator") or ""}' for r in c['source_refs'])
        out.extend(['',f'- **{c["claim_id"]} [{c["role"]} / {c["assessment"]}]** {c["claim"]}',f'  - 原文依据：{refs or "未定位"}',f'  - 证据与判断：{c["evidence_summary"]}；{c["reasoning"]}'])
    out.extend(['','## 批判性评估'])
    for a in record['critical_appraisal']:
        out.extend(['',f'- **{a["issue_id"]} [{a["verdict"]}]** {a["question"]}：{a["reasoning"]}（Claim: {", ".join(a["source_claim_ids"]) }）'])
    out.extend(['','## 主要价值与局限'])
    out.extend(['', '**主要收获**：'+('；'.join(record['takeaways']) or '尚未整理')])
    if record['author_limitations']:out.extend(['','**作者报告的局限**：'+'；'.join(record['author_limitations'])])
    if record['agent_limitations']:out.extend(['','**Agent 评估的局限**：'+'；'.join(record['agent_limitations'])])
    if record['user_annotations']:out.extend(['','**研究者批注（原文保留）**：'+'；'.join(record['user_annotations'])])
    if record['unresolved_questions']:out.extend(['','**待解决问题**：'+'；'.join(record['unresolved_questions'])])
    out.extend(['','## 图表核验记录', '',f'- 已核验：{result["checks"]["visual_verified_count"]}/{len(fig["items"])}；正文图表清单已人工核对：{"是" if fig["all_main_figures_accounted_for"] else "否"}'])
    for item in fig['items']:
        out.append(f'- {item["label"]}：{item["status"]}；PDF p.{item["page"] or "待定位"}；{item["visual_observation"]}')
    if result['issues']:
        out.extend(['','## 审查未完成项',*('- '+x for x in result['issues'])])
    out.extend(['','## 来源与交接说明',f'- 原始 PDF：`{meta["pdf_path"]}`',f'- PDF SHA-256：`{meta["sha256"]}`','- 本文件是任务暂存阅读草稿，不等于已经写入 Obsidian。','- 机构授权 PDF 默认本地保留，不会随笔记自动上传到第三方。'])
    dest=folder/f'paper_note_{uuid.uuid4().hex[:8]}.md';new_text(dest,'\n'.join(out)+'\n')
    return dest

def make_html(folder):
    folder=Path(folder).resolve();record=read(folder/'reading_record.json');source=read(folder/'source_bundle.json');fig=read(folder/'figure_inventory.json')
    title=html.escape(source['source']['title'] or record['paper_id']);blocks=[]
    for h,key in [('研究问题','problem'),('已有不足','prior_limitation'),('解决思路','approach'),('机制与方法','mechanism'),('关键结果','results'),('结论边界','conclusion')]:
        value=html.escape(record['argument_chain'][key]);blocks.append(f'<section><h2>{h}</h2><p>{value or "尚未记录"}</p></section>')
    for x in fig['items']:
        path=x['rendered_asset'];img=''
        if path and x['page'] is not None and path_inside(folder,path).is_file():img=f'<a href="{html.escape(path,quote=True)}" target="_blank"><img loading="lazy" src="{html.escape(path,quote=True)}" alt="{html.escape(x["label"])}" /></a>'
        blocks.append(f'<section><h2>{html.escape(x["label"])} · {html.escape(x["status"])}</h2>{img}<p>{html.escape(x["visual_observation"] or "该图尚无已核验的视觉观察记录")}</p></section>')
    css='body{font:16px/1.7 system-ui,sans-serif;max-width:980px;margin:auto;padding:26px;color:#192938;background:#f5f7fa}section{background:white;border:1px solid #d9e1e8;border-radius:10px;padding:22px;margin:16px 0}img{max-width:100%;height:auto}h1{line-height:1.3}small{color:#667}'
    page=f'<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{css}</style></head><body><h1>{title}</h1><small>PRKE · 本地阅读视图 · 不含联网聊天或自动回写能力；选择交互式时在 Codex 中向 Agent 追问</small>{"".join(blocks)}</body></html>'
    dest=folder/f'interactive_reader_{uuid.uuid4().hex[:8]}.html';new_text(dest,page);return dest

def organize_handoff(folder,batch_id,approved=False):
    # Deliberately NO formal Vault API: Organize is NOT_CONNECTED in current release.
    folder=Path(folder).resolve();note_files=sorted(folder.glob('paper_note_*.md'))
    if not note_files:raise UnderstandError('先生成 Paper Note Draft 后才能交接')
    result=audit(folder,save=True)
    if result['status']=='BLOCKED':raise UnderstandError('来源被阻断，不能交接入库')
    out={'schema_version':'1.0','batch_id':safe_id(batch_id),'paper_id':result['paper_id'],'source_note':str(note_files[-1]),'reading_status':result['status'],'write_state':'PENDING_ORGANIZE','authorization_state':'USER_TASK_APPROVED' if approved else 'NOT_YET_APPROVED','permission_scope':'ONE_SPECIFIC_BATCH_ONLY','conflict_policy':'STOP_ON_CONFLICT_OR_EXISTING_USER_CONTENT','operations':['PROPOSE_UPSERT_NOTE'],'message':'仅交接候选；未连接 Organize，未对 Obsidian 进行任何写入'}
    dest=folder/f'organize_handoff_{uuid.uuid4().hex[:8]}.json';new_file(dest,out);return dest

def init_comparison(task_dir,paper_folders,question):
    task=task_dir_safe(task_dir)
    if len(paper_folders)<2:raise UnderstandError('至少需要两份论文记录')
    papers=[]
    for folder in paper_folders:
        p=Path(folder).resolve();r=audit(p,False);rec=read(p/'reading_record.json');s=read(p/'source_bundle.json')
        if r['status']=='BLOCKED':raise UnderstandError('含 BLOCKED 文献：'+rec['paper_id'])
        papers.append({'paper_id':rec['paper_id'],'record_dir':str(p),'primary_type':rec['primary_type'],'reading_depth':rec['depth'],'audit_status':r['status'],'source_sha256':s['source']['sha256']})
    if len({x['paper_id'] for x in papers})!=len(papers):raise UnderstandError('存在重复论文 ID')
    out={'schema_version':'1.0','question':question,'papers':papers,'dimensions':[],'divergences':[],'external_checks':[], 'interpretation_scope':'SELECTED_PAPERS_ONLY','status':'DRAFT_NOT_COMPARATIVELY_VERIFIED'}
    dest=task/'understand'/'comparisons'/f'comparison_{uuid.uuid4().hex[:8]}.json';new_file(dest,out);return dest

def doctor():
    files=['routes/understand.md','references/understand/reading-protocol.md','references/understand/paper-type-protocols.md','references/understand/visual-evidence.md','references/understand/critical-appraisal.md','references/understand/knowledge-handoff.md','scripts/understand/engine.py']
    if any(not (ROOT/x).is_file() for x in files):raise UnderstandError('Understand 关键协议文件缺失')
    for kind in ('source_bundle','reading_record','figure_inventory','claim_evidence_matrix','reading_audit','comparison_matrix'):
        import jsonschema
        jsonschema.Draft202012Validator.check_schema(read(ROOT/'schemas'/'understand'/(kind+'.schema.json')))
    reg=read(ROOT/'router/interfaces/module-registry.json')
    if reg['modules']['understand']['status']!='INSTRUCTION_READY' or reg['modules']['organize']['status']!='INSTRUCTION_READY':raise UnderstandError('Understand / Organize 注册状态错误')
    print('PASS: Understand 6 Schemas、协议、单入口注册有效；PDF 解析/视觉理解需运行实际论文任务')

def main(argv=None):
    p=argparse.ArgumentParser(description='PRKE Understand: 本地证据准备和质量审查；不触碰正式知识库，不联网')
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('doctor')
    a=sub.add_parser('prepare');a.add_argument('--supplement',action='append',default=[],help='本地补充材料 PDF，可重复');a.add_argument('--pdf',required=True);a.add_argument('--task-dir',required=True);a.add_argument('--paper-id',required=True);a.add_argument('--depth',choices=['SCAN','FOCUSED','DEEP'],default='DEEP');a.add_argument('--interaction',choices=['SILENT','INTERACTIVE'],default='SILENT');a.add_argument('--type',choices=list(TYPE_FIELDS),default='SCIENTIFIC');a.add_argument('--goal',required=True);a.add_argument('--doi',default='');a.add_argument('--title',default='');a.add_argument('--dpi',type=int,default=144)
    a=sub.add_parser('audit');a.add_argument('--paper-dir',required=True)
    a=sub.add_parser('note');a.add_argument('--paper-dir',required=True);a.add_argument('--allow-partial',action='store_true')
    a=sub.add_parser('html');a.add_argument('--paper-dir',required=True)
    a=sub.add_parser('handoff');a.add_argument('--paper-dir',required=True);a.add_argument('--batch-id',required=True);a.add_argument('--task-approved',action='store_true')
    a=sub.add_parser('init-comparison');a.add_argument('--task-dir',required=True);a.add_argument('--paper-dir',required=True,action='append');a.add_argument('--question',required=True)
    args=p.parse_args(argv)
    try:
        if args.cmd=='doctor':doctor()
        elif args.cmd=='prepare':
            if not 72<=args.dpi<=300:raise UnderstandError('DPI 必须介于 72–300')
            dest=prepare(args.pdf,args.task_dir,args.paper_id,args.depth,args.interaction,args.type,args.goal,args.doi,args.title,args.dpi,supplements=args.supplement);print('PREPARED:',dest,'\n注意：仅渲染/抽取，未自动阅读或核验图表')
        elif args.cmd=='audit':
            result=audit(args.paper_dir,True);print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['status']=='COMPLETED' else 3
        elif args.cmd=='note':print('DRAFT:',note(args.paper_dir,args.allow_partial))
        elif args.cmd=='html':print('HTML:',make_html(args.paper_dir))
        elif args.cmd=='handoff':print('STAGED HANDOFF ONLY:',organize_handoff(args.paper_dir,args.batch_id,args.task_approved))
        elif args.cmd=='init-comparison':print('COMPARISON DRAFT:',init_comparison(args.task_dir,args.paper_dir,args.question))
        return 0
    except (UnderstandError,ImportError,OSError,ValueError) as exc:print('ERROR:',exc,file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
