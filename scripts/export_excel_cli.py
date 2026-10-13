"""On-demand read-only PRKE comparative export. Requires optional artifact_tool."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path

def export(a):
    source=Path(a.input).expanduser().resolve();dest=Path(a.output).expanduser().resolve()
    if dest.exists():raise ValueError('只允许创建新 Excel 文件，不覆盖旧表')
    if not source.is_file():raise ValueError('来源索引不存在')
    data=json.loads(source.read_text(encoding='utf-8-sig'))
    try:from artifact_tool import Workbook,SpreadsheetFile
    except ImportError as e:raise ValueError('可选 Excel 依赖 artifact_tool 不可用：请在用户 Windows 环境安装后再启用，此功能不影响主 Skill') from e
    rows=data.get('papers',{})
    if not isinstance(rows,dict):raise ValueError('需要来自正式 Organize 的 papers index')
    wb=Workbook.create();groups={'总表':[],'Review':[],'Analysis':[],'Method':[],'Data':[]}
    headers=['Paper UID','Paper ID','DOI','标题简写','阅读笔记','精读笔记','Zotero Library','Zotero Key','PDF SHA256','类型']
    types={'REVIEW':'Review','SCIENTIFIC':'Analysis','METHOD':'Method','DATA_RESOURCE':'Data'}
    for uid,x in sorted(rows.items()):
        category=x.get('primary_type','');row=[uid,x.get('paper_id',''),x.get('doi',''),x.get('stem',''),x.get('paper_rel',''),x.get('reading_rel',''),x.get('zotero_library',''),x.get('zotero_item_key',''),x.get('source_sha256',''),category]
        groups['总表'].append(row)
        if types.get(category) in groups:groups[types[category]].append(row)
    for name,items in groups.items():
        sheet=wb.worksheets.add(name)
        n=max(2,len(items)+1)
        sheet.get_range_by_indexes(0,0,1,len(headers)).values=[headers]
        if items:sheet.get_range_by_indexes(1,0,len(items),len(headers)).values=items
        header=sheet.get_range_by_indexes(0,0,1,len(headers))
        header.format={'fill':'#244A44','font':{'bold':True,'color':'#FFFFFF'},'row_height':29,'wrap_text':True}
        sheet.get_range_by_indexes(0,0,n,3).format.column_width=24
        sheet.get_range_by_indexes(0,3,n,1).format.column_width=38
        sheet.get_range_by_indexes(0,4,n,2).format.column_width=36
        sheet.get_range_by_indexes(0,6,n,4).format.column_width=25
        sheet.freeze_panes.freeze_rows(1)
    dest.parent.mkdir(parents=True,exist_ok=True)
    SpreadsheetFile.export_xlsx(wb).save(str(dest))
    print('EXPORTED_ON_DEMAND:',dest,'ROWS:',len(rows),'SOURCE:',source,'NO DATABASE WRITES')

def main(argv=None):
    p=argparse.ArgumentParser(description='Export PRKE index as optional comparison-only Excel workbook')
    p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    a=p.parse_args(argv)
    try:export(a);return 0
    except (ValueError,OSError,KeyError,RuntimeError) as e:print('ERROR:',e,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
