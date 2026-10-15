"""Regression tests for PRKE 1.7 research-first integration. Synthetic inputs only."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock
from contextlib import redirect_stdout
from io import StringIO
from argparse import Namespace
import json, sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import execution_core as ex
import scientific_semantics as sem
import review_gate as rv

class ResearchFirstRegression(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.d=Path(self.tmp.name)
    def packet(self):
        return {'schema_version':'1.0',
            'papers':[{'paper_uid':'paperA','access_scope':'FULLTEXT_ACCESSED','identity':{'doi':'10.1234/a'}},
                      {'paper_uid':'paperB','access_scope':'FULLTEXT_ACCESSED','identity':{'doi':'10.1234/b'}}],
            'evidence':[{'evidence_id':'evA','paper_uid':'paperA','evidence_kind':'FULLTEXT_TEXT',
                         'source_locator':'PDF p2','source_version':'a'*64},
                        {'evidence_id':'evB','paper_uid':'paperB','evidence_kind':'FULLTEXT_TEXT',
                         'source_locator':'PDF p3','source_version':'b'*64}],
            'claims':[{'claim_id':'clA','paper_uid':'paperA','claim_kind':'AUTHOR_RESULT',
                       'statement':'Observed original scoped association','evidence_refs':['evA'],
                       'study_context':self.ctx()},
                      {'claim_id':'clB','paper_uid':'paperB','claim_kind':'AUTHOR_RESULT',
                       'statement':'Observed distinct scoped association','evidence_refs':['evB'],
                       'study_context':self.ctx()}],
            'relations':[]}
    def ctx(self):
        return dict(population='plants', measurement='SIF and GPP', time_support='hourly',
                    space_support='tower site', study_design='observational', estimate_target='rho')
    def relation(self, typ='REFINES'):
        return {'relation_id':'relation1','source_claim_id':'clA',
                'target_claim_id':'clB','relation_type':typ,
                'comparability':{'status':'NOT_COMPARABLE',
                  'rationale':'Different measurement support and study design require a hold.'},
                'scientific_warrant':'A possible scope qualification, not direct comparison.',
                'evidence_refs':['evA','evB'],'review_status':'CANDIDATE'}
    def test_incomparable_refines_is_held(self):
        p=self.packet();p['relations']=[self.relation()]
        r=sem.validate(p)
        self.assertEqual(r['held_relations'][0]['decision'],'HOLD_CANDIDATE')
    def test_wrong_author_paper_id_rejected(self):
        p=self.packet();p['claims'][0]['paper_uid']='paperB'
        with self.assertRaises(sem.SemanticsError):sem.validate(p)
    def test_author_cannot_combine_two_papers(self):
        p=self.packet();p['claims'][0]['evidence_refs']=['evA','evB']
        with self.assertRaises(sem.SemanticsError):sem.validate(p)
    def test_unregistered_method_target_not_promoted(self):
        p=self.packet();r=self.relation('USES_METHOD');r.pop('target_claim_id');r['target_id']='unregistered-method'
        p['relations']=[r]
        self.assertEqual(sem.validate(p)['held_relations'][0]['issue'],'EXTERNAL_TARGET_NOT_RESOLVED')
        p['external_targets']=[{'target_id':'unregistered-method'}]
        self.assertEqual(sem.validate(p)['held_relations'],[])
    def test_review_reason_is_string(self):
        p={'schema_version':'1.0','risk':'HIGH','main_claim':'A long scoped scientific inference',
           'main_evidence_refs':['evA'],'counterarguments':[{'reason':1}],
           'reviewer_verdict':'DEFER','review_method':'SELF_CHECK','review_evidence_refs':[]}
        with self.assertRaises(rv.ReviewError):rv.validate(p)
    def test_exclusive_json_create(self):
        f=self.d/'receipt.json';ex.atomic_new(f,{'v':1})
        with self.assertRaises(FileExistsError):ex.atomic_new(f,{'v':2})
        self.assertEqual(ex.read(f),{'v':1})
    def prepare_args(self, uid='action01'):
        input_file=self.d/'input.json';input_file.write_text('{"query":"toy"}',encoding='utf-8')
        return Namespace(workspace=str(self.d/'tasks'),task_id='task1',action_id=uid,
          capability='literature.search',provider='host_search',input=str(input_file),requested_permission='P0')
    def test_prepare_failure_has_no_public_partial_action(self):
        a=self.prepare_args()
        with mock.patch.object(ex,'atomic_new',side_effect=OSError('synthetic crash')):
            with self.assertRaises(OSError):ex.prepare(a)
        self.assertFalse((self.d/'tasks/actions/action01').exists())
        with redirect_stdout(StringIO()):ex.prepare(a)
        self.assertTrue((self.d/'tasks/actions/action01/request.json').is_file())
    def test_receipt_digest_detects_accidental_edit(self):
        a=self.prepare_args()
        with redirect_stdout(StringIO()):ex.prepare(a)
        artifact=self.d/'result.txt';artifact.write_text('actual bytes')
        result=self.d/'result.json';result.write_text(json.dumps({
            'schema_version':'1.0','action_id':'action01','provider':'host_search',
            'status':'HOST_REPORTED_SUCCESS','artifacts':[str(artifact)],
            'output':{'ok':True},'source_provenance':[{'url':'https://example.org'}]}),encoding='utf-8')
        with redirect_stdout(StringIO()):ex.finalize(Namespace(workspace=str(self.d/'tasks'),action_id='action01',result=str(result)))
        rpath=self.d/'tasks/actions/action01/receipt.json';r=ex.read(rpath)
        self.assertEqual(r['receipt_digest'],ex.receipt_digest(r))
        r['status']='HOST_REPORTED_FAILURE';rpath.write_text(json.dumps(r),encoding='utf-8')
        stdout=StringIO()
        with redirect_stdout(stdout):ex.inspect(Namespace(workspace=str(self.d/'tasks'),action_id='action01'))
        self.assertEqual(json.loads(stdout.getvalue())['receipt_integrity'],'MISMATCH_OR_LEGACY')
    def test_source_provenance_must_be_list(self):
        a=self.prepare_args()
        with redirect_stdout(StringIO()):ex.prepare(a)
        data={'schema_version':'1.0','action_id':'action01','provider':'host_search','status':'HOST_REPORTED_SUCCESS',
              'provider_result_ref':'made-up-host','output':{},'source_provenance':'plain string'}
        f=self.d/'bad.json';f.write_text(json.dumps(data),encoding='utf-8')
        with self.assertRaises(ex.ExecutionError):ex.finalize(Namespace(workspace=str(self.d/'tasks'),action_id='action01',result=str(f)))
