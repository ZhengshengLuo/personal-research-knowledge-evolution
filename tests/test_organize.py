"""Offline safety tests using *synthetic* scientific records, not real science.
Real Zotero/Obsidian Windows GUI connection has not been exercised here.
"""
import importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1]
SCRIPT=BASE/'scripts/organize_cli.py'
spec=importlib.util.spec_from_file_location('organize_cli',SCRIPT)
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
sys.path.insert(0,str(BASE/'scripts'))
from understand.engine import prepare, audit, checksum

class OrganizeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.d=Path(self.tmp.name)
        self.v=self.d/'vault';self.task=self.d/'staging'
    def init(self):
        self.assertEqual(o.main(['init-vault','--vault',str(self.v),'--execute','--acknowledge-empty-vault']),0)
    def fixture(self,complete=True):
        import fitz
        pdf=self.d/'fake.pdf';d=fitz.open();p=d.new_page();p.insert_text((40,50),'Synthetic Academic Test Paper Fig. 1 Methods Results '+'x'*250);d.save(str(pdf));d.close()
        self.pp=prepare(pdf,self.d/'job','paperx','DEEP','SILENT','SCIENTIFIC','test','10.5555/fake-123','Synthetic academic test paper',dpi=72)
        if complete:
            src=o.load(self.pp/'source_bundle.json');fig=o.load(self.pp/'figure_inventory.json');record=o.load(self.pp/'reading_record.json');claims=o.load(self.pp/'claim_evidence_matrix.json')
            f=fig['items'][0];f.update({'page':1,'rendered_asset':src['rendered_pages'][0]['path'],'status':'VISUALLY_CHECKED','visual_observation':'Synthetic test deliberately injected, not a scientific finding','checked_by':'AGENT_VISUAL_INSPECTION','checked_at':'2026-10-13T08:00:00Z','claim_ids':['c1']})
            fig.update({'all_main_figures_accounted_for':True,'visual_reconciliation_note':'Only fixture page exists'})
            for k in record['argument_chain']:record['argument_chain'][k]='Synthetic '+k
            for k in record['type_specific']:record['type_specific'][k]='Synthetic '+k
            record['takeaways']=['Synthetic takeaway'];record['critical_appraisal']=[{'issue_id':'R1','question':'Is it fake?','verdict':'LIMITED_SCOPE','reasoning':'Synthetic fixture','source_claim_ids':['c1']}]
            claims['claims']=[{'claim_id':'c1','central':True,'role':'AUTHOR_OBSERVATION','claim':'Synthetic observation','evidence_summary':'Synthetic drawn mark','reasoning':'Fixture only','assessment':'QUALIFIED','source_refs':[{'source_kind':'PDF_IMAGE','page':1,'figure_id':f['figure_id'],'locator':None}]}]
            for n,x in [('figure_inventory.json',fig),('reading_record.json',record),('claim_evidence_matrix.json',claims)]:
                (self.pp/n).write_text(json.dumps(x,ensure_ascii=False),encoding='utf-8')
            (self.pp/'reading_audit.json').write_text(json.dumps(audit(self.pp),ensure_ascii=False),encoding='utf-8')
        return self.pp
    def stage(self,allow_partial=False,stem='Synthetic 2026 - Example',folder=None):
        args=['stage-paper','--paper-dir',str(self.pp),'--vault',str(self.v),'--stage-dir',str(folder or self.task),'--stem',stem]
        if allow_partial:args.append('--allow-partial')
        return o.main(args)
    def commit(self,folder=None,approval=True):
        folder=folder or self.task
        args=['commit','--stage-dir',str(folder),'--vault',str(self.v),'--approve-plan-sha256',o.file_sha(folder/'plan.json')]
        if approval:args.append('--acknowledge-vault-write')
        return o.main(args)
    def test_doctor(self):self.assertEqual(o.main(['doctor']),0)
    def test_preview_no_creation(self):
        self.assertEqual(o.main(['init-vault','--vault',str(self.v)]),0)
        self.assertFalse(self.v.exists())
    def test_reject_nonempty_init(self):
        self.v.mkdir();(self.v/'existing.md').write_text('Human',encoding='utf-8')
        self.assertEqual(o.main(['init-vault','--vault',str(self.v),'--execute','--acknowledge-empty-vault']),2)
        self.assertEqual((self.v/'existing.md').read_text(encoding='utf-8'),'Human')
    def test_init_flat_vault(self):
        self.init();self.assertTrue((self.v/'Papers').is_dir());self.assertTrue((self.v/'Readings').is_dir());self.assertFalse((self.v/'00_Papers').exists());self.assertEqual(len(list((self.v/'Templates').glob('*.md'))),8)
    def test_no_commit_without_approval(self):
        self.init();self.fixture();self.assertEqual(self.stage(),0)
        self.assertEqual(self.commit(approval=False),2)
        self.assertEqual(list((self.v/'Papers').glob('*.md')),[])
    def test_reject_stage_in_vault(self):
        self.init();self.fixture();self.assertEqual(o.main(['stage-paper','--paper-dir',str(self.pp),'--vault',str(self.v),'--stage-dir',str(self.v/'oops')]),2)
    def test_approved_commit_and_persistent_evidence(self):
        self.init();self.fixture();self.assertEqual(self.stage(),0)
        self.assertEqual(len(list((self.v/'Papers').glob('*.md'))),0)
        self.assertEqual(self.commit(),0)
        self.assertEqual(len(list((self.v/'Papers').glob('*.md'))),1)
        self.assertEqual(len(list((self.v/'Readings').glob('*.md'))),1)
        self.assertEqual(len(list((self.v/'.prke/evidence').glob('*/claim_evidence_matrix.json'))),1)
        s=(self.v/'Papers/Synthetic 2026 - Example.md').read_text(encoding='utf-8')
        self.assertIn('ZOTERO_PENDING',s);self.assertIn('[[Synthetic 2026 - Example - 精读]]',s)
        self.assertEqual(o.load(self.task/'commit_receipt.json')['state'],'COMMITTED')
    def test_partial_only_one_note(self):
        self.init();self.fixture(False)
        self.assertEqual(self.stage(),2)
        self.assertEqual(self.stage(True),0)
        self.assertEqual(self.commit(),0)
        self.assertEqual(len(list((self.v/'Papers').glob('*.md'))),1)
        self.assertEqual(len(list((self.v/'Readings').glob('*.md'))),0)
    def test_source_changed_after_staging(self):
        self.init();self.fixture();self.stage()
        self.pp.joinpath('reading_record.json').write_text('{}',encoding='utf-8')
        self.assertEqual(self.commit(),2)
        self.assertEqual(len(list((self.v/'Papers').glob('*.md'))),0)
    def test_pdf_changed_after_staging(self):
        self.init();self.fixture();self.stage()
        (self.d/'fake.pdf').write_bytes((self.d/'fake.pdf').read_bytes()+b'changed')
        self.assertEqual(self.commit(),2)
    def test_duplicate_reimport_preserves_human_text(self):
        self.init();self.fixture();self.stage();self.commit()
        note=self.v/'Papers/Synthetic 2026 - Example.md'
        with note.open('a',encoding='utf-8') as f:f.write('我的手写意见：保留这一段。\n')
        second=self.d/'second'
        self.assertEqual(self.stage(folder=second),0)
        self.assertEqual(self.commit(folder=second),0)
        self.assertIn('我的手写意见：保留这一段。',note.read_text(encoding='utf-8'))
        self.assertEqual(len(list((self.v/'Papers').glob('*.md'))),1)
    def test_managed_text_conflict(self):
        self.init();self.fixture();self.stage();self.commit()
        note=self.v/'Papers/Synthetic 2026 - Example.md';text=note.read_text(encoding='utf-8');note.write_text(text.replace('Synthetic conclusion','My modified conclusion'),encoding='utf-8')
        self.assertEqual(self.stage(folder=self.d/'second'),2)
    def test_target_changed_after_staging(self):
        self.init();self.fixture();self.stage();self.commit()
        second=self.d/'second';self.stage(folder=second)
        note=self.v/'Papers/Synthetic 2026 - Example.md'
        with note.open('a',encoding='utf-8') as f:f.write('\nmanual after staging\n')
        self.assertEqual(self.commit(second),2)
    def test_zotero_requires_real_match(self):
        self.init();self.fixture()
        self.assertEqual(o.main(['stage-paper','--paper-dir',str(self.pp),'--vault',str(self.v),'--stage-dir',str(self.task),'--stem','synthetic','--zotero-library','users/0','--zotero-item-key','AAAAAAAA']),2)
        self.assertFalse(self.task.exists())
    def test_zotero_probe_is_readonly(self):
        with patch.object(o,'zotero_fetch',side_effect=[(b'{}',{}),(b'[{"key":"ABCD1234","data":{"title":"Test","DOI":"10.0000/test","collections":[]}}]',{'Zotero-API-Version':'3'})]) as f:
            self.assertEqual(o.main(['zotero-probe','--limit','1']),0)
            self.assertEqual(f.call_count,2)
            self.assertEqual(f.call_args[0][0],'users/0/items/top?limit=1')
    def test_reject_traversal_stem(self):
        with self.assertRaises(o.OrganizeError):o.safe_stem('../other')
    def test_same_doi_changed_pdf_version_requires_review(self):
        self.init();self.fixture();self.stage();self.commit()
        src=o.load(self.pp/'source_bundle.json')
        # Same DOI, different source hash: source revision cannot silently replace verified version.
        src['source']['sha256']='f'*64
        (self.pp/'source_bundle.json').write_text(json.dumps(src,ensure_ascii=False),encoding='utf-8')
        self.assertEqual(self.stage(folder=self.d/'version2'),2)

    def test_tampered_plan_cannot_commit(self):
        self.init();self.fixture();self.stage()
        p=self.task/'plan.json';digest=o.file_sha(p)
        p.write_text(p.read_text(encoding='utf-8').replace('PENDING_USER_BATCH_APPROVAL','APPROVED'),encoding='utf-8')
        self.assertEqual(o.main(['commit','--stage-dir',str(self.task),'--vault',str(self.v),'--approve-plan-sha256',digest,'--acknowledge-vault-write']),2)
if __name__=='__main__':unittest.main()
