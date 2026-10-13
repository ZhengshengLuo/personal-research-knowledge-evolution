import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('acquire_cli', BASE/'scripts'/'acquire_cli.py')
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

class AcquireTests(unittest.TestCase):
    def setUp(self):
        self.plan=a.read_json(BASE/'examples/acquire/search_plan.example.json')
        self.candidates=a.read_json(BASE/'examples/acquire/candidate_set.example.json')
        self.log=a.read_json(BASE/'examples/acquire/search_log.example.json')

    def test_doctor(self):
        self.assertEqual(a.run(['doctor']),0)

    def test_all_valid_examples(self):
        for key, obj in [('search_plan',self.plan),('candidate_set',self.candidates),('search_log',self.log)]:
            a.validate(key,obj)

    def test_normalize_doi_without_online_claim(self):
        self.assertEqual(a.normalize_doi('HTTPS://DOI.ORG/10.1234/ABC.DEF.'),'10.1234/abc.def')
        self.assertEqual(a.normalize_doi('doi: 10.5555/Test_23'),'10.5555/test_23')
        self.assertIsNone(a.normalize_doi('made-up-id'))

    def test_candidate_needs_syntax_valid_doi(self):
        d=copy.deepcopy(self.candidates);d['papers'][0]['doi']='DOI_NOT_VALID'
        with self.assertRaises(a.AcquireError):a.validate('candidate_set',d)

    def test_crosschecked_needs_two_sources(self):
        d=copy.deepcopy(self.candidates);v=d['papers'][0]['verification'];v['bibliography']='CROSSCHECKED';v['bibliographic_sources']=['single-provider']
        with self.assertRaises(a.AcquireError):a.validate('candidate_set',d)

    def test_no_fulltext_claim_without_access(self):
        d=copy.deepcopy(self.candidates);v=d['papers'][0]['verification'];v['read_scope']='FULLTEXT_ACCESSED'
        with self.assertRaises(a.AcquireError):a.validate('candidate_set',d)

    def test_no_claim_checked_without_fulltext(self):
        d=copy.deepcopy(self.candidates);v=d['papers'][0]['verification'];v['claim_evidence']='CHECKED'
        with self.assertRaises(a.AcquireError):a.validate('candidate_set',d)

    def test_metadata_conflict_cannot_include(self):
        d=copy.deepcopy(self.candidates);v=d['papers'][0]['verification'];v['bibliography']='CONFLICT';d['papers'][0]['screening']['decision']='INCLUDE'
        with self.assertRaises(a.AcquireError):a.validate('candidate_set',d)

    def test_duplicate_ids_rejected(self):
        d=copy.deepcopy(self.candidates);d['papers'].append(copy.deepcopy(d['papers'][0]))
        with self.assertRaises(a.AcquireError):a.validate('candidate_set',d)

    def test_doi_duplicates_flagged_not_merged(self):
        d=copy.deepcopy(self.candidates);p=d['papers'][0];p['doi']='doi: 10.1234/example';p['title']='A sample paper';p['year']=2021
        second=copy.deepcopy(p);second['record_id']='demo-002';second['doi']='https://doi.org/10.1234/EXAMPLE'
        d['papers'].append(second);a.validate('candidate_set',d)
        risk=a.duplicate_risks(d['papers'])
        self.assertEqual(len(risk['identical_doi_groups']),1)
        self.assertEqual(len(risk['same_title_year_groups']),1)
        self.assertEqual(len(d['papers']),2)

    def test_same_title_year_flag_not_merged_without_doi(self):
        d=copy.deepcopy(self.candidates);d['papers'][0]['year']=2023
        another=copy.deepcopy(d['papers'][0]);another['record_id']='demo-002';another['title']=another['title'].lower()
        d['papers'].append(another)
        risk=a.duplicate_risks(d['papers'])
        self.assertEqual(risk['identical_doi_groups'],[])
        self.assertEqual(len(risk['same_title_year_groups']),1)

    def test_systematic_cannot_be_exploratory(self):
        p=copy.deepcopy(self.plan);p['mode']='SYSTEMATIC'
        with self.assertRaises(a.AcquireError):a.validate('search_plan',p)

    def test_reversed_years_rejected(self):
        p=copy.deepcopy(self.plan);p['scope']['publication_from']=2025;p['scope']['publication_to']=2020
        with self.assertRaises(a.AcquireError):a.validate('search_plan',p)

    def test_duplicate_query_ids_rejected(self):
        p=copy.deepcopy(self.plan);p['queries'].append(copy.deepcopy(p['queries'][0]))
        with self.assertRaises(a.AcquireError):a.validate('search_plan',p)

    def test_running_async_must_track_job_id(self):
        log=copy.deepcopy(self.log);log['runs'][0]['status']='RUNNING'
        with self.assertRaises(a.AcquireError):a.validate('search_log',log)
        log['runs'][0]['external_job_ref']='existing-job-01'
        a.validate('search_log',log)

    def test_dedup_report_creates_new_only(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'source.json';source.write_text(json.dumps(self.candidates),encoding='utf-8')
            out=Path(td)/'safe'/'report.json'
            self.assertEqual(a.run(['dedup-report','--file',str(source),'--output',str(out)]),0)
            self.assertTrue(out.is_file())
            self.assertEqual(a.run(['dedup-report','--file',str(source),'--output',str(out)]),2)

    def test_protect_vault_output(self):
        with tempfile.TemporaryDirectory() as td:
            vault=Path(td)/'vault';(vault/'.obsidian').mkdir(parents=True)
            with self.assertRaises(a.AcquireError):a.protect_output(vault/'prke'/'report.json')

    def test_registry_is_instruction_only(self):
        r=a.read_json(BASE/'router/interfaces/module-registry.json')
        self.assertEqual(r['modules']['acquire']['status'],'INSTRUCTION_READY')
        self.assertFalse(r['modules']['acquire']['guarantees_tool_access'])
        self.assertEqual(r['modules']['understand']['status'],'INSTRUCTION_READY')
        self.assertEqual(r['modules']['organize']['status'],'INSTRUCTION_READY')
        self.assertEqual(r['modules']['synthesize']['status'],'INSTRUCTION_READY')

if __name__=='__main__':unittest.main()
