"""Conservative offline paper identity resolution; NEVER silently merge versions.

The registry is a task-local candidate index, not a Vault or Zotero database.
Exact DOI/arXiv identifiers nominate matches; differing PDF hashes require
version review, and fuzzy title similarity never auto merges records.
"""
from __future__ import annotations
import argparse,json,re,sys,uuid
from pathlib import Path
from execution_core import safe_workspace, atomic_new
class IdentityError(ValueError):pass
DOI_PREFIX=re.compile(r'^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)',re.I)
DOI=re.compile(r'^10\.\d{4,9}/\S+$',re.I)
HEX=re.compile(r'^[a-f0-9]{64}$')

def normalize_doi(value):
    if not value:return None
    if not isinstance(value,str):raise IdentityError('DOI 必须是字符串')
    v=DOI_PREFIX.sub('',value.strip()).strip().lower()
    if not DOI.fullmatch(v):raise IdentityError('DOI 格式不合法')
    return v

def normalize_record(record):
    if not isinstance(record,dict):raise IdentityError('paper record 非法')
    r=dict(record);r['doi']=normalize_doi(record.get('doi'))
    if not r.get('doi') and not r.get('arxiv_id') and not r.get('pdf_sha256') and not r.get('zotero_key'):
        raise IdentityError('至少需要 DOI、arXiv、PDF SHA 或已核验的 Zotero 来源')
    if r.get('pdf_sha256') and (not isinstance(r['pdf_sha256'],str) or not HEX.fullmatch(r['pdf_sha256'])):
        raise IdentityError('PDF SHA-256 无效')
    if r.get('zotero_key') and not r.get('zotero_library'):
        raise IdentityError('Zotero Key 必须限定 Library')
    if r.get('arxiv_id') and not re.fullmatch(r'(?:\d{4}\.\d{4,5}(?:v\d+)?|[a-zA-Z.-]+/\d{7}(?:v\d+)?)',r['arxiv_id']):
        raise IdentityError('arXiv ID 无效')
    return r

def resolve(registry,record):
    r=normalize_record(record)
    rows=registry.setdefault('papers',[])
    ids=[x.get('paper_uid') for x in rows]
    if len(ids)!=len(set(ids)):raise IdentityError('身份索引已有重复内部 Paper UID')
    candidates=[]
    for p in rows:
        reasons=[]
        if r.get('doi') and p.get('doi')==r['doi']:reasons.append('SAME_DOI')
        if r.get('arxiv_id') and p.get('arxiv_id')==r['arxiv_id']:reasons.append('SAME_ARXIV')
        if r.get('pdf_sha256') and p.get('pdf_sha256')==r['pdf_sha256']:reasons.append('SAME_PDF_BYTES')
        if r.get('zotero_key') and r.get('zotero_library') and (p.get('zotero_key'),p.get('zotero_library'))==(r['zotero_key'],r['zotero_library']):reasons.append('SAME_ZOTERO_ITEM')
        if reasons:candidates.append((p,reasons))
    if len(candidates)>1:return {'decision':'IDENTITY_CONFLICT','candidates':[c[0]['paper_uid'] for c in candidates], 'reason':'相同输入引用多个不同现有 Paper UID，禁止自动合并'}
    if candidates:
        old,reasons=candidates[0]
        if (r.get('pdf_sha256') and old.get('pdf_sha256') and r['pdf_sha256']!=old['pdf_sha256']):
            return {'decision':'VERSION_REVIEW_REQUIRED','paper_uid':old['paper_uid'],'matched_on':reasons,'reason':'外部身份相同但 PDF 版本内容不同，需核查预印本、正式版或修订'}
        if (r.get('doi') and old.get('doi') and r['doi']!=old['doi']):
            return {'decision':'IDENTITY_CONFLICT','paper_uid':old['paper_uid'],'reason':'PDF/其他身份匹配，但 DOI 不同'}
        return {'decision':'EXACT_IDENTITY_MATCH','paper_uid':old['paper_uid'],'matched_on':reasons}
    # Title similarity cannot silently create a duplicate or merge into same paper.
    title=str(r.get('title','')).strip().casefold()
    if title:
        potential=[p['paper_uid'] for p in rows if title==str(p.get('title','')).strip().casefold() and title]
        if potential:return {'decision':'POSSIBLE_DUPLICATE_REVIEW','candidates':potential,'reason':'题名相同仅作为候选，不可自动合并'}
    uid='paper-'+uuid.uuid4().hex[:20]
    rows.append({'paper_uid':uid,**r})
    return {'decision':'NEW_IDENTITY_CANDIDATE','paper_uid':uid,'reason':'新增库外候选，仅建立身份索引并未完成科研核验'}

def write_index(index,reg,expected_sha=None):
    """Atomic task-local update. Advisory lock prevents two PRKE writers colliding.
    Does not protect against arbitrary external editors; do not store in Vault.
    """
    import os, tempfile
    lock=index.with_name(index.name+'.lock')
    try:fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise IdentityError('身份注册任务已有执行者或遗留锁，拒绝并发')
    os.close(fd)
    try:
        from execution_core import sha
        actual=sha(index) if index.exists() else None
        if actual!=expected_sha:raise IdentityError('身份注册表在读取后发生变化，拒绝覆盖并要求重新解析')
        temp_fd,tmp=tempfile.mkstemp(dir=index.parent,prefix='.prke-ids-',suffix='.tmp')
        try:
            with os.fdopen(temp_fd,'w',encoding='utf-8') as f:
                json.dump(reg,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
            os.replace(tmp,index)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    finally:lock.unlink(missing_ok=True)

def main(argv=None):
    p=argparse.ArgumentParser(description='PRKE task-local paper identity resolver; no Vault writes')
    p.add_argument('--registry',required=True);p.add_argument('--record',required=True);p.add_argument('--create-new-index',action='store_true')
    try:
        a=p.parse_args(argv);index=Path(a.registry).expanduser().resolve();safe_workspace(index.parent)
        index.parent.mkdir(parents=True,exist_ok=True)
        from execution_core import sha
        base_sha=sha(index) if index.exists() else None
        if index.exists():reg=json.loads(index.read_text(encoding='utf-8-sig'))
        elif a.create_new_index:reg={'schema_version':'1.0','papers':[]}
        else:raise IdentityError('索引不存在；新建请明确添加 --create-new-index')
        new=json.loads(Path(a.record).read_text(encoding='utf-8-sig'))
        result=resolve(reg,new)
        if result['decision']=='NEW_IDENTITY_CANDIDATE':write_index(index,reg,expected_sha=base_sha)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (IdentityError,OSError,ValueError) as e:print('ERROR:',e,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
