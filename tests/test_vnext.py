"""Synthetic safety/integration-contract tests; NOT independent scientific Gold Set."""
import json, sys, tempfile, unittest
from pathlib import Path
from argparse import Namespace
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'scripts'))
import execution_core as ex
import scientific_semantics as sem
import review_gate as rv
import synthesize_engine as se
import synthesize_cli as sc
import organize_cli as org
import knowledge_cli as kb

class VNextContracts(unittest.TestCase):
 def setUp(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup)
  self.root=Path(td.name);self.task=self.root/'task';self.task.mkdir()
 def dump(self,name,obj):
  p=self.root/name;p.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8');return p
 def test_capability_registry_is_declarative(self):
  caps=ex.capabilities()['capabilities']
  self.assertGreaterEqual(len(caps),5)
  self.assertTrue(all('allowed_permissions' in x and 'providers' in x for x in caps))
  self.assertNotIn('knowledge.commit',[x['capability_id'] for x in caps])
 def test_handoff_is_not_fake_execution(self):
  file=self.dump('input.json',{'query':'synthetic research query'})
  self.assertEqual(ex.main(['prepare','--workspace',str(self.task),'--task-id','t1','--action-id','a1',
    '--capability','literature.search','--input',str(file)]),0)
  p=self.task/'actions/a1'
  self.assertFalse((p/'receipt.json').exists())
  self.assertEqual(ex.read(p/'request.json')['status'],'AWAITING_HOST_EXECUTION')
  self.assertEqual(ex.main(['inspect','--workspace',str(self.task),'--action-id','a1']),0)
  self.assertEqual(ex.main(['prepare','--workspace',str(self.task),'--task-id','t1','--action-id','a1','--capability','literature.search','--input',str(file)]),2)
 def test_host_receipt_checks_artifacts_but_not_science(self):
  src=self.dump('input.json',{'query':'synthetic'})
  ex.main(['prepare','--workspace',str(self.task),'--task-id','t1','--action-id','a2','--capability','pdf.inspect','--provider','local_pdf','--input',str(src)])
  artifact=self.root/'sample.pdf';artifact.write_bytes(b'not a real pdf, synthetic output test')
  report=self.dump('host.json',{'schema_version':'1.0','action_id':'a2','provider':'local_pdf','status':'HOST_REPORTED_SUCCESS','artifacts':[str(artifact)],'output':{'page':1}})
  self.assertEqual(ex.main(['finalize','--workspace',str(self.task),'--action-id','a2','--result',str(report)]),0)
  rec=ex.read(self.task/'actions/a2/receipt.json')
  self.assertEqual(rec['execution_assurance'],'HOST_REPORTED_UNVERIFIED')
  self.assertEqual(rec['scientific_verification'],'NOT_ASSESSED')
  self.assertEqual(ex.main(['finalize','--workspace',str(self.task),'--action-id','a2','--result',str(report)]),2)
  artifact.write_bytes(b'mutated')
  self.assertNotEqual(ex.sha(artifact),rec['artifacts'][0]['sha256'])
 def test_provider_and_permission_boundaries(self):
  f=self.dump('args.json',{'objective':'synthetic'})
  self.assertEqual(ex.main(['prepare','--workspace',str(self.task),'--task-id','t1','--capability','literature.search','--input',str(f),'--requested-permission','P2']),2)
  self.assertEqual(ex.main(['prepare','--workspace',str(self.task),'--task-id','t1','--capability','literature.search','--input',str(f),'--provider','unknown']),2)
  vault=self.root/'vault';vault.mkdir();(vault/'.obsidian').mkdir()
  self.assertEqual(ex.main(['prepare','--workspace',str(vault/'task'),'--task-id','t1','--capability','literature.search','--input',str(f)]),2)
 def semantic(self):
  ctx={'population':'synthetic plantation','measurement':'fluorescence','time_support':'16 day',
      'space_support':'0.1deg','study_design':'observational','estimate_target':'anomaly association'}
  return {'schema_version':'1.0', 'papers':[{'paper_uid':'P1','access_scope':'FULLTEXT_ACCESSED','identity':{'doi':'10.1234/example'}}],
    'evidence':[{'evidence_id':'E1','paper_uid':'P1','evidence_kind':'FULLTEXT_FIGURE','source_locator':'PDF physical p3 Fig1','source_version':'a'*64}],
    'claims':[{'claim_id':'C1','claim_kind':'AUTHOR_RESULT','statement':'Synthetic result for testing first claim','study_context':ctx,'evidence_refs':['E1']},
              {'claim_id':'C2','claim_kind':'AGENT_INFERENCE','statement':'Synthetic second inference for testing','study_context':ctx,'evidence_refs':['E1']}],
    'relations':[{'relation_id':'R1','source_claim_id':'C1','target_claim_id':'C2','relation_type':'CHALLENGES',
       'comparability':{'status':'CONDITIONALLY_COMPARABLE','rationale':'Same measurement, with acknowledged variation in study context.'},
       'scientific_warrant':'Synthetic illustrative claim-to-claim relation only, no truth judgment.',
       'evidence_refs':['E1'],'review_status':'CANDIDATE'}]}
 def test_semantic_relations_are_only_structural(self):
  p=self.semantic();x=sem.validate(p)
  self.assertEqual(x['epistemic_status'],'STRUCTURE_AND_REFERENCES_CHECKED_ONLY')
  self.assertEqual(x['relation_count'],1)
  p['relations'][0]['comparability']['status']='NOT_COMPARABLE'
  self.assertEqual(len(sem.validate(p)['held_relations']),1)
 def test_semantic_requires_source_not_name_similarity(self):
  p=self.semantic();p['claims'][0]['evidence_refs']=['made-up']
  with self.assertRaises(sem.SemanticsError):sem.validate(p)
  p=self.semantic();p['papers'][0]['access_scope']='ABSTRACT_READ'
  with self.assertRaises(sem.SemanticsError):sem.validate(p)
  p=self.semantic();p['relations'][0]['review_status']='SCIENTIFIC_REVIEWED'
  with self.assertRaises(sem.SemanticsError):sem.validate(p)
 def test_critic_cannot_claim_independence_without_receipt(self):
  p={'schema_version':'1.0','risk':'HIGH','main_claim':'Synthetic Claim requires further evidence',
    'main_evidence_refs':['P1#C1'],'counterarguments':[{'reason':'Synthetic competing explanation'}],
    'reviewer_verdict':'QUALIFY','review_method':'SELF_CHECK','review_evidence_refs':['P1#C1']}
  self.assertEqual(rv.validate(p)['review_status'],'INDEPENDENT_REVIEW_NOT_PERFORMED')
  p['review_method']='SEPARATE_CONTEXT_AGENT'
  with self.assertRaises(rv.ReviewError):rv.validate(p)
  p['reviewer_execution_receipt']='action-1';p['reviewer_source_access']='PDF hash abc'
  self.assertEqual(rv.validate(p)['review_status'],'REVIEW_RECORDED_NOT_TRUTH_VERIFIED')
 def test_gap_counterevidence_is_separate_from_scope_revision(self):
  vault=self.root/'vault'
  self.assertEqual(org.main(['init-vault','--vault',str(vault),'--execute','--acknowledge-empty-vault']),0)
  pkt={'topic_id':'syntheticTopic','research_question':'Synthetic timing fidelity question','mode':'FOCUSED_SYNTHESIS',
    'papers':[{'paper_uid':'p1','source_type':'PEER_REVIEWED_FULLTEXT','source_sha256':'a'*64,
        'claims':[{'claim_id':'c1','statement':'synthetic source challenge','source_locator':'PDF p2 Fig1',
          'question_dimension':'timing','study_context':'toy','study_design':'observational','evidence_kind':'FULLTEXT_FIGURE','stance':'CHALLENGES'}]}],
    'scientific_findings':[{'finding_id':'F1','statement':'Synthetic scoped finding only',
      'evidence_refs':['p1#c1'],'boundary':'Synthetic only','epistemic_label':'AGENT_SYNTHESIS_DRAFT'}],
    'candidate_gaps':[{'gap_id':'GAPx','statement':'Synthetic gap initial','evidence_refs':['p1#c1'],
      'verification':{'searches':[{'database':'test','date':'2026-10-14','query':'toy','status':'COMPLETED'}]}}]}
  def stage_run(packet,tag):
   source=self.dump(tag+'.json',packet);out=self.root/(tag+'-syn');self.assertEqual(sc.main(['stage','--input',str(source),'--output',str(out)]),0)
   stage=self.root/(tag+'-stage');self.assertEqual(kb.main(['stage','--vault',str(vault),'--synthesis-result',str(out/'synthesis_result.json'),'--stage-dir',str(stage)]),0)
   self.assertEqual(kb.main(['commit','--vault',str(vault),'--stage-dir',str(stage),'--approve-plan-sha256',org.file_sha(stage/'plan.json'),'--acknowledge-vault-write']),0)
  stage_run(pkt,'first')
  import copy
  q=copy.deepcopy(pkt)
  q['candidate_gaps'][0]['statement']='Synthetic gap with narrower scope'
  q['candidate_gaps'][0]['evidence_change']={'kind':'COUNTEREVIDENCE_FOUND','evidence_refs':['p1#c1'],
     'reason':'This scoped source challenges a critical scientific assumption.'}
  stage_run(q,'second')
  events=kb.event_history(vault)
  self.assertEqual([e['event_type'] for e in events],['EVIDENCE_ADDED','COUNTEREVIDENCE_FOUND','SCOPE_REFINED'])
  self.assertEqual(kb.gap_state(vault)['gaps']['GAPx']['current_statement'],'Synthetic gap initial')
  self.assertEqual(kb.gap_state(vault)['gaps']['GAPx']['workflow_status'],'PENDING_HUMAN')
  kb.verify_chain(kb.gap_state(vault),events)
 def test_new_method_data_note_not_mislabeled_topic(self):
  vault=self.root/'vault';org.main(['init-vault','--vault',str(vault),'--execute','--acknowledge-empty-vault'])
  updates=self.dump('updates.json',{'items':[{'kind':'METHOD','name':'ToyMethod','content':'Synthetic method assumptions and example are stated.','source_refs':['p#c']},
                      {'kind':'DATA','name':'ToyDataset','content':'Synthetic dataset characteristics and provenance.','source_refs':['p#c']}]})
  stage=self.root/'newstage';self.assertEqual(kb.main(['stage-knowledge','--vault',str(vault),'--updates-json',str(updates),'--stage-dir',str(stage),'--acknowledge-new-node']),0)
  self.assertEqual(kb.main(['commit','--vault',str(vault),'--stage-dir',str(stage),'--approve-plan-sha256',org.file_sha(stage/'plan.json'),'--acknowledge-vault-write']),0)
  method=(vault/'Methods/ToyMethod.md').read_text(encoding='utf8');data=(vault/'Data/ToyDataset.md').read_text(encoding='utf8')
  self.assertIn('asset_type: method',method);self.assertIn('asset_type: data_resource',data)
  self.assertNotIn('# 科学问题',method)
if __name__=='__main__':unittest.main()
# This block is picked up by unittest discovery despite appearing after the module main.
import paper_identity as ident
class PaperIdentityTests(unittest.TestCase):
 def test_doi_and_pdf_are_separate_identity_and_version(self):
  registry={'schema_version':'1.0','papers':[]}
  first=ident.resolve(registry,{'doi':'https://doi.org/10.1234/TEST', 'title':'A'})
  self.assertEqual(first['decision'],'NEW_IDENTITY_CANDIDATE')
  same=ident.resolve(registry,{'doi':'10.1234/test','title':'A'})
  self.assertEqual(same['decision'],'EXACT_IDENTITY_MATCH')
  registry['papers'][0]['pdf_sha256']='a'*64
  self.assertEqual(ident.resolve(registry,{'doi':'10.1234/test','pdf_sha256':'b'*64})['decision'],'VERSION_REVIEW_REQUIRED')
 def test_title_only_cannot_become_verified_paper(self):
  with self.assertRaises(ident.IdentityError):ident.resolve({'papers':[]},{'title':'fuzzy only'})
 def test_title_collision_holds_candidate(self):
  registry={'papers':[{'paper_uid':'P1','title':'Same Title','doi':'10.1234/a'}]}
  self.assertEqual(ident.resolve(registry,{'doi':'10.1234/b','title':'same title'})['decision'],'POSSIBLE_DUPLICATE_REVIEW')
