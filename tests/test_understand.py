import importlib.util, json, tempfile, unittest
from pathlib import Path
import fitz
BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('understand_engine',BASE/'scripts/understand/engine.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

class UnderstandTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.pdf=self.root/'paper.pdf'
        d=fitz.open();p=d.new_page();p.insert_text((35,40),'Research motivation: drought affects ecosystems. Fig. 1 shows patterns.\n'+'Relevant Methods and Results. '*20);p.draw_rect(fitz.Rect(35,80,150,190));p.insert_text((35,205),'Figure 1. example visualization.');d.save(str(self.pdf));d.close()
    def _prepare(self,depth='DEEP',typ='SCIENTIFIC',supp=None):
        return u.prepare(self.pdf,self.root/'tasks','test-paper',depth,'SILENT',typ,'Understand scientific evidence','10.0000/test','Fake testing-only paper',dpi=72,supplements=supp)
    def _files(self,p):
        return [u.read(p/n) for n in ('source_bundle.json','figure_inventory.json','reading_record.json','claim_evidence_matrix.json')]
    def _put(self,path,obj):path.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8')
    def test_doctor(self):u.doctor()
    def test_all_schemas_are_valid(self):
        for x in (BASE/'schemas/understand').glob('*.schema.json'):
            import jsonschema
            jsonschema.Draft202012Validator.check_schema(u.read(x))
    def test_prepare_source_sha_and_render(self):
        p=self._prepare();s,f,r,c=self._files(p)
        self.assertEqual(s['source']['sha256'],u.checksum(self.pdf));self.assertEqual(len(s['rendered_pages']),1)
        self.assertEqual(r['depth'],'DEEP');self.assertEqual(len(f['items']),1)
        self.assertEqual(f['items'][0]['status'],'PENDING_VISUAL')
        self.assertEqual(u.audit(p)['status'],'PARTIAL')
    def test_prepare_never_claims_vision(self):
        p=self._prepare();s,f,r,c=self._files(p)
        self.assertIn('NOT_VISUALLY_CHECKED',s['render_quality']['status'])
        self.assertFalse(f['all_main_figures_accounted_for'])
        self.assertEqual(u.read(p/'reading_audit.json')['status'],'PARTIAL')
    def test_text_only_does_not_pass_visual(self):
        p=self._prepare();s,f,r,c=self._files(p)
        x=f['items'][0];x['status']='VISUALLY_CHECKED';x['page']=1;x['visual_observation']='Description only';x['checked_by']='AGENT_VISUAL_INSPECTION';x['checked_at']='2026-10-13';self._put(p/'figure_inventory.json',f)
        self.assertEqual(u.audit(p)['status'],'PARTIAL')
        self.assertTrue(any('渲染来源' in e for e in u.audit(p)['issues']))
    def test_partial_note_rejected_by_default(self):
        p=self._prepare()
        with self.assertRaises(u.UnderstandError):u.note(p)
    def test_partial_note_explicitly_labeled(self):
        p=self._prepare();out=u.note(p,True);txt=out.read_text(encoding='utf-8')
        self.assertIn('PARTIAL',txt);self.assertIn('审查未完成项',txt);self.assertNotIn('已写入 Obsidian',txt)
    def test_html_no_remote_and_no_key(self):
        p=self._prepare();out=u.make_html(p);s=out.read_text(encoding='utf-8')
        self.assertIn('本地阅读视图',s);self.assertNotIn('fetch(',s);self.assertNotIn('API_KEY',s)
    def test_handoff_is_pending(self):
        p=self._prepare();u.note(p,True);f=u.organize_handoff(p,'batch-demo',True);x=u.read(f)
        self.assertEqual(x['write_state'],'PENDING_ORGANIZE');self.assertEqual(x['authorization_state'],'USER_TASK_APPROVED')
        self.assertFalse((self.root/'.obsidian').exists())
    def test_duplicate_protects_records(self):
        self._prepare()
        with self.assertRaises(u.UnderstandError):self._prepare()
    def test_vault_protected(self):
        v=self.root/'vault';(v/'.obsidian').mkdir(parents=True)
        with self.assertRaises(u.UnderstandError):u.prepare(self.pdf,v/'tasks','paper','DEEP','SILENT','METHOD','method')
    def test_source_changed_blocks(self):
        p=self._prepare();self.pdf.write_bytes(self.pdf.read_bytes()+b'changed')
        self.assertEqual(u.audit(p)['status'],'BLOCKED')
    def test_scanned_pdf_limited(self):
        q=self.root/'scanned.pdf';d=fitz.open();d.new_page();d.save(str(q));d.close()
        p=u.prepare(q,self.root/'tasks','scan-paper','SCAN','SILENT','REVIEW','review')
        self.assertEqual(u.read(p/'source_bundle.json')['source']['text_quality'],'TEXT_LIMITED')
        self.assertEqual(u.audit(p)['status'],'PARTIAL')
    def test_all_four_types_have_distinct_fields(self):
        self.assertEqual(len(u.TYPE_FIELDS),4)
        self.assertEqual(len(set(tuple(v) for v in u.TYPE_FIELDS.values())),4)
    def test_invalid_id_rejected(self):
        with self.assertRaises(u.UnderstandError):self._prepare_bad_id()
    def _prepare_bad_id(self):u.prepare(self.pdf,self.root/'tasks','../../unsafe','DEEP','SILENT','METHOD','x')
    def test_comparison_reject_duplicate(self):
        p=self._prepare(depth='SCAN')
        with self.assertRaises(u.UnderstandError):u.init_comparison(self.root/'tasks',[p,p],'research question')
    def test_comparison_two_papers(self):
        p=self._prepare(depth='SCAN');q=u.prepare(self.pdf,self.root/'tasks','paper-b','FOCUSED','SILENT','METHOD','question')
        path=u.init_comparison(self.root/'tasks',[p,q],'methods differ?');z=u.read(path)
        self.assertEqual(z['status'],'DRAFT_NOT_COMPARATIVELY_VERIFIED');self.assertEqual(len(z['papers']),2)
    def test_supplement_pdf_metadata_and_render(self):
        s=self.root/'supp.pdf';d=fitz.open();d.new_page();d.save(str(s));d.close()
        p=self._prepare(supp=[s]);obj=u.read(p/'source_bundle.json');self.assertEqual(len(obj['supplements']),1)
        self.assertTrue((p/obj['supplements'][0]['rendered_pages'][0]['path']).exists())
        self.assertEqual(u.audit(p)['status'],'PARTIAL')
    def test_supplement_hash_changes_blocks(self):
        s=self.root/'supp.pdf';d=fitz.open();d.new_page();d.save(str(s));d.close()
        p=self._prepare(supp=[s]);s.write_bytes(s.read_bytes()+b'modified')
        self.assertEqual(u.audit(p)['status'],'BLOCKED')
    def test_paper_type_deep_requires_content(self):
        for typ in u.TYPE_FIELDS:
            with self.subTest(typ=typ):
                self.assertGreaterEqual(len(u.TYPE_FIELDS[typ]),6)
    def test_audit_does_not_claim_reality(self):
        p=self._prepare();d=u.audit(p,True)
        self.assertEqual(d['checks']['visual_verified_count'],0)
        self.assertTrue(len(d['issues'])>3)
    def test_simulated_receipts_pass_structural_audit_only(self):
        # The test deliberately injects SYNTHETIC visual receipts. PASS means the
        # audit structure is complete; it does not prove real scientific reading.
        p=self._prepare();source,fig,record,claims=self._files(p)
        f=fig['items'][0];f['page']=1;f['rendered_asset']=source['rendered_pages'][0]['path']
        f['status']='VISUALLY_CHECKED';f['visual_observation']='Synthetic test fixture: axes and rectangle seen'
        f['checked_by']='AGENT_VISUAL_INSPECTION';f['checked_at']='2026-10-13T08:00:00Z';f['claim_ids']=['c1']
        fig['all_main_figures_accounted_for']=True;fig['visual_reconciliation_note']='Synthetic fixture page 1 only'
        for k in record['argument_chain']:record['argument_chain'][k]='Synthetic '+k
        for k in record['type_specific']:record['type_specific'][k]='Synthetic '+k
        record['takeaways']=['Synthetic takeaway']
        record['critical_appraisal']=[{'issue_id':'R1','question':'What does the data show?',
                                      'verdict':'LIMITED_SCOPE','reasoning':'Synthetic scoped evidence fixture',
                                      'source_claim_ids':['c1']}]
        claims['claims']=[{'claim_id':'c1','central':True,'role':'AUTHOR_OBSERVATION',
                           'claim':'Synthetic result','evidence_summary':'Synthetic rectangle visual fixture',
                           'reasoning':'Only synthetic sample','assessment':'QUALIFIED',
                           'source_refs':[{'source_kind':'PDF_IMAGE','page':1,'figure_id':f['figure_id'],'locator':None}]}]
        for n,d in [('figure_inventory.json',fig),('reading_record.json',record),('claim_evidence_matrix.json',claims)]:self._put(p/n,d)
        self.assertEqual(u.audit(p)['status'],'COMPLETED')
        self.assertTrue(u.note(p).is_file())

    def test_organize_route_registered(self):
        reg=u.read(BASE/'router/interfaces/module-registry.json');self.assertEqual(reg['modules']['organize']['status'],'INSTRUCTION_READY')
    def test_only_one_skill(self):self.assertEqual(len(list(BASE.rglob('SKILL.md'))),1)

if __name__=='__main__':unittest.main()
