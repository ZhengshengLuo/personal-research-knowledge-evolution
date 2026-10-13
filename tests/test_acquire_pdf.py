import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pdf_acquisition',ROOT/'scripts/pdf_acquisition.py')
pdf=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdf)


def base_candidate():
    return {
        'schema_version':'1.0','task_id':'task-unit-test','generated_at':'2026-10-13T00:00:00Z',
        'papers':[{'record_id':'test-0001','title':'A Thorough Study of Simulated Land Vegetation Responses to Drought',
                   'authors':['Alice Researcher'],'year':2023,'venue':'Journal of Test Cases','doi':'10.5555/test-case-001',
                   'url':'https://doi.org/10.5555/test-case-001','publication_type':'JOURNAL',
                   'sources':[{'tool':'TEST_FIXTURE','query_id':'mock','retrieved_at':'2026-10-13T00:00:00Z'}],
                   'screening':{'decision':'INCLUDE','reason':'offline synthetic test'},
                   'verification':{'bibliography':'UNKNOWN','bibliographic_sources':[],
                         'fulltext':'NOT_CHECKED','read_scope':'METADATA_ONLY','claim_evidence':'NOT_CHECKED'},
                   'relevance_reason':'Synthetic fixture only; not a paper','recommended_for':[]}
                  ], 'limitations':['Synthetic. Not a real reference.']}


def make_pdf(path,title='A Thorough Study of Simulated Land Vegetation Responses to Drought',doi='10.5555/test-case-001'):
    import fitz
    doc=fitz.open();page=doc.new_page()
    page.insert_text((50,50),title,fontname='helv',fontsize=11)
    page.insert_text((50,75),'Article DOI: '+doi,fontname='helv',fontsize=11)
    doc.save(str(path));doc.close()


class AcquisitionPDFTests(unittest.TestCase):
    def test_api_host_allowlist(self):
        self.assertTrue(pdf.allowed_pdf_url('https://api.elsevier.com/content/article/doi/10.1016/xyz'))
        self.assertFalse(pdf.allowed_pdf_url('http://api.elsevier.com/foo'))
        self.assertFalse(pdf.allowed_pdf_url('https://localhost/latest.pdf'))
        self.assertFalse(pdf.allowed_pdf_url('https://api.elsevier.com.evil.test/latest.pdf'))
        self.assertFalse(pdf.allowed_pdf_url('https://10.0.0.2/private'))
        self.assertFalse(pdf.allowed_pdf_url('https://user:secret@api.wiley.com/x.pdf'))

    def test_curated_iop_and_ugent_hosts(self):
        self.assertTrue(pdf.allowed_pdf_url('https://iopscience.iop.org/article/10.1088/123/pdf'))
        self.assertTrue(pdf.allowed_pdf_url('https://biblio.ugent.be/publication/123/file/123.pdf'))
        self.assertFalse(pdf.allowed_pdf_url('https://iopscience.iop.org.evil.example/pdf'))
    def test_springer_skips_non_springer_doi_even_with_key(self):
        with patch.object(pdf,'fetch_json',side_effect=AssertionError('wrong publisher request')):
            self.assertEqual(pdf.candidate_urls_from_springer('10.5194/bg-18-2379-2021','dummy'),[])
    def test_openalex_filtered_url_audited(self):
        data={'best_oa_location':{'pdf_url':'https://untrusted.example.com/anything.pdf?token=SECRET','is_oa':True,'version':'PUBLISHED'}}
        rejected=[]
        with patch.object(pdf,'fetch_json',return_value=data):
            self.assertEqual(pdf.candidate_urls_from_openalex('10.5555/x',rejected=rejected),[])
        self.assertEqual(rejected[0]['reason'],'UNAPPROVED_DOMAIN_OR_SCHEME')
        self.assertNotIn('SECRET',rejected[0]['url_without_query'])

    def test_expected_doi_not_enough_to_match(self):
        item=base_candidate()['papers'][0]
        scan={'status':'PARSED','first_page':'Other Research Paper 10.5555/test-case-001','metadata':{},'reason':'ok'}
        self.assertNotEqual(pdf.match_paper(scan,item)[0],'VERIFIED')

    def test_matching_title_and_firstpage_doi(self):
        p=base_candidate()['papers'][0]
        scan={'status':'PARSED','first_page':p['title']+'\nDOI 10.5555/test-case-001','metadata':{},'reason':'ok'}
        self.assertEqual(pdf.match_paper(scan,p)[0],'VERIFIED')

    def test_matching_title_without_doi_stays_unverified(self):
        p=base_candidate()['papers'][0]
        scan={'status':'PARSED','first_page':p['title']+'\nIntroduction', 'metadata':{},'reason':'ok'}
        self.assertEqual(pdf.match_paper(scan,p)[0],'PROBABLE')

    def test_only_header_does_not_count(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'notreally.pdf';f.write_bytes(b'%PDF-1.4\nfake')
            self.assertEqual(pdf.pdf_inspect(f)['status'],'INVALID_PDF')

    def test_no_vault_write(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'vault';(dest/'.obsidian').mkdir(parents=True)
            with self.assertRaises(pdf.PDFError):pdf.safe_task_dir(dest/'tasks'/'abc')

    def test_manual_full_handoff_and_immutable_source(self):
        import fitz
        with tempfile.TemporaryDirectory() as td:
            task=Path(td)/'task';pdf.ensure_task_dirs(task)
            src=task/'pdf/manual_inbox'/'random_filename.pdf'
            make_pdf(src)
            original=hashlib.sha256(src.read_bytes()).hexdigest()
            path, report=pdf.scan_manual(task,base_candidate())
            self.assertEqual(len(report['items']),1)
            self.assertEqual(report['items'][0]['status'],'VERIFIED')
            self.assertEqual(report['items'][0]['record_id'],'test-0001')
            self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),original)
            self.assertTrue(Path(report['items'][0]['verified_copy']).exists())
            # The human queue should no longer contain a successfully verified record.
            queuepath,queue=pdf.manual_queue(task,base_candidate())
            self.assertEqual(len(queue['items']),0)
            self.assertNotEqual(path,queuepath)

    def test_wrong_pdf_kept_out_of_verified(self):
        import fitz
        with tempfile.TemporaryDirectory() as td:
            task=Path(td)/'task';pdf.ensure_task_dirs(task)
            src=task/'pdf/manual_inbox'/'wrong.pdf'
            make_pdf(src,title='Some Completely Unrelated Study of an Entirely Different Topic',doi='10.5555/different')
            _,rep=pdf.scan_manual(task,base_candidate())
            self.assertEqual(rep['items'][0]['status'],'REVIEW_REQUIRED')
            self.assertEqual(list((task/'pdf/verified').glob('*.pdf')),[])
            self.assertTrue(src.is_file())

    def test_preview_makes_no_request_or_credential_read(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(pdf,'fetch_bytes',side_effect=AssertionError('no network')):
                with patch.object(pdf,'load_keys',side_effect=AssertionError('no .env read')):
                    _,rep=pdf.auto_fetch(Path(td)/'task',base_candidate(),execute=False)
            self.assertEqual(rep['items'][0]['status'],'PLAN_ONLY')

    def test_mock_autofetch_full_pdf(self):
        import fitz
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'template.pdf';make_pdf(f);blob=f.read_bytes()
            with patch.object(pdf,'candidate_urls_from_openalex',return_value=[('https://zenodo.org/record/xy.pdf','PUBLISHED_VERSION','OPENALEX_OA')]):
                with patch.object(pdf,'candidate_urls_from_unpaywall',return_value=[]),patch.object(pdf,'candidate_urls_from_springer',return_value=[]):
                    with patch.object(pdf,'fetch_bytes',return_value=blob):
                        _,report=pdf.auto_fetch(Path(td)/'task',base_candidate(),limit=1,execute=True)
            self.assertEqual(report['items'][0]['status'],'VERIFIED')
            self.assertTrue(Path(report['items'][0]['file']['verified_path']).exists())

    def test_mock_autofetch_html_is_not_pdf(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(pdf,'candidate_urls_from_openalex',return_value=[('https://zenodo.org/data.pdf','UNKNOWN','OPENALEX_OA')]):
                with patch.object(pdf,'candidate_urls_from_unpaywall',return_value=[]),patch.object(pdf,'candidate_urls_from_springer',return_value=[]):
                    with patch.object(pdf,'fetch_bytes',return_value=b'<html>403 error</html>'):
                        _,report=pdf.auto_fetch(Path(td)/'task',base_candidate(),execute=True)
            self.assertEqual(report['items'][0]['status'],'NEEDS_MANUAL_REVIEW')
            self.assertEqual(list((Path(td)/'task/pdf/verified').glob('*.pdf')),[])

    def test_no_secrets_in_package(self):
        src=(ROOT/'scripts/pdf_acquisition.py').read_text(encoding='utf-8')
        self.assertIn('ELSEVIER_API_KEY',src)
        self.assertNotIn('HARDCODED_SECRET',src)
        self.assertIn('load_keys',src)

    def test_source_downloader_not_bundled(self):
        self.assertFalse((ROOT/'downloader'/'resolver.py').exists())
        self.assertFalse((ROOT/'scripts'/'institutional_worker.py').exists())

if __name__=='__main__':unittest.main()

class EvidenceContractTests(unittest.TestCase):
    def test_unsupported_domain_branch_rejected(self):
        spec=importlib.util.spec_from_file_location('acqcli',ROOT/'scripts/acquire_cli.py')
        acq=importlib.util.module_from_spec(spec);spec.loader.exec_module(acq)
        data=json.loads((ROOT/'examples/acquire/domain_map.example.json').read_text(encoding='utf-8'))
        data['branches']=[{'branch_id':'b1','description':'Unsupported claim','supporting_paper_ids':[],
                           'confidence':'SUPPORTED','reading_priority':'HIGH'}]
        with self.assertRaises(acq.AcquireError):acq.validate('domain_map',data)

    def test_coverage_cannot_claim_adequate_without_evidence(self):
        spec=importlib.util.spec_from_file_location('acqcli2',ROOT/'scripts/acquire_cli.py')
        acq=importlib.util.module_from_spec(spec);spec.loader.exec_module(acq)
        data=json.loads((ROOT/'examples/acquire/coverage_matrix.example.json').read_text(encoding='utf-8'))
        data['dimensions']=[{'dimension':'methods','coverage':'REASONABLE_FOR_TASK','supporting_paper_ids':[],'gaps':[]}]
        with self.assertRaises(acq.AcquireError):acq.validate('coverage_matrix',data)
