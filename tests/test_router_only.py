import copy, importlib.util, json, tempfile, unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('router_cli', BASE/'scripts'/'router_cli.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class UnifiedRootRouterTests(unittest.TestCase):
    def setUp(self): self.d=r.read(BASE/'examples/task_contract.example.json')
    def test_doctor(self): self.assertEqual(r.run(['doctor']),0)
    def test_schema(self):r.validate('task_contract',self.d)
    def test_all_schemas(self):
        for f in (BASE/'schemas'/'router').glob('*.schema.json'):
            r.js_module().Draft202012Validator.check_schema(r.read(f))
    def test_examples(self):
        for f in (BASE/'examples').glob('*.json'):
            name=f.name.split('.')[0]
            r.validate(name,r.read(f))
    def test_registry_for_current_stage(self):
        reg=r.read(BASE/'router/interfaces/module-registry.json')
        self.assertEqual(set(reg['modules']),set(r.ROUTES))
        self.assertEqual(reg['modules']['acquire']['status'],'INSTRUCTION_READY')
        self.assertEqual(reg['modules']['acquire']['implementation_ref'],'routes/acquire.md')
        self.assertEqual(reg['modules']['understand']['status'],'INSTRUCTION_READY')
        self.assertEqual(reg['modules']['understand']['implementation_ref'],'routes/understand.md')
        self.assertEqual(reg['modules']['organize']['status'],'INSTRUCTION_READY')
        self.assertEqual(reg['modules']['organize']['implementation_ref'],'routes/organize.md')
        self.assertEqual(reg['modules']['synthesize']['status'],'INSTRUCTION_READY')
    def test_no_business_implementations(self):
        self.assertTrue((BASE/'routes/acquire.md').exists())
        self.assertTrue((BASE/'routes/understand.md').exists())
        self.assertTrue((BASE/'routes/organize.md').exists())
        self.assertTrue((BASE/'routes/synthesize.md').exists())
        self.assertFalse((BASE/'legacy').exists())
    def test_single_unified_root(self):
        self.assertEqual(BASE.name,'personal-research-knowledge-evolution')
        for name in ['router','routes','references','adapters','schemas','scripts','tests']:
            self.assertTrue((BASE/name).is_dir())
    def test_skill_name(self):
        x=(BASE/'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(x.startswith('---\nname: personal-research-knowledge-evolution\n'))
    def test_no_duplicate_skill(self):
        self.assertEqual(len(list(BASE.rglob('SKILL.md'))),1)
    def test_reject_formal_commit(self):
        d=copy.deepcopy(self.d);d['permissions']['formal_commit']=True
        with self.assertRaises(r.PRKEError):r.validate('task_contract',d)
    def test_reject_destructive(self):
        d=copy.deepcopy(self.d);d['permissions']['destructive']=True
        with self.assertRaises(r.PRKEError):r.validate('task_contract',d)
    def test_reject_unready_running(self):
        d=copy.deepcopy(self.d);d['readiness']='CLARIFYING';d['task_state']='RUNNING'
        with self.assertRaises(r.PRKEError):r.validate('task_contract',d)
    def test_reject_budget(self):
        d=copy.deepcopy(self.d);d['budget']['limits']['search_calls']=1;d['budget']['usage']['search_calls']=2
        with self.assertRaises(r.PRKEError):r.validate('task_contract',d)
    def test_reject_duplicate_route(self):
        d=copy.deepcopy(self.d);d['support_routes'].append(d['primary_route'])
        with self.assertRaises(r.PRKEError):r.validate('task_contract',d)
    def test_reject_extra_field(self):
        d=copy.deepcopy(self.d);d['disable_governance']=True
        with self.assertRaises(r.PRKEError):r.validate('task_contract',d)
    def test_reject_vault(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'vault';p.mkdir();(p/'.obsidian').mkdir()
            with self.assertRaises(r.PRKEError):r.safe_folder(p/'runs')
    def test_init_task(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(r.run(['init-task','--output-dir',t,'--route','acquire','--objective','找论文']),0)
            f=next(Path(t).glob('task-*/task_contract.json'));d=r.read(f)
            self.assertEqual(d['task_state'],'CLARIFYING')
            self.assertEqual(d['primary_route'],'acquire')
            self.assertFalse(d['permissions']['formal_commit'])
    def test_checkpoint(self):
        with tempfile.TemporaryDirectory() as t:
            r.run(['init-task','--output-dir',t,'--route','understand','--objective','解读论文'])
            f=next(Path(t).glob('task-*/task_contract.json'))
            self.assertEqual(r.run(['checkpoint','--task-file',str(f)]),0)
            ck=next((f.parent/'checkpoints').glob('*.json'))
            self.assertEqual(r.read(ck)['contract_sha256'],r.hashlib.sha256(f.read_bytes()).hexdigest())
    def test_capabilities(self): self.assertEqual(r.run(['capabilities']),0)

if __name__=='__main__':unittest.main()
