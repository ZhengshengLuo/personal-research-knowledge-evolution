"""Optional source-grounded figure crop / read-only Zotero annotation snapshot.
No image understanding or annotation semantics is claimed by this helper.
"""
from __future__ import annotations
import argparse,json,sys,hashlib,uuid
from pathlib import Path
from organize_cli import (get_understand,OrganizeError,safe_task,file_sha,zotero_fetch,verify_zotero_item)

def crop(a):
    p,source,rec,audit,inventory,claims=get_understand(a.paper_dir)
    items=[x for x in inventory['items'] if x['figure_id']==a.figure_id]
    if len(items)!=1:raise OrganizeError('图表 ID 不唯一或不存在')
    info=items[0]
    if info['status']!='VISUALLY_CHECKED' or not a.acknowledge_visual_identity:
        raise OrganizeError('只有原图真实视觉核验并再次确认图像身份，才能裁剪')
    page=info.get('page')
    if not page:raise OrganizeError('缺正文 PDF 页定位')
    import fitz
    coords=list(a.rect)
    if not len(coords)==4 or not all(0<=n<=1 for n in coords) or not (coords[0]<coords[2] and coords[1]<coords[3]):
        raise OrganizeError('需提供页面归一化 bbox [left top right bottom]，均 0..1')
    doc=fitz.open(source['source']['pdf_path'])
    try:
        if page>len(doc):raise OrganizeError('PDF 页面不存在')
        pg=doc[page-1];r=pg.rect
        rect=fitz.Rect(coords[0]*r.width,coords[1]*r.height,coords[2]*r.width,coords[3]*r.height)
        if rect.is_empty:raise OrganizeError('图像区域为空')
        pix=pg.get_pixmap(matrix=fitz.Matrix(a.scale,a.scale),clip=rect,alpha=False)
        out=Path(a.output).expanduser().resolve()
        if out.exists() or out.with_suffix('.json').exists():raise OrganizeError('目标图像或溯源记录已存在')
        safe_task(out.parent)
        out.parent.mkdir(parents=True,exist_ok=True)
        pix.save(str(out))
        out.with_suffix('.json').write_text(json.dumps({'origin':'ACTUAL_PDF_CROP','paper_id':source['paper_id'],'figure_id':a.figure_id,'pdf_sha256':source['source']['sha256'],'pdf_page':page,'bbox_normalized':coords,'png_sha256':file_sha(out),'image_verified_by_user_or_host':True,'claim_source':'Understand FigureInventory VISUALLY_CHECKED'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('CROPPED_SOURCE_BOUND:',out,'\nFIGURE_ID:',a.figure_id,'\nPDF_PAGE:',page,'\nNO VAULT WRITES')
    finally:doc.close()

def annotations(a):
    out=Path(a.output).expanduser().resolve()
    if out.exists():raise OrganizeError('不覆盖旧批注快照')
    if not a.zotero_item_key.isalnum() or len(a.zotero_item_key)!=8:raise OrganizeError('Zotero Item Key 非法')
    if a.library!='users/0':raise OrganizeError('阶段一批注读取仅支持本机 users/0 库')
    from urllib.parse import quote
    from urllib.error import HTTPError,URLError
    try:
        raw,_=zotero_fetch('users/0/items/'+quote(a.zotero_item_key,safe='')+'/children?limit=100')
        children=json.loads(raw.decode('utf-8'))
        rows=[]
        for ch in children:
            data=ch.get('data',{});typ=data.get('itemType')
            if typ=='annotation':
                rows.append({'item_key':ch.get('key'),'parent_key':data.get('parentItem'),'annotationText':data.get('annotationText',''),
                             'annotationComment':data.get('annotationComment',''),'annotationPageLabel':data.get('annotationPageLabel'),
                             'annotationType':data.get('annotationType'),'user_original_unmodified':True})
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps({'connection':'ZOTERO_LOCAL_READONLY','origin_item_key':a.zotero_item_key,'annotations':rows,
                                   'note':'只读快照；智能选取与精读证据关联需要科研 Agent 独立审核。'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('ANNOTATION_SNAPSHOT:',out,'\nCOUNT:',len(rows),'\nZOTERO WRITES: 0')
    except (HTTPError,URLError,ValueError) as e:raise OrganizeError('本地 Zotero 批注获取失败: '+str(e)) from e

def main(argv=None):
    p=argparse.ArgumentParser(description='PRKE source-grounded figures and Zotero annotation snapshot')
    sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('crop-figure');c.add_argument('--paper-dir',required=True);c.add_argument('--figure-id',required=True);c.add_argument('--rect',type=float,nargs=4,required=True)
    c.add_argument('--output',required=True);c.add_argument('--scale',type=float,default=2);c.add_argument('--acknowledge-visual-identity',action='store_true');c.set_defaults(f=crop)
    z=sub.add_parser('zotero-annotations');z.add_argument('--library',default='users/0');z.add_argument('--zotero-item-key',required=True);z.add_argument('--output',required=True);z.set_defaults(f=annotations)
    a=p.parse_args(argv)
    try:a.f(a);return 0
    except (OrganizeError,OSError,ValueError,ImportError) as e:print('ERROR:',e,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
