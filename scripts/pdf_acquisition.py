"""PRKE Acquire PDF acquisition adapter.

No institutional login/cookies, no paywall circumvention, no formal library edits.
All downloads require an explicit task staging path and real user invocation.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import re
import ipaddress
import socket
import shutil
import uuid
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit, urljoin

MAX_PDF_BYTES = 40 * 1024 * 1024
MAX_METADATA_BYTES = 3 * 1024 * 1024
SAFE_HOSTS = (
    'api.elsevier.com','api.wiley.com','api.openalex.org','api.unpaywall.org',
    'api.springernature.com','link.springer.com','link.springer.com.cn',
    'arxiv.org','export.arxiv.org','www.arxiv.org','static.arxiv.org',
    'europepmc.org','www.ebi.ac.uk','www.europepmc.org',
    'pmc.ncbi.nlm.nih.gov','www.ncbi.nlm.nih.gov','zenodo.org',
    'www.frontiersin.org','frontiersin.org','www.mdpi.com','mdpi.com',
    'onlinelibrary.wiley.com','www.nature.com','nature.com',
    'sciencedirect.com','www.sciencedirect.com','assets-eu.researchsquare.com',
    'www.science.org','science.org', 'api.crossref.org',
    'iopscience.iop.org','biblio.ugent.be',
)
SAFE_SUFFIXES = ('.springer.com','.springernature.com','.copernicus.org',
                 '.frontiersin.org','.wiley.com','.elsevier.com',
                 '.arxiv.org','.ncbi.nlm.nih.gov','.europepmc.org',
                 '.zenodo.org','.amazonaws.com','.cloudfront.net')

class PDFError(Exception): pass

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def doi_normalize(s):
    if not isinstance(s,str): return None
    s=re.sub(r'^(https?://(?:dx\.)?doi\.org/|doi\s*:\s*)','',s.strip(),flags=re.I)
    s=s.rstrip(' .,;')
    return s.lower() if re.fullmatch(r'10\.\d{4,9}/\S+',s,flags=re.I) else None

def safe_task_dir(task_dir):
    p=Path(task_dir).expanduser().resolve()
    if p == Path(p.anchor): raise PDFError('任务目录不可为磁盘根目录')
    if 'manual_inbox' in p.parts or 'verified' in p.parts: raise PDFError('请传入任务根目录而非 PDF 子目录')
    for x in (p,*p.parents):
        if (x/'.obsidian').exists() or (x/'.research-kb').exists():
            raise PDFError('正式知识库下禁止创建 Acquire 暂存')
    return p

def atomic_new_json(dest, data):
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
    return dest

def unique_report(task_dir,prefix):
    return Path(task_dir)/'pdf'/'reports'/(prefix+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json')

def ensure_task_dirs(p):
    for x in ('pdf/manual_inbox','pdf/verified','pdf/reports','pdf/auto'):
        target=p/x
        if target.is_symlink():raise PDFError('任务目录中不允许符号链接: '+x)
        target.mkdir(parents=True,exist_ok=True)

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def safe_id(s): return re.sub(r'[^a-zA-Z0-9_-]','_',str(s))[:70]

def title_norm(s):
    s=unicodedata.normalize('NFKC',str(s)).casefold()
    return re.sub(r'[^\w]+','',s)

def title_tokens(s):
    s=unicodedata.normalize('NFKC',str(s)).casefold()
    return {w for w in re.findall(r'[\w]+',s) if len(w)>2}

def pdf_inspect(path):
    path=Path(path)
    if path.stat().st_size > MAX_PDF_BYTES: return {'status':'OVERSIZE','pages':0,'first_page':'','metadata':{},'reason':'size_limit'}
    with path.open('rb') as f:
        if not f.read(5).startswith(b'%PDF-'):
            return {'status':'INVALID_PDF','pages':0,'first_page':'','metadata':{},'reason':'pdf_signature'}
    try:
        import fitz
    except ImportError:
        return {'status':'UNVERIFIABLE','pages':None,'first_page':'','metadata':{},'reason':'pymupdf_not_installed'}
    try:
        with fitz.open(str(path)) as doc:
            if len(doc)==0: return {'status':'INVALID_PDF','pages':0,'first_page':'','metadata':{},'reason':'empty_pdf'}
            if doc.needs_pass: return {'status':'UNVERIFIABLE','pages':len(doc),'first_page':'','metadata':{},'reason':'encrypted'}
            text=doc[0].get_text(sort=True)[:12000]
            metadata=doc.metadata or {}
            return {'status':'PARSED','pages':len(doc),'first_page':text,'metadata':{k:str(metadata.get(k) or '')[:600] for k in ('title','author','subject','doi')},'reason':'ok' if text.strip() else 'image_only'}
    except Exception:
        return {'status':'INVALID_PDF','pages':None,'first_page':'','metadata':{},'reason':'parser_error'}

def match_paper(pdf, paper):
    if pdf['status']!='PARSED' or not pdf['first_page'].strip():
        return ('UNVERIFIABLE',0.0,pdf['reason'])
    title=paper['title']; first=pdf['first_page'][:9000]
    meta_title=pdf['metadata'].get('title','')
    tokens=title_tokens(title)
    cleaned_first=title_norm(first)
    cleaned_title=title_norm(title)
    contained=len(cleaned_title)>15 and cleaned_title in cleaned_first
    ratio=(len(tokens & title_tokens(first))/len(tokens)) if tokens else 0.0
    meta_ratio=(len(tokens & title_tokens(meta_title))/len(tokens)) if tokens else 0.0
    score=max(1.0 if contained else 0,ratio,meta_ratio)
    expected_doi=doi_normalize(paper.get('doi'))
    first_dois={doi_normalize(x.rstrip('.,;)]}')) for x in re.findall(r'10\.\d{4,9}/[^\s\]<>"\')]+',first[:4500],re.I)}
    first_dois.discard(None)
    # A DOI alone never verifies identity; it might belong to a cited paper.
    if score>=.83 and expected_doi and expected_doi in first_dois:
        return ('VERIFIED',score,'title_and_first_page_doi')
    if score>=.94:
        return ('PROBABLE',score,'title_match_but_doi_unverified')
    if score>=.75:
        return ('REVIEW',score,'partial_title_match')
    return ('NO_MATCH',score,'title_not_established')

def read_candidates(path):
    src=Path(path)
    data=json.loads(src.read_text(encoding='utf-8-sig'))
    if not isinstance(data,dict) or 'papers' not in data or 'task_id' not in data:
        raise PDFError('需要规范的 CandidateSet JSON')
    if not isinstance(data['papers'],list): raise PDFError('papers 必须是列表')
    ids=[x.get('record_id') for x in data['papers']]
    if len(ids)!=len(set(ids)) or any(not s for s in ids): raise PDFError('record_id 重复或缺失')
    return data

def write_pdf_copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as inp, target.open('xb') as out: shutil.copyfileobj(inp,out,1024*1024)

def scan_manual(task_dir, candidates):
    p=safe_task_dir(task_dir);ensure_task_dirs(p)
    papers=[x for x in candidates['papers'] if x.get('screening',{}).get('decision')!='EXCLUDE']
    entries=[]
    for pdf_path in sorted((p/'pdf/manual_inbox').iterdir()):
        if pdf_path.is_symlink() or not pdf_path.is_file() or pdf_path.suffix.lower()!='.pdf':continue
        digest=sha256_file(pdf_path)
        inspection=pdf_inspect(pdf_path)
        scores=[(x,)+match_paper(inspection,x) for x in papers]
        best=sorted(scores,key=lambda x:x[2],reverse=True)
        ok=[x for x in best if x[1]=='VERIFIED']
        selected=ok[0] if len(ok)==1 else None
        state='VERIFIED' if selected else ('AMBIGUOUS' if len(ok)>1 else 'REVIEW_REQUIRED')
        dest=None
        if selected:
            rec_id=safe_id(selected[0]['record_id'])
            outfile=p/'pdf/verified'/(rec_id+'_'+digest[:14]+'.pdf')
            if not outfile.exists():write_pdf_copy(pdf_path,outfile)
            elif sha256_file(outfile)!=digest:raise PDFError('已存在同名但内容不同的文件，禁止覆盖')
            dest=str(outfile)
        entries.append({'original':str(pdf_path),'sha256':digest,'size_bytes':pdf_path.stat().st_size,
                        'status':state,'record_id':selected[0]['record_id'] if selected else None,
                        'verified_copy':dest,'inspection':{'parse_status':inspection['status'],
                        'pages':inspection['pages'],'reason':inspection['reason']},
                        'candidate_matches':[{'record_id':x['record_id'],'verdict':v,'title_score':round(s,3),'reason':r} for x,v,s,r in best[:5]]})
    report={'schema_version':'1.0','task_id':candidates['task_id'],'generated_at':now(),
            'channel':'MANUAL_INBOX','items':entries,'notes':['原始人工文件保持不变','只有首页标题与目标 DOI 均匹配才标记 VERIFIED；无全文可读文字则待核验']}
    target=atomic_new_json(unique_report(p,'manual_import'),report)
    return target,report

def manual_queue(task_dir,candidates):
    p=safe_task_dir(task_dir);ensure_task_dirs(p)
    verified_ids=set()
    for report_file in (p/'pdf/reports').glob('*.json'):
        try:
            saved=json.loads(report_file.read_text(encoding='utf-8'))
            if saved.get('task_id')!=candidates['task_id']:continue
            for item in saved.get('items',[]):
                if item.get('status')=='VERIFIED':
                    path=item.get('verified_copy') or (item.get('file') or {}).get('verified_path')
                    if path and Path(path).is_file() and safe_task_dir(task_dir) in Path(path).resolve().parents:
                        verified_ids.add(item.get('record_id'))
        except (OSError,ValueError):continue
    manifest={'schema_version':'1.0','task_id':candidates['task_id'],'generated_at':now(),
       'items':[{'record_id':x['record_id'],'title':x['title'],'doi':x.get('doi'),
       'publisher_url':x.get('url'),'priority':'HIGH' if 'MUST_READ' in x.get('recommended_for',[]) else 'NORMAL',
       'status':'NEEDS_MANUAL_REVIEW','reason':'尚未确认通过自动途径取得匹配全文；请核对自动获取报告',
       'recommended_action':'使用图书馆或官方授权途径人工下载至 pdf/manual_inbox'}
       for x in candidates['papers'] if x.get('screening',{}).get('decision')!='EXCLUDE' and x['record_id'] not in verified_ids]}
    dest=atomic_new_json(unique_report(p,'manual_queue'),manifest)
    return dest,manifest

def load_keys(env_file=None):
    names=('ELSEVIER_API_KEY','WILEY_API_KEY','TDM_API_TOKEN','SPRINGER_OA_API_KEY','SPRINGER_API_KEY','SPRINGER_META_API_KEY','UNPAYWALL_EMAIL')
    keys={n:os.environ.get(n,'') for n in names}
    filename=Path(env_file).expanduser() if env_file else Path.home()/'.env'
    if filename.is_file():
        for line in filename.read_text(encoding='utf-8-sig').splitlines():
            if '=' not in line or line.strip().startswith('#'):continue
            k,val=line.split('=',1);k=k.strip()
            if k in keys and not keys[k]:keys[k]=val.strip().strip('"\'')
    return keys

def allowed_pdf_url(url):
    try:
        u=urlsplit(url)
        if u.scheme!='https' or not u.hostname or u.username or u.password:return False
        host=u.hostname.lower().rstrip('.')
        if host.replace('.','').isdigit() or host in ('localhost','127.0.0.1','0.0.0.0') or host.startswith('192.168.') or host.startswith('10.') or host.startswith('172.16.'):
            return False
        return host in SAFE_HOSTS or any(host.endswith(s) for s in SAFE_SUFFIXES)
    except ValueError:return False

def check_public_dns(host):
    """Conservative SSRF gate; rejects an entire host if any resolved address is nonpublic."""
    try:
        addresses=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        if not addresses:raise PDFError('DNS_NOT_RESOLVED')
        for info in addresses:
            ip=ipaddress.ip_address(info[4][0])
            if not ip.is_global:raise PDFError('DNS_NONPUBLIC_ADDRESS')
    except OSError as exc:
        raise PDFError('DNS_LOOKUP_FAILED') from exc

def fetch_bytes(url, headers=None, max_bytes=MAX_PDF_BYTES, session=None, timeout=(8,35)):
    if not allowed_pdf_url(url):raise PDFError('UNAPPROVED_DOMAIN: PDF URL not on allowed HTTPS host list')
    try: import requests
    except ImportError as e:raise PDFError('requests 未安装') from e
    ses=session or requests.Session()
    current=url; clean_headers=dict(headers or {})
    for redirects in range(5):
        if session is None:check_public_dns(urlsplit(current).hostname)
        resp=ses.get(current,headers=clean_headers,timeout=timeout,stream=True,allow_redirects=False)
        try:
            if resp.status_code in (301,302,303,307,308):
                nxt=urljoin(current,resp.headers.get('Location',''))
                if not allowed_pdf_url(nxt):raise PDFError('UNAPPROVED_REDIRECT')
                if urlsplit(nxt).hostname!=urlsplit(current).hostname:
                    clean_headers={k:v for k,v in clean_headers.items() if k.lower() not in ('authorization','x-els-apikey','wiley-tdm-client-token')}
                current=nxt;continue
            if resp.status_code in (401,403):raise PDFError('AUTH_OR_ENTITLEMENT_DENIED')
            if resp.status_code==429:raise PDFError('RATE_LIMITED')
            if resp.status_code>=400:raise PDFError('HTTP_'+str(resp.status_code))
            buf=io.BytesIO()
            for chunk in resp.iter_content(chunk_size=65536):
                if not chunk:continue
                if buf.tell()+len(chunk)>max_bytes:raise PDFError('MAX_DOWNLOAD_SIZE')
                buf.write(chunk)
            return buf.getvalue()
        finally:resp.close()
    raise PDFError('TOO_MANY_REDIRECTS')

def fetch_json(url, params=None, headers=None,session=None):
    if not allowed_pdf_url(url):raise PDFError('UNAPPROVED_METADATA_HOST')
    try:import requests
    except ImportError as e:raise PDFError('requests 未安装') from e
    ses=session or requests.Session()
    if session is None:check_public_dns(urlsplit(url).hostname)
    response=ses.get(url,params=params,headers=headers or {},timeout=(8,20),allow_redirects=False,stream=True)
    try:
        if response.status_code!=200:raise PDFError('METADATA_HTTP_'+str(response.status_code))
        raw=bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            if len(raw)+len(chunk)>MAX_METADATA_BYTES:raise PDFError('MAX_METADATA_SIZE')
            raw.extend(chunk)
        return json.loads(raw)
    finally:response.close()

def candidate_urls_from_openalex(doi,session=None,rejected=None):
    if not doi:return []
    info=fetch_json('https://api.openalex.org/works/https://doi.org/'+quote(doi,safe=''),session=session)
    items=[]
    for loc in ([info.get('best_oa_location')] if info.get('best_oa_location') else []) + (info.get('locations') or []):
        if isinstance(loc,dict) and loc.get('pdf_url') and loc.get('is_oa'):
            items.append((loc['pdf_url'],loc.get('version') or 'UNKNOWN','OPENALEX_OA'))
    seen=set();result=[]
    for url,version,provider in items:
        if url in seen:continue
        seen.add(url)
        if allowed_pdf_url(url):result.append((url,version,provider))
        elif rejected is not None:
            u=urlsplit(url)
            rejected.append({'source':provider,'url_without_query':u._replace(query='',fragment='').geturl()[:500],
                             'reason':'UNAPPROVED_DOMAIN_OR_SCHEME'})
    return result

def candidate_urls_from_unpaywall(doi, email, session=None,rejected=None):
    if not (doi and email and '@' in email):return []
    info=fetch_json('https://api.unpaywall.org/v2/'+quote(doi,safe=''),params={'email':email},session=session)
    locations=([info['best_oa_location']] if info.get('best_oa_location') else [])+(info.get('oa_locations') or [])
    seen=set();result=[]
    for loc in locations:
        if not isinstance(loc,dict) or not loc.get('url_for_pdf'):continue
        url=loc['url_for_pdf']
        if url in seen:continue
        seen.add(url)
        if allowed_pdf_url(url):result.append((url,loc.get('version') or 'UNKNOWN','UNPAYWALL_OA'))
        elif rejected is not None:
            u=urlsplit(url)
            rejected.append({'source':'UNPAYWALL_OA','url_without_query':u._replace(query='',fragment='').geturl()[:500],
                             'reason':'UNAPPROVED_DOMAIN_OR_SCHEME'})
    return result

def candidate_urls_from_springer(doi, key, session=None):
    """Springer OA metadata only: never assume JATS/XML is PDF."""
    if not (doi and key and doi.startswith(('10.1007/','10.1186/','10.1038/'))):return []
    info=fetch_json('https://api.springernature.com/openaccess/json',params={'q':'doi:'+doi,'api_key':key},session=session)
    result=[]
    for rec in info.get('records',[]) or []:
        if doi_normalize(rec.get('doi'))!=doi:continue
        for link in rec.get('url',[]) or []:
            if isinstance(link,dict) and str(link.get('format','')).lower()=='pdf' and allowed_pdf_url(link.get('value','')):
                result.append((link['value'],'PUBLISHER_OA','SPRINGER_OA'))
    return result

def validate_pdf_bytes(data):
    # PDF header may be preceded by a few transport bytes; require exact header at start to be conservative
    return data.startswith(b'%PDF-') and b'%%EOF' in data[-2048:]

def store_download(task_root,paper,raw,provider,version,source):
    p=safe_task_dir(task_root);ensure_task_dirs(p)
    rec_id=safe_id(paper['record_id']);digest=hashlib.sha256(raw).hexdigest()
    out=p/'pdf/auto'/(rec_id+'_'+digest[:14]+'.pdf')
    if not out.exists():
        with out.open('xb') as f:f.write(raw)
    elif sha256_file(out)!=digest:raise PDFError('CACHE_HASH_CONFLICT')
    inspected=pdf_inspect(out)
    verdict,score,reason=match_paper(inspected,paper)
    # The auto directory is a quarantine until title+first-page DOI verified.
    verified_path=None
    if verdict=='VERIFIED':
        dst=p/'pdf/verified'/out.name
        if not dst.exists():write_pdf_copy(out,dst)
        verified_path=str(dst)
    return {'provider':provider,'version':version,'source_host':urlsplit(source).hostname,
            'sha256':digest,'size_bytes':len(raw),'raw_path':str(out),'verified_path':verified_path,
            'identity_status':verdict,'title_score':round(score,3),'verification_reason':reason}

def auto_fetch(task_dir,candidates,limit=10,execute=False,env_file=None,session=None):
    p=safe_task_dir(task_dir);ensure_task_dirs(p)
    keys=load_keys(env_file) if execute else {};items=[]
    selection=[x for x in candidates['papers'] if x.get('screening',{}).get('decision')=='INCLUDE'][:limit]
    for paper in selection:
        record={'record_id':paper['record_id'],'doi':paper.get('doi'),'status':'PLAN_ONLY' if not execute else 'NOT_ACQUIRED','attempts':[],'filtered_urls':[],'file':None}
        doi=doi_normalize(paper.get('doi'))
        if not doi:record['status']='NEEDS_MANUAL_REVIEW';record['reason']='NO_VALID_DOI';items.append(record);continue
        if not execute:
            record['planned_sources']=['OPENALEX_OA','UNPAYWALL_OA (if email configured)','SPRINGER_OA (publisher prefix only)','ELSEVIER_API','WILEY_TDM_API']
            items.append(record);continue
        urls=[]
        for provider,action in [('OPENALEX_OA',lambda:candidate_urls_from_openalex(doi,session,record['filtered_urls'])),
                               ('UNPAYWALL_OA',lambda:candidate_urls_from_unpaywall(doi,keys['UNPAYWALL_EMAIL'],session,record['filtered_urls'])),
                               ('SPRINGER_OA',lambda:candidate_urls_from_springer(doi,keys['SPRINGER_OA_API_KEY'],session))]:
            try:urls+=action()
            except Exception as e:record['attempts'].append({'source':provider,'status':'FAILED','reason':(str(e)[:70] if isinstance(e,PDFError) else type(e).__name__)})
        proposals=[(name,url,ver,{}) for url,ver,name in urls]
        if doi.startswith('10.1016/') and keys['ELSEVIER_API_KEY']:
            proposals.append(('ELSEVIER_API','https://api.elsevier.com/content/article/doi/'+quote(doi,safe=''),'PUBLISHER_VERSION',{'X-ELS-APIKey':keys['ELSEVIER_API_KEY'],'Accept':'application/pdf'}))
        if (doi.startswith(('10.1002/','10.1111/','10.1029/'))) and (keys['WILEY_API_KEY'] or keys['TDM_API_TOKEN']):
            proposals.append(('WILEY_TDM_API','https://api.wiley.com/onlinelibrary/tdm/v1/articles/'+quote(doi,safe=''),'PUBLISHER_VERSION',{'Wiley-TDM-Client-Token':keys['TDM_API_TOKEN'] or keys['WILEY_API_KEY']}))
        for name,url,ver,headers in proposals:
            try:
                raw=fetch_bytes(url,headers=headers,session=session)
                if not validate_pdf_bytes(raw):raise PDFError('NON_PDF_OR_INCOMPLETE_RESPONSE')
                info=store_download(p,paper,raw,name,ver,url)
                record['file']=info
                record['attempts'].append({'source':name,'status':'DOWNLOADED','identity':info['identity_status']})
                record['status']='VERIFIED' if info['identity_status']=='VERIFIED' else 'IDENTITY_REVIEW_REQUIRED'
                # Do not keep downloading after a real PDF is acquired but identity needs review.
                break
            except Exception as e:
                record['attempts'].append({'source':name,'status':'FAILED','reason':(str(e)[:70] if isinstance(e,PDFError) else type(e).__name__)})
        if not record['file']:
            record['status']='NEEDS_MANUAL_REVIEW'
        items.append(record)
    report={'schema_version':'1.0','task_id':candidates['task_id'],'generated_at':now(),
            'channel':'AUTO_FETCH','execute':execute,'items':items,
            'notes':['只有 VERIFIED 可自动交付后续模块','不使用机构浏览器、Cookie、受限镜像；不改动正式库']}
    out=atomic_new_json(unique_report(p,'auto_fetch'),report)
    return out,report
