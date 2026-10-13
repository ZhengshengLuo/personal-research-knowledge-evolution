"""Synthetic fixtures ONLY. Scientific truths cannot be inferred from this test suite."""
from __future__ import annotations
import json,sys,tempfile,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'scripts'))
import synthesize_engine as se
import synthesize_cli as sc
import knowledge_cli as k
import organize_cli as o
import trigger_cli as t

def packet(gap='GAP-A',statement='Candidate gap pending external verification',version=1):
    return {'topic_id':'SIF-监测','research_question':'How does SIF monitor extreme vegetation response?',
            'mode':'FOCUSED_SYNTHESIS','papers':[{'paper_uid':'paper-test-1','source_type':'PEER_REVIEWED_FULLTEXT','source_independence_key':'same_flux_dataset',
            'source_sha256':'a'*64,'claims':[{'claim_id':'c1','statement':'synthetic support only', 'source_locator':'PDF p.2 Fig.1',
                'question_dimension':'timing','study_context':'synthetic forest','study_design':'observational',
                'evidence_kind':'FULLTEXT_FIGURE','stance':'SUPPORTS'}]}],
            'scientific_findings':[{'finding_id':'F1','statement':'Synthetic within-case observation, not a verified domain consensus',
                'evidence_refs':['paper-test-1#c1'],'boundary':'Synthetic case, no generalization','epistemic_label':'AGENT_SYNTHESIS_DRAFT'}],
            'candidate_gaps':[{'gap_id':gap,'statement':statement,'evidence_refs':['paper-test-1#c1'],
                'verification':{'searches':[{'database':'OpenAlex','date':'2026-10-13','query':'SIF timing fidelity','status':'COMPLETED'}],
                   'closest_prior_work':['This is a synthetic placeholder; not scientific evidence']}}]}

class SynthTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory();self.addCleanup(self.td.cleanup);self.d=Path(self.td.name)
        self.v=self.d/'vault';o.main(['init-vault','--vault',str(self.v),'--execute','--acknowledge-empty-vault'])
    def sample(self,p=None,where=None):
        x=where or self.d/'input.json';x.write_text(json.dumps(p or packet(),ensure_ascii=False),encoding='utf-8');return x
    def synthesis(self,p=None,name='run'):
        x=self.sample(p,self.d/(name+'.json'));out=self.d/name
        self.assertEqual(sc.main(['stage','--input',str(x),'--output',str(out)]),0)
        return out
    def stage(self,syn,name='batch'):
        stage=self.d/name
        self.assertEqual(k.main(['stage','--vault',str(self.v),'--synthesis-result',str(syn/'synthesis_result.json'),'--stage-dir',str(stage)]),0)
        return stage
    def commit(self,stage,allow=True):
        args=['commit','--vault',str(self.v),'--stage-dir',str(stage),'--approve-plan-sha256',o.file_sha(stage/'plan.json')]
        if allow:args.append('--acknowledge-vault-write')
        return k.main(args)
    def test_synthesis_input_and_draft(self):
        out=self.synthesis();res=se.read(out/'synthesis_result.json')
        self.assertEqual(res['audit']['status'],'COMPLETED')
        self.assertEqual(res['audit']['content_verdict'],'SCIENTIFIC_REVIEW_REQUIRED')
        self.assertEqual(len(res['evidence_matrix']),1)
        self.assertIn('不得', (out/'Synthesis_Report_DRAFT.md').read_text(encoding='utf-8'))
    def test_invalid_claim_location(self):
        p=packet();p['papers'][0]['claims'][0]['source_locator']=''
        with self.assertRaises(se.ScienceError):se.build(p)
    def test_invalid_gap_ref(self):
        p=packet();p['candidate_gaps'][0]['evidence_refs']=['invented#claim']
        with self.assertRaises(se.ScienceError):se.build(p)
    def test_abstract_cannot_claim_figure(self):
        p=packet();p['papers'][0]['source_type']='ABSTRACT_ONLY'
        with self.assertRaises(se.ScienceError):se.build(p)
    def test_internal_requires_run_id(self):
        p=packet();p['papers'][0]['source_type']='INTERNAL_EXPERIMENT'
        with self.assertRaises(se.ScienceError):se.build(p)
    def test_unclear_novelty_partial(self):
        p=packet();p['candidate_gaps'][0].pop('verification')
        self.assertEqual(se.build(p)['audit']['status'],'PARTIAL')
    def test_no_vault_write_at_stage(self):
        syn=self.synthesis();stage=self.stage(syn)
        self.assertFalse((self.v/'Research Gap Overview.md').exists())
        self.assertFalse((self.v/'.prke/gaps/events.jsonl').exists())
        self.assertEqual(self.commit(stage,False),2)
    def test_approved_and_idempotent_staging(self):
        syn=self.synthesis();stage=self.stage(syn);self.assertEqual(self.commit(stage),0)
        self.assertEqual(self.commit(stage),2)
        self.assertTrue((self.v/'Research Gap Overview.md').is_file())
        history=k.event_history(self.v);self.assertEqual(len(history),1)
        k.verify_chain(k.gap_state(self.v),history)
    def test_human_text_preserved_and_refinement_pending(self):
        syn=self.synthesis();self.commit(self.stage(syn))
        topic=self.v/'Topics/科学问题/SIF-监测.md'
        with topic.open('a',encoding='utf-8') as f:f.write('我的人工科学判断不要改。\n')
        p=packet(statement='Narrowed candidate gap')
        syn2=self.synthesis(p,name='run2');stage=self.stage(syn2,name='batch2')
        self.assertEqual(self.commit(stage),0)
        self.assertIn('我的人工科学判断不要改。',topic.read_text(encoding='utf-8'))
        g=k.gap_state(self.v)['gaps']['GAP-A']
        self.assertEqual(g['current_statement'],'Candidate gap pending external verification')
        self.assertEqual(g['pending_statement'],'Narrowed candidate gap')
        self.assertEqual(g['workflow_status'],'PENDING_HUMAN')
        dec=self.d/'decision.json';dec.write_text(json.dumps({'gap_id':'GAP-A','action':'APPROVE_REVISION','rationale':'Confirmed narrower scope after reviewing evidence'},ensure_ascii=False),encoding='utf-8')
        ds=self.d/'decision-stage'
        self.assertEqual(k.main(['stage-decision','--vault',str(self.v),'--decision-json',str(dec),'--stage-dir',str(ds),'--acknowledge-researcher-decision']),0)
        self.assertEqual(self.commit(ds),0)
        self.assertEqual(k.gap_state(self.v)['gaps']['GAP-A']['current_statement'],'Narrowed candidate gap')
        self.assertEqual(len(k.event_history(self.v)),3)
    def test_safe_target_conflict(self):
        syn=self.synthesis();st=self.stage(syn)
        (self.v/'Research Gap Overview.md').write_text('human created independently',encoding='utf-8')
        self.assertEqual(self.commit(st),2)
        self.assertEqual((self.v/'Research Gap Overview.md').read_text(),'human created independently')
    def test_fake_first_priority_blocked(self):
        p=packet(statement='首次 SIF monitoring in the world')
        with self.assertRaises(se.ScienceError):se.build(p)
    def test_trigger_idempotent_and_exact_threshold(self):
        state=self.d/'worker';manifest=self.d/'papers.json'
        records=[{'paper_uid':f'P{i}','topic_relevant':True,'source_check':'VERIFIED','reading_status':'READ_AND_VERIFIED'} for i in range(9)]
        def write():manifest.write_text(json.dumps({'topic_id':'SIF-监测','papers':records},ensure_ascii=False),encoding='utf-8')
        write();self.assertEqual(t.main(['check','--manifest',str(manifest),'--state-dir',str(state)]),0)
        self.assertIsNone(se.read(state/'topic_triggers.json')['topics']['SIF-监测']['pending'])
        records.append(dict(records[0]));records.append({'paper_uid':'P9','topic_relevant':True,'source_check':'VERIFIED','reading_status':'DEEP_COMPLETED'})
        write();self.assertEqual(t.main(['check','--manifest',str(manifest),'--state-dir',str(state)]),0)
        run=se.read(state/'topic_triggers.json')['topics']['SIF-监测']['pending']['run_key']
        self.assertEqual(t.main(['check','--manifest',str(manifest),'--state-dir',str(state)]),0)
        self.assertEqual(se.read(state/'topic_triggers.json')['topics']['SIF-监测']['pending']['run_key'],run)
    def test_science_scope_not_conflated(self):
        p=packet();p['papers'].append(dict(p['papers'][0]))
        with self.assertRaises(se.ScienceError):se.build(p)
    def test_duplicate_same_synthesis_snapshot_is_rejected(self):
        syn=self.synthesis();self.commit(self.stage(syn))
        self.assertEqual(k.main(['stage','--vault',str(self.v),'--synthesis-result',str(syn/'synthesis_result.json'),'--stage-dir',str(self.d/'repeat')]),2)
        self.assertEqual(len(k.event_history(self.v)),1)
    def test_method_knowledge_requires_existing_or_new_node_approval(self):
        f=self.d/'updates.json'
        f.write_text(json.dumps({'items':[{'kind':'METHOD','name':'PCMCI','content':'Synthetic explanation of a statistical dependence method not a causal treatment effect.', 'source_refs':['paper-test-1#c1']}]},ensure_ascii=False),encoding='utf-8')
        stage=self.d/'knowledge-stage'
        args=['stage-knowledge','--vault',str(self.v),'--updates-json',str(f),'--stage-dir',str(stage)]
        self.assertEqual(k.main(args),2)
        self.assertEqual(k.main(args+['--acknowledge-new-node']),0)
        self.assertFalse((self.v/'Methods/PCMCI.md').exists())
        self.assertEqual(self.commit(stage),0)
        self.assertTrue((self.v/'Methods/PCMCI.md').exists())
    def test_knowledge_preserves_existing_human_method(self):
        method=self.v/'Methods/PCMCI.md';method.write_text('# PCMCI\n\nHuman explanation important.\n',encoding='utf-8')
        f=self.d/'updates.json';f.write_text(json.dumps({'items':[{'kind':'METHOD','name':'PCMCI','content':'Synthetic method comparison based on an independently reviewed full source.', 'source_refs':['paper-test-1#c1']}]},ensure_ascii=False),encoding='utf-8')
        stage=self.d/'knowledge-stage'
        self.assertEqual(k.main(['stage-knowledge','--vault',str(self.v),'--updates-json',str(f),'--stage-dir',str(stage)]),0)
        self.assertEqual(self.commit(stage),0)
        self.assertIn('Human explanation important.',method.read_text(encoding='utf-8'))
    def test_formal_idea_requires_decision_and_approved_commit(self):
        syn=self.synthesis();self.commit(self.stage(syn))
        d=self.d/'decision.json';d.write_text(json.dumps({'gap_id':'GAP-A','action':'APPROVE_IDEA','rationale':'Confirmed the constrained and falsifiable research question','idea_title':'Example research idea','idea_summary':'Synthetic proposed hypothesis with clear controls, evaluation and failure modes.'},ensure_ascii=False),encoding='utf-8')
        stage=self.d/'idea-stage';args=['stage-decision','--vault',str(self.v),'--decision-json',str(d),'--stage-dir',str(stage)]
        self.assertEqual(k.main(args),2)
        self.assertEqual(k.main(args+['--acknowledge-researcher-decision']),0)
        self.assertFalse(list((self.v/'Ideas').glob('*.md')))
        self.assertEqual(self.commit(stage),0)
        self.assertEqual(len(list((self.v/'Ideas').glob('*.md'))),1)
    def test_soak_without_elapsed_cannot_be_pass(self):
        import soak_cli, time
        root=self.d/'soak';root.mkdir();(root/'config.json').write_text(json.dumps({'start_unix':time.time(),'hours_requested':24}),encoding='utf-8')
        with (root/'heartbeats.jsonl').open('w',encoding='utf-8') as f:
            for i in range(2):f.write(json.dumps({'unix':time.time()+i,'utc':'test'})+'\n')
        self.assertEqual(soak_cli.main(['verify','--output',str(root)]),2)
    def test_doctors(self):
        self.assertEqual(sc.main(['doctor']),0);self.assertEqual(k.main(['doctor']),0);self.assertEqual(t.main(['doctor']),0)

if __name__=='__main__':unittest.main()
