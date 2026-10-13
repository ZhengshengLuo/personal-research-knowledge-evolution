"""Offline Acquire record validator and duplicate-risk report.

This is not a scholarly search engine. No network access, DOI resolver checks,
PDF retrieval, Undermind invocation, or writes to Zotero/Obsidian.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / 'schemas' / 'acquire'
KINDS = ('search_plan', 'candidate_set', 'search_log', 'domain_map', 'coverage_matrix', 'manual_handoff_queue', 'pdf_acquisition_manifest')
REQUIRED_FILES = [
    'routes/acquire.md','references/acquire-methodology.md',
    'references/acquire-screening.md','adapters/undermind.md',
    'router/interfaces/module-registry.json', 'scripts/pdf_acquisition.py', 'scripts/acquire_pdf_cli.py',
]

class AcquireError(Exception):
    pass


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        raise AcquireError(f'无法读取 JSON: {path}: {exc}') from exc


def validator_lib():
    try:
        import jsonschema
    except ImportError as exc:
        raise AcquireError('缺少 jsonschema，请安装 requirements.txt') from exc
    return jsonschema


def normalize_doi(raw):
    """Syntax-level normalization only, never proves DOI exists."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    x = unquote(raw.strip()).replace('\\', '/')
    x = re.sub(r'^(?:doi\s*:\s*|https?://(?:dx\.)?doi\.org/)', '', x, flags=re.I)
    x = x.strip().strip('<>')
    x = re.sub(r'[.\s,;]+$', '', x)
    if re.fullmatch(r'10\.\d{4,9}/\S+', x, flags=re.I):
        return x.lower()
    return None


def title_key(title):
    text = unicodedata.normalize('NFKC', str(title)).casefold().strip()
    text = re.sub(r'[^\w]+', '', text)
    return text


def semantic_check(kind, data):
    if kind == 'search_plan':
        years=data['scope']
        if years.get('publication_from') is not None and years.get('publication_to') is not None and years['publication_from'] > years['publication_to']:
            raise AcquireError('发表时间起始年份晚于结束年份')
        ids=[q['query_id'] for q in data['queries']]
        if len(ids)!=len(set(ids)):
            raise AcquireError('检索计划 query_id 不唯一')
        if data['mode']=='SYSTEMATIC' and data['protocol_status']=='EXPLORATORY':
            raise AcquireError('SYSTEMATIC 不能使用 EXPLORATORY 协议状态')
        if data['protocol_status'] in ('FROZEN','AMENDED') and not data['sources']:
            raise AcquireError('冻结协议必须记录预定文献来源')
    if kind == 'candidate_set':
        ids=[p['record_id'] for p in data['papers']]
        if len(ids)!=len(set(ids)):
            raise AcquireError('候选记录 record_id 不唯一')
        for p in data['papers']:
            v=p['verification']
            if p['doi'] is not None and normalize_doi(p['doi']) is None:
                raise AcquireError(f"DOI 语法异常 ({p['record_id']}): {p['doi']}")
            if v['bibliography']=='CROSSCHECKED' and len(set(v['bibliographic_sources']))<2:
                raise AcquireError(f"CROSSCHECKED 必须列出至少两个可核验来源: {p['record_id']}")
            if v['read_scope']=='FULLTEXT_ACCESSED' and v['fulltext']!='ACCESSED':
                raise AcquireError(f"标记读全文却未记录已访问全文: {p['record_id']}")
            if v['claim_evidence']!='NOT_CHECKED' and v['read_scope']!='FULLTEXT_ACCESSED':
                raise AcquireError(f"未读全文不能标记正文主张已核验: {p['record_id']}")
            if v['bibliography']=='CONFLICT' and p['screening']['decision']=='INCLUDE':
                raise AcquireError(f"题录冲突条目应暂缓纳入: {p['record_id']}")
    if kind == 'domain_map':
        for branch in data['branches']:
            if branch['confidence']=='SUPPORTED' and not branch['supporting_paper_ids']:
                raise AcquireError('领域地图的 SUPPORTED 分支必须引用真实候选记录 ID')
    if kind == 'coverage_matrix':
        for dimension in data['dimensions']:
            if dimension['coverage']=='REASONABLE_FOR_TASK' and not dimension['supporting_paper_ids']:
                raise AcquireError('覆盖充分判断必须有支撑的候选文献记录')
    if kind == 'manual_handoff_queue':
        ids=[x['record_id'] for x in data['items']]
        if len(ids)!=len(set(ids)):raise AcquireError('人工队列存在重复 record_id')
    if kind == 'pdf_acquisition_manifest':
        for entry in data['items']:
            if entry['status']=='VERIFIED':
                path=entry.get('verified_copy') or (entry.get('file') or {}).get('verified_path')
                if not path:raise AcquireError('VERIFIED 下载项必须记录已验证 PDF 副本路径')
    if kind == 'search_log':
        ids=[q['query_id'] for q in data['runs']]
        if len(ids)!=len(set(ids)):
            raise AcquireError('检索日志中 query_id 重复；重试应另记检索 ID')
        for row in data['runs']:
            if row['status']=='RUNNING' and not row.get('external_job_ref'):
                raise AcquireError('RUNNING 异步任务需提供 external_job_ref')
            if row['status']=='SKIPPED' and row['result_count'] is not None:
                raise AcquireError('SKIPPED 任务不应该填写实际结果数量')


def validate(kind, data):
    if kind not in KINDS:
        raise AcquireError(f'不支持的 Schema：{kind}')
    lib=validator_lib()
    schema=read_json(SCHEMAS / (kind+'.schema.json'))
    lib.Draft202012Validator.check_schema(schema)
    errors=sorted(lib.Draft202012Validator(schema,format_checker=lib.FormatChecker()).iter_errors(data),key=lambda e:list(map(str,e.absolute_path)))
    if errors:
        e=errors[0]
        raise AcquireError(f'Schema 不通过: {".".join(map(str,e.absolute_path))}: {e.message}')
    semantic_check(kind,data)


def duplicate_risks(papers):
    by_doi=defaultdict(list)
    by_title=defaultdict(list)
    invalid=[]
    for paper in papers:
        key=normalize_doi(paper['doi'])
        if key: by_doi[key].append(paper['record_id'])
        elif paper['doi']: invalid.append(paper['record_id'])
        year=paper.get('year')
        if year and title_key(paper['title']):
            by_title[(title_key(paper['title']), year)].append(paper['record_id'])
    confirmed=[]
    for doi,ids in sorted(by_doi.items()):
        if len(ids)>1:
            confirmed.append({'doi':doi,'record_ids':ids,'action':'REVIEW_BEFORE_MERGE'})
    possible=[]
    for (title,year),ids in sorted(by_title.items()):
        if len(ids)>1:
            possible.append({'normalized_title':title,'year':year,'record_ids':ids,'action':'MANUAL_REVIEW'})
    return {'identical_doi_groups':confirmed,'same_title_year_groups':possible,'invalid_doi_records':invalid,'note':'此报告只提示重复风险，不自动合并；不同 DOI 的预印本/正式版可能为同一研究的不同版本。'}


def protect_output(output):
    # Always create only a new file, never overwrite. Disallow output under any
    # parent containing .obsidian or .research-kb marker; resolve symlinks.
    target=Path(output).expanduser().resolve()
    for parent in (target.parent,*target.parent.parents):
        if (parent/'.obsidian').exists() or (parent/'.research-kb').exists():
            raise AcquireError('不允许向正式 Obsidian/PRKE 库写入；请指定独立暂存目录')
    if target.parent == Path(target.anchor):
        raise AcquireError('不允许将报告直接写入磁盘根目录')
    if target.exists():
        raise AcquireError('输出已存在，不覆盖: '+str(target))
    return target


def run(args=None):
    parser=argparse.ArgumentParser(description='PRKE Acquire offline validator; no literature search or Vault changes')
    sub=parser.add_subparsers(dest='cmd',required=True)
    sub.add_parser('doctor')
    v=sub.add_parser('validate');v.add_argument('--kind',required=True,choices=KINDS);v.add_argument('--file',required=True)
    d=sub.add_parser('dedup-report');d.add_argument('--file',required=True);d.add_argument('--output',required=True)
    a=sub.add_parser('audit');a.add_argument('--file',required=True)
    parsed=parser.parse_args(args)
    try:
        if parsed.cmd=='doctor':
            for item in REQUIRED_FILES:
                if not (ROOT/item).is_file(): raise AcquireError('缺少必要文件: '+item)
            for kind in KINDS:
                validate(kind,read_json(ROOT/'examples'/'acquire'/(kind+'.example.json')))
            registry=read_json(ROOT/'router/interfaces/module-registry.json')
            conf=registry['modules']['acquire']
            if conf['status']!='INSTRUCTION_READY' or conf['implementation_ref']!='routes/acquire.md':
                raise AcquireError('Acquire 注册表错误')
            print('PASS: Acquire 7 Schemas、示例、检索协议与注册表有效（不包含联网功能测试）')
        elif parsed.cmd=='validate':
            validate(parsed.kind,read_json(parsed.file));print('PASS:',parsed.kind)
        elif parsed.cmd=='audit':
            data=read_json(parsed.file);validate('candidate_set',data)
            p=data['papers']; risk=duplicate_risks(p)
            print(json.dumps({'count':len(p),'screening':{k:sum(x['screening']['decision']==k for x in p) for k in ['INCLUDE','MAYBE','EXCLUDE']},'duplicate_risks':risk},ensure_ascii=False,indent=2))
        elif parsed.cmd=='dedup-report':
            data=read_json(parsed.file);validate('candidate_set',data)
            output=protect_output(parsed.output)
            result={'task_id':data['task_id'],'candidates_count':len(data['papers']),'duplicate_risks':duplicate_risks(data['papers'])}
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('x',encoding='utf-8') as file: json.dump(result,file,ensure_ascii=False,indent=2);file.write('\n')
            print('CREATED:',output)
        return 0
    except AcquireError as exc:
        print('ERROR:',exc,file=sys.stderr);return 2

if __name__=='__main__':
    raise SystemExit(run())
