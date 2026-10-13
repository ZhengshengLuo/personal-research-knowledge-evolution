"""PRKE Organize v1.4: local, read-only Zotero and narrowly authorized Obsidian commits.
No automatic access to the user's real Vault. Requires explicit init/commit operations.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, sys, tempfile, uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.error import URLError, HTTPError

ROOT=Path(__file__).resolve().parents[1]
BEGIN='<!-- PRKE:AI-MANAGED:BEGIN -->'
END='<!-- PRKE:AI-MANAGED:END -->'
SECTIONS=('Workspaces','Topics/领域知识','Topics/科学问题','Papers','Readings','Methods','Data','Ideas','Assets/Figures','Templates')
SOURCE_FILES=('source_bundle.json','reading_record.json','reading_audit.json','figure_inventory.json','claim_evidence_matrix.json')
class OrganizeError(Exception):pass

def utc():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def sha(data):return hashlib.sha256(data).hexdigest()
def file_sha(path):return sha(Path(path).read_bytes())
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def dump(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
def new_file(path,txt):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(txt)
def safe_task(path,vault=None):
    p=Path(path).expanduser().resolve()
    if p==Path(p.anchor):raise OrganizeError('拒绝磁盘根目录作为任务区')
    if vault and (p==vault or vault in p.parents or p in vault.parents):raise OrganizeError('任务区必须与 Vault 分离')
    for x in (p,*p.parents):
        if (x/'.obsidian').exists():raise OrganizeError('任务区不得位于 Obsidian Vault 中')
    return p

def vault_path(path,must_exist=True):
    v=Path(path).expanduser().resolve()
    if v==Path(v.anchor):raise OrganizeError('拒绝磁盘根目录作为 Vault')
    if must_exist and not (v/'.obsidian').is_dir():raise OrganizeError('不是已初始化的 Obsidian Vault，先 init-vault')
    return v

def inside(base,rel):
    if Path(rel).is_absolute() or '\\' in str(rel):raise OrganizeError('仅允许 Vault 内相对 POSIX 路径')
    p=(base/rel).resolve()
    if base not in p.parents:raise OrganizeError('检测到路径越界或符号链接')
    return p

def doi_norm(doi):
    doi=(doi or '').strip().lower()
    doi=re.sub(r'^https?://(?:dx\.)?doi\.org/','',doi)
    doi=re.sub(r'^doi:\s*','',doi)
    if doi and not re.fullmatch(r'10\.\d{4,9}/\S+',doi):raise OrganizeError('DOI 格式不正确')
    return doi

def paper_uid(source):
    d=doi_norm(source['source'].get('doi'))
    basis=('doi:'+d) if d else ('source:'+source['source']['sha256'])
    return 'paper-'+sha(basis.encode('utf-8'))[:16]

def safe_stem(stem):
    stem=re.sub(r'\s+',' ',stem).strip().rstrip('. ')
    if not stem or len(stem)>110 or re.search(r'[\\/:*?"<>|\x00-\x1f]',stem) or stem.upper() in ('CON','PRN','AUX','NUL') or stem in ('.','..'):
        raise OrganizeError('不安全的论文笔记文件名')
    return stem

def q(value):return json.dumps(value,ensure_ascii=False)
def frontmatter(uid,source,record,audit,zkey='',zlibrary=''):
    s=source['source']; doi=doi_norm(s.get('doi'))
    return '\n'.join(['---','asset_type: paper_note','cssclasses: [prke-academic]',f'paper_uid: {q(uid)}',f'title: {q(s.get("title") or record["paper_id"])}',f'doi: {q(doi)}',f'primary_type: {q(record["primary_type"])}',f'reading_depth: {q(record["depth"])}',f'reading_audit: {q(audit["status"])}',f'source_sha256: {q(s["sha256"])}',f'zotero_item_key: {q(zkey)}',f'zotero_library: {q(zlibrary)}',f'zotero_status: {"LINKED" if zkey and zlibrary else "ZOTERO_PENDING"}','---'])

def ref_claim(c):
    return '；'.join(f'{r["source_kind"]} PDF p.{r.get("page") or "?"} {r.get("figure_id") or r.get("locator") or ""}'.strip() for r in c['source_refs'])

def formatted_paper(uid,source,record,fig,claims,audit,stem,zkey='',zlibrary=''):
    cs=claims['claims'];core=[c for c in cs if c.get('central')] or cs
    chain=record['argument_chain'];title=source['source'].get('title') or record['paper_id']
    rl=f'[[{stem} - 精读]]' if record['depth']=='DEEP' and audit['status']=='COMPLETED' else '未完成正式精读'
    zot=f'Zotero Item Key：`{zkey}`（{zlibrary}）' if zkey and zlibrary else 'Zotero 待关联，未伪造链接'
    body='\n'.join([
      f'# {title}','', '> [!abstract] 核心认识', f'> {chain.get("conclusion") or "本次阅读尚未形成经过核验的综合认识。"}', '',
      '## 科学问题与研究设计', '',chain.get('problem') or '尚未完成核验。', '',chain.get('approach') or '',
      '', '## 核心发现与证据', '',*([f'- **{c["claim_id"]} · {c["role"]}**：{c["claim"]}（{ref_claim(c)}；{c["assessment"]}）' for c in core[:5]] or ['- 尚未提供可追溯主张。']),
      '', '## 关键局限与批判性判断', '', *([f'- {a["verdict"]}：{a["reasoning"]}' for a in record['critical_appraisal'][:3]] or ['- 暂无已核验的批判性评价。']),
      '', '## 对科研的价值', '',*([f'- {x}' for x in record['takeaways'][:4]] or ['- 尚待研究者评估。']),
      '', '## 关联与来源', '',f'- 精读笔记：{rl}',f'- {zot}',f'- 原始 DOI：{source["source"].get("doi") or "未提供"}',f'- 阅读审计：`{audit["status"]}`（软件结构审计不等于独立科学复核）','',
      '> [!info] 知识链接', '> Workspace / Topic / Method / Data 仅在确认后增补真实 WikiLinks；不会生成虚构节点。'
    ])
    return frontmatter(uid,source,record,audit,zkey,zlibrary)+'\n\n'+BEGIN+'\n'+body+'\n'+END+'\n\n## 我的思考与批注（人工维护，PRKE 不覆盖）\n\n'

def formatted_reading(uid,source,record,fig,claims,audit,stem):
    chain=record['argument_chain'];title=source['source'].get('title') or record['paper_id']
    labels={'problem':'研究问题','prior_limitation':'现有研究不足','approach':'数据与研究方案','mechanism':'机制与方法逻辑','results':'核心研究结果','conclusion':'结论及适用边界'}
    parts=[f'# {title} · 完整精读','',f'> [!info] 原文来源和核验状态',f'> 对应 [[{stem}]]；PDF SHA-256 `{source["source"]["sha256"]}`；审核状态 **{audit["status"]}**。原文 Figure/页码均指实际 PDF。','',
           '## 科学论证与研究逻辑','']
    for k,l in labels.items():parts.extend([f'### {l}',chain.get(k) or '尚未整理。',''])
    parts.extend(['## 类型专项深入理解',''])
    for k,val in record['type_specific'].items():
        if val.strip():parts.extend([f'### {k}',val,''])
    parts.extend(['## 关键图表与原始证据','', '> [!important] 原图规则', '> 以下引用 PDF 原图视觉核验记录。未提供经过复查的单独裁切图时，不自动插入可能误配的图片。',''])
    for f in fig['items']:
        parts.extend([f'### {f["label"]} · PDF p.{f.get("page") or "?"}',f'**核验状态：{f["status"]}**。{f.get("visual_observation") or "尚未视觉核验。"}',''])
    parts.extend(['## 科学主张与原文证据',''])
    for c in claims['claims']:
        parts.extend([f'### {c["claim_id"]} · {c["claim"]}',f'- 类型：`{c["role"]}`；评价：`{c["assessment"]}`',f'- 来源：{ref_claim(c)}',f'- 直接证据：{c["evidence_summary"]}',f'- 边界与分析：{c["reasoning"]}',''])
    parts.extend(['## 批判性科学评价',''])
    for a in record['critical_appraisal']:parts.extend([f'### {a["issue_id"]} · {a["question"]}',f'**{a["verdict"]}**。{a["reasoning"]}；依据：{", ".join(a["source_claim_ids"])}',''])
    if record.get('user_annotations'):
        parts.extend(['## Understand 交接的研究者原始批注（USER_ORIGIN，保留文字）',''])
        parts.extend(['> [!warning] 来源', '> 以下是已有研究者文字，不等于作者原文结论。',''])
        parts.extend([f'- {x}' for x in record['user_annotations']])
        parts.append('')
    parts.extend(['## 研究价值、局限与待解问题',''])
    for h,v in [('主要收获',record['takeaways']),('作者报告的局限',record['author_limitations']),('Agent 评估的局限',record['agent_limitations']),('待解决问题',record['unresolved_questions'])]:
        parts.extend([f'### {h}',*([f'- {x}' for x in v] or ['- 暂无']), ''])
    return '\n'.join(['---','asset_type: deep_reading','cssclasses: [prke-academic]',f'paper_uid: {q(uid)}',f'reading_audit: {q(audit["status"])}','---','',BEGIN,*parts,END,'','## 我的推导与科研思考（人工维护，PRKE 不覆盖）','','## 我的 Zotero 精选批注（保留原文与来源）','',''])

def get_understand(p):
    p=Path(p).expanduser().resolve()
    for f in SOURCE_FILES:
        if not (p/f).is_file():raise OrganizeError('Understand 交接资料缺失: '+f)
    src,rec,au,fig,claims=(load(p/f) for f in SOURCE_FILES)
    if len({src['paper_id'],rec['paper_id'],au['paper_id'],fig['paper_id'],claims['paper_id']})!=1:raise OrganizeError('Understand Paper ID 不一致')
    sourcepdf=Path(src['source']['pdf_path'])
    if not sourcepdf.is_file() or file_sha(sourcepdf)!=src['source']['sha256']:raise OrganizeError('PDF 哈希或路径变化，拒绝交接')
    # Import the actual v1.3.0 scientific structure gate, do not trust saved audit label.
    from understand.engine import audit as verify
    checked=verify(p)
    if checked['status']!='BLOCKED' and au['status']=='COMPLETED' and checked['status']!='COMPLETED':raise OrganizeError('保存的 COMPLETED 与重新审计不一致')
    if checked['status']=='BLOCKED':raise OrganizeError('Understand 审计 BLOCKED，禁止入库')
    return p,src,rec,checked,fig,claims

def managed(s):
    if s.count(BEGIN)!=1 or s.count(END)!=1 or s.index(BEGIN)>s.index(END):raise OrganizeError('受管标记缺失/重复，拒绝覆盖用户文件')
    return s[s.index(BEGIN):s.index(END)+len(END)]

def patch(old,new):
    a=old.index(BEGIN);b=old.index(END)+len(END)
    prefix=old[:a]
    replacement=new[:new.index(BEGIN)]
    # Update only PRKE-owned YAML properties; retain any additional user metadata.
    for key in ('reading_audit','reading_depth','source_sha256','zotero_item_key','zotero_library','zotero_status'):
        new_match=re.search(r'^'+re.escape(key)+r': .*$',replacement,re.M)
        if new_match and re.search(r'^'+re.escape(key)+r': .*$',prefix,re.M):
            prefix=re.sub(r'^'+re.escape(key)+r': .*$',lambda _:new_match.group(),prefix,count=1,flags=re.M)
    return prefix+managed(new)+old[b:]

def init_vault(args):
    v=vault_path(args.vault,False)
    if not (args.execute and args.acknowledge_empty_vault):
        print('PLAN_ONLY: 将在所选位置创建一个空白 Vault，不会导入旧模板：',v);return
    if v.exists() and any(v.iterdir()):raise OrganizeError('目标目录非空；为了避免误覆盖，不支持在此初始化')
    v.mkdir(parents=True,exist_ok=True)
    (v/'.obsidian').mkdir(exist_ok=False)
    for s in SECTIONS:(v/s).mkdir(parents=True,exist_ok=True)
    (v/'.prke').mkdir(exist_ok=True)
    new_file(v/'Home.md','# Research Knowledge Base\n\n> PRKE 个人科研知识库。知识只在经过授权后写入。\n\n- [[Workspaces]] 与 [[Topics]] 是知识组织层，实际节点待真实科研任务建立。\n')
    new_file(v/'.prke'/'index.json',dump({'schema_version':'1.0','papers':{},'updated_at':utc()}))
    for f in (ROOT/'templates'/'obsidian').glob('*.md'):
        new_file(v/'Templates'/f.name, f.read_text(encoding='utf-8'))
    snippet=ROOT/'templates'/'obsidian'/'css'/'prke-hybrid.css'
    if snippet.is_file():new_file(v/'.obsidian'/'snippets'/'prke-hybrid.css',snippet.read_text(encoding='utf-8'))
    print('VAULT_INITIALIZED:',v)

def doctor(args):
    reg=load(ROOT/'router/interfaces/module-registry.json')
    if reg['modules']['organize']['status']!='INSTRUCTION_READY':raise OrganizeError('Organize 路由尚未注册')
    if not (ROOT/'routes'/'organize.md').exists():raise OrganizeError('缺 Organize 阅读合同')
    if not (ROOT/'templates'/'obsidian'/'Paper Note.md').exists():raise OrganizeError('缺内置模板')
    print('PASS: Organize local adapter ready; Zotero connection and Vault write NOT checked')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

def zotero_fetch(suffix):
    # localhost direct: do not follow redirects, don't inherit HTTP(S)_PROXY.
    base='http://127.0.0.1:23119/api/'
    opener=build_opener(ProxyHandler({}),NoRedirect())
    req=Request(base+suffix,headers={'Zotero-API-Version':'3','Accept':'application/json'},method='GET')
    with opener.open(req,timeout=5) as r:
        data=r.read(2*1024*1024+1)
        if len(data)>2*1024*1024:raise OrganizeError('Zotero 响应过大')
        return data,r.headers

def zotero_probe(args):
    try:
        try:root,headers=zotero_fetch('')
        except HTTPError as e:
            if e.code!=404:raise
            root=b'';headers={}
        items_raw,item_headers=zotero_fetch('users/0/items/top?limit='+str(args.limit))
        items=json.loads(items_raw.decode('utf-8'))
        if not isinstance(items,list):raise OrganizeError('本地 API 返回非列表')
        samples=[]
        for x in items[:args.limit]:
            d=x.get('data',{});key=x.get('key') or d.get('key')
            if not key:continue
            children=[]
            if args.children:
                from urllib.parse import quote
                try:
                    raw,_=zotero_fetch('users/0/items/'+quote(key,safe='')+'/children?limit=30')
                    children=[{'item_type':v.get('data',{}).get('itemType'),'key':v.get('key'),'parent_key':v.get('data',{}).get('parentItem')} for v in json.loads(raw.decode('utf-8')) if v.get('data',{}).get('itemType') in ('attachment','annotation','note')]
                except (URLError,ValueError):children=[{'error':'CHILDREN_UNAVAILABLE'}]
            samples.append({'title':d.get('title'), 'doi':d.get('DOI'),'item_key':key,'collections':d.get('collections',[]),'library':x.get('library',{}).get('id'),'attachments_or_annotations':children})
        result={'connection':'CONNECTED_READONLY','api_version':item_headers.get('Zotero-API-Version') or headers.get('Zotero-API-Version'), 'sample_count':len(samples),'samples':samples,'zotero_write_attempts':0}
        print(dump(result))
    except (URLError,HTTPError,ValueError) as e:
        raise OrganizeError('Zotero 本机 API 无法实际读取（请启动 Zotero、启用本地 API、检查 23119）：'+str(e)) from e

def verify_zotero_item(library,key,source):
    if not re.fullmatch(r'(users/0|groups/[0-9]+)',library):
        raise OrganizeError('Zotero 库标识只接受 users/0 或 groups/<numeric-id>')
    if not re.fullmatch(r'[A-Z0-9]{8}',key.upper()):raise OrganizeError('Zotero Item Key 格式非法')
    try:
        raw,_=zotero_fetch(library+'/items/'+key.upper())
        item=json.loads(raw.decode('utf-8'));data=item.get('data',{})
        item_doi=doi_norm(data.get('DOI'));source_doi=doi_norm(source['source'].get('doi'))
        if source_doi and item_doi!=source_doi:
            raise OrganizeError('Zotero 条目 DOI 与 Understand 原文不符')
        if not source_doi:
            title=lambda s:re.sub(r'[^\w]+','',str(s).lower())
            if title(data.get('title'))!=title(source['source'].get('title')):
                raise OrganizeError('没有 DOI 时 Zotero 标题必须完全规范化匹配')
        if data.get('itemType') in ('attachment','annotation','note'):
            raise OrganizeError('关联对象不是 Zotero 顶层论文条目')
    except (URLError,HTTPError,ValueError) as e:
        raise OrganizeError('无法验证 Zotero 真实条目身份，改为 ZOTERO_PENDING 后重试：'+str(e)) from e

def stage_paper(args):
    v=vault_path(args.vault);task=safe_task(args.stage_dir,v)
    if task.exists() and any(task.iterdir()):raise OrganizeError('暂存目录非空：为避免覆盖旧计划，请换新目录')
    paper,src,record,audit,fig,claims=get_understand(args.paper_dir)
    uid=paper_uid(src);doi=doi_norm(src['source'].get('doi'))
    index=load(v/'.prke'/'index.json')
    old=index['papers'].get(uid)
    if old and old['doi']!=doi:raise OrganizeError('论文身份冲突，停止')
    if old and old.get('source_sha256')!=src['source']['sha256']:
        raise OrganizeError('同 DOI 的 PDF 版本发生变化，必须人工审查版本关系后再入库；不能自动覆盖旧证据')
    stem=safe_stem(args.stem) if args.stem else (old['stem'] if old else safe_stem((src['source'].get('title') or record['paper_id'])[:70]+' - '+uid[-6:]))
    if old and stem!=old['stem']:raise OrganizeError('既有论文不能随意改文件名，避免重复笔记')
    zkey=(args.zotero_item_key or (old or {}).get('zotero_item_key') or '').strip()
    zlibrary=(args.zotero_library or (old or {}).get('zotero_library') or '').strip()
    if bool(zkey)!=bool(zlibrary):raise OrganizeError('Zotero library/key 必须成对提供（不能伪造链接）')
    if zkey:verify_zotero_item(zlibrary,zkey,src)
    p_rel='Papers/'+stem+'.md'; r_rel='Readings/'+stem+' - 精读.md'
    result=[(p_rel,formatted_paper(uid,src,record,fig,claims,audit,stem,zkey,zlibrary))]
    if audit['status']=='COMPLETED' and record['depth']=='DEEP':result.append((r_rel,formatted_reading(uid,src,record,fig,claims,audit,stem)))
    elif audit['status']=='PARTIAL' and not args.allow_partial:raise OrganizeError('Understand 为 PARTIAL；必须显式 --allow-partial，且仅生成 Paper Note')
    files=[];task.mkdir(parents=True,exist_ok=False);(task/'drafts').mkdir();(task/'source_snapshot').mkdir()
    for rel,content in result:
        target=inside(v,rel)
        if target.exists():
            if not old or old['paper_rel']!=p_rel:raise OrganizeError('目标已有文件但没有受管理的论文身份，拒绝覆盖')
            existing=target.read_text(encoding='utf-8'); prev=old.get('managed_sha',{}).get(rel)
            if not prev or sha(managed(existing).encode('utf-8'))!=prev:raise OrganizeError('已有受管内容被人工编辑；停止自动合并')
            content=patch(existing,content);mode='UPDATE';base=file_sha(target)
        else:mode='CREATE';base=None
        name='drafts/'+('paper.md' if rel.startswith('Papers/') else 'reading.md')
        new_file(task/name,content)
        files.append({'target_rel':rel,'draft_rel':name,'mode':mode,'base_sha256':base,'draft_sha256':sha(content.encode('utf-8'))})
    snapshot=[]
    for f in SOURCE_FILES:
        payload=(paper/f).read_bytes()
        (task/'source_snapshot'/f).write_bytes(payload)
        snapshot.append({'file':f,'sha256':sha(payload),'target_rel':'.prke/evidence/'+uid+'/'+f,'base_sha256':file_sha(inside(v,'.prke/evidence/'+uid+'/'+f)) if inside(v,'.prke/evidence/'+uid+'/'+f).exists() else None})
    plan={'schema_version':'1.0','batch_id':str(uuid.uuid4()),'created_at':utc(),'vault':str(v),'paper_dir':str(paper),'paper_uid':uid,'paper_id':src['paper_id'],'doi':doi,'stem':stem,'source_sha256':src['source']['sha256'],'reading_status':audit['status'],'reading_depth':record['depth'],'zotero_library':zlibrary,'zotero_item_key':zkey,'files':files,'snapshots':snapshot,'index_base_sha256':file_sha(v/'.prke'/'index.json'),'operation':'CREATE_OR_SAFE_UPDATE','permission':'PENDING_USER_BATCH_APPROVAL'}
    new_file(task/'plan.json',dump(plan))
    digest=file_sha(task/'plan.json')
    print('STAGED:',task,'\nPLAN_SHA256:',digest,'\nFILES:',[(f['mode'],f['target_rel']) for f in files],'\nNO VAULT WRITES')

def commit(args):
    task=Path(args.stage_dir).expanduser().resolve();plan_path=task/'plan.json';plan=load(plan_path)
    v=vault_path(args.vault)
    if str(v)!=plan['vault']:raise OrganizeError('当前 Vault 不匹配原计划')
    safe_task(task,v)
    if not args.acknowledge_vault_write or file_sha(plan_path)!=args.approve_plan_sha256:
        raise OrganizeError('需实际核对 plan/diff 并显式提供其 SHA-256 与写入确认参数')
    idxpath=v/'.prke'/'index.json'
    if file_sha(idxpath)!=plan['index_base_sha256']:raise OrganizeError('索引自预览以来已变化，请重新预览')
    for info in plan['snapshots']:
        if file_sha(task/'source_snapshot'/info['file'])!=info['sha256']:raise OrganizeError('来源快照被修改')
        if not (Path(plan['paper_dir'])/info['file']).is_file() or file_sha(Path(plan['paper_dir'])/info['file'])!=info['sha256']:
            raise OrganizeError('源 Understand 审读记录自预览后变化，请重新预览')
    pp=Path(plan['paper_dir']);src=load(task/'source_snapshot'/'source_bundle.json')
    if not Path(src['source']['pdf_path']).is_file() or file_sha(src['source']['pdf_path'])!=plan['source_sha256']:
        raise OrganizeError('源 PDF 发生变化，拒绝提交')
    files=[]
    for f in plan['files']:
        target=inside(v,f['target_rel']);draft=(task/f['draft_rel']).resolve()
        if task not in draft.parents or file_sha(draft)!=f['draft_sha256']:raise OrganizeError('草稿哈希已变')
        current=file_sha(target) if target.exists() else None
        if current!=f['base_sha256']:raise OrganizeError('目标文件自预览后已变化，拒绝提交：'+f['target_rel'])
        files.append((f,target,draft.read_bytes()))
    # Long-term evidence snapshots live inside the hidden Vault sidecar, not the staging folder.
    for info in plan['snapshots']:
        target=inside(v,info['target_rel'])
        actual=file_sha(target) if target.exists() else None
        if actual!=info['base_sha256']:raise OrganizeError('证据侧文件自预览后变化，请重新预览')
        files.append(({'target_rel':info['target_rel'],'draft_sha256':info['sha256']},target,(task/'source_snapshot'/info['file']).read_bytes()))
    # Backup first, then write-ahead receipt. In case of failure, restore all changed files.
    backups=task/'backups';backups.mkdir(exist_ok=False)
    original={}
    for i,(f,target,blob) in enumerate(files):
        original[str(target)]=target.read_bytes() if target.exists() else None
        if target.exists():(backups/(str(i)+'.bak')).write_bytes(original[str(target)])
    original[str(idxpath)]=idxpath.read_bytes();(backups/'index.bak').write_bytes(original[str(idxpath)])
    journal={'batch_id':plan['batch_id'],'plan_sha256':file_sha(plan_path),'state':'PREPARING','created_at':utc(),'files':[f['target_rel'] for f,_,_ in files]}
    new_file(task/'commit_receipt.json',dump(journal))
    def atomic(target,payload):
        target.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(dir=target.parent,prefix='.prke-',suffix='.tmp')
        try:
            with os.fdopen(fd,'wb') as h:h.write(payload);h.flush();os.fsync(h.fileno())
            os.replace(tmp,target)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    def receipt(state):
        journal['state']=state;journal['updated_at']=utc();atomic(task/'commit_receipt.json',dump(journal).encode('utf-8'))
    try:
        receipt('WRITING')
        for f,target,blob in files:atomic(target,blob)
        idx=load(idxpath);managed_sha={f['target_rel']:sha(managed(blob.decode('utf-8')).encode('utf-8')) for f,_,blob in files if f['target_rel'].endswith('.md')}
        previous=idx['papers'].get(plan['paper_uid'],{})
        managed_sha={**previous.get('managed_sha',{}),**managed_sha}
        idx['papers'][plan['paper_uid']]={'doi':plan['doi'],'paper_id':plan['paper_id'],'stem':plan['stem'],'paper_rel':next(f['target_rel'] for f,_,_ in files if f['target_rel'].startswith('Papers/')),'reading_rel':next((f['target_rel'] for f,_,_ in files if f['target_rel'].startswith('Readings/')),previous.get('reading_rel')),'managed_sha':managed_sha,'source_sha256':plan['source_sha256'],'zotero_library':plan['zotero_library'],'zotero_item_key':plan['zotero_item_key'],'updated_at':utc()}
        idx['updated_at']=utc();atomic(idxpath,dump(idx).encode('utf-8'))
        for f,target,blob in files:
            if file_sha(target)!=f['draft_sha256']:raise OrganizeError('提交后文件校验失败')
        receipt('COMMITTED')
        print('COMMITTED:',plan['batch_id'],'\nVAULT:',v,'\nFILES:',len(files),'\nZOTERO WRITES: 0')
    except Exception:
        try:
            for path,data in original.items():
                target=Path(path)
                if data is None:target.unlink(missing_ok=True)
                else:atomic(target,data)
            receipt('ROLLED_BACK')
        except Exception:receipt('NEEDS_RECOVERY')
        raise

def main(argv=None):
    p=argparse.ArgumentParser(description='PRKE Organize v1.4.0 M1/M2 — Zotero READ-ONLY, Obsidian batch-approved')
    sub=p.add_subparsers(dest='command',required=True)
    x=sub.add_parser('doctor');x.set_defaults(func=doctor)
    x=sub.add_parser('zotero-probe');x.add_argument('--limit',type=int,choices=range(1,6),default=3);x.add_argument('--children',action='store_true');x.set_defaults(func=zotero_probe)
    x=sub.add_parser('init-vault');x.add_argument('--vault',required=True);x.add_argument('--execute',action='store_true');x.add_argument('--acknowledge-empty-vault',action='store_true');x.set_defaults(func=init_vault)
    x=sub.add_parser('stage-paper');x.add_argument('--paper-dir',required=True);x.add_argument('--vault',required=True);x.add_argument('--stage-dir',required=True);x.add_argument('--stem');x.add_argument('--allow-partial',action='store_true');x.add_argument('--zotero-library');x.add_argument('--zotero-item-key');x.set_defaults(func=stage_paper)
    x=sub.add_parser('commit');x.add_argument('--stage-dir',required=True);x.add_argument('--vault',required=True);x.add_argument('--approve-plan-sha256',required=True);x.add_argument('--acknowledge-vault-write',action='store_true');x.set_defaults(func=commit)
    a=p.parse_args(argv)
    try:a.func(a);return 0
    except (OrganizeError,PermissionError,OSError,ValueError,KeyError,IndexError) as e:
        print('ERROR:',str(e),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
