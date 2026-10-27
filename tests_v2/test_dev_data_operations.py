from __future__ import annotations
import unittest
from rom_v2.domain.dev_data_operations import *

class Ops:
    def __init__(self,fail=False): self.calls=[]; self.fail=fail
    def _call(self,name,c):
        self.calls.append((name,c.operation_key,c.value))
        if self.fail: raise RuntimeError("boom")
    def give(self,c): self._call("give",c)
    def reset(self,c): self._call("reset",c)
    def set_value(self,c): self._call("set",c)
class Receipts:
    def __init__(self,existing=False): self.existing=existing; self.records=[]
    def exists(self,key): return self.existing
    def record(self,c,actor): self.records.append((c.operation_id,actor))
class Uow:
    def __init__(self): self.commits=0; self.rollbacks=0
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def commit(self): self.commits+=1
    def rollback(self): self.rollbacks+=1

def service(fail=False,existing=False):
    o,r,u=Ops(fail),Receipts(existing),Uow(); return DevDataOperationsService(o,r,u),o,r,u
def auth(ok=True): return DevAuthorization(ok,1,"authorized" if ok else "denied")

class Tests(unittest.TestCase):
    def test_denied_before_any_side_effect(self):
        s,o,r,u=service()
        with self.assertRaises(PermissionError): s.execute(auth(False),DevDataCommand("x",DevOperationKind.GIVE,2,"gold",5))
        self.assertEqual((o.calls,r.records,u.commits,u.rollbacks),([],[],0,0))
    def test_give_reset_set_delegate_and_commit(self):
        cases=((DevOperationKind.GIVE,5,"give"),(DevOperationKind.RESET,None,"reset"),(DevOperationKind.SET,7,"set"))
        for i,(kind,value,name) in enumerate(cases):
            s,o,r,u=service(); result=s.execute(auth(),DevDataCommand(str(i),kind,2,"key",value))
            self.assertEqual(o.calls[0][0],name); self.assertEqual(r.records,[(str(i),1)]); self.assertEqual(u.commits,1); self.assertFalse(result.replayed)
    def test_replay_has_no_mutation_or_receipt(self):
        s,o,r,u=service(existing=True); result=s.execute(auth(),DevDataCommand("x",DevOperationKind.SET,2,"level",3))
        self.assertTrue(result.replayed); self.assertEqual((o.calls,r.records,u.commits,u.rollbacks),([],[],0,0))
    def test_failure_rolls_back_and_does_not_record(self):
        s,o,r,u=service(fail=True)
        with self.assertRaises(RuntimeError): s.execute(auth(),DevDataCommand("x",DevOperationKind.GIVE,2,"gold",5))
        self.assertEqual(r.records,[]); self.assertEqual(u.commits,0); self.assertEqual(u.rollbacks,1)
    def test_command_validation_fail_closed(self):
        with self.assertRaises(ValueError): DevDataCommand("",DevOperationKind.GIVE,1,"x",1)
        with self.assertRaises(ValueError): DevDataCommand("x",DevOperationKind.GIVE,1,"x",None)
        with self.assertRaises(ValueError): DevDataCommand("x",DevOperationKind.RESET,1,"x",0)
    def test_module_has_no_sql_or_runtime_dependencies(self):
        # Inspect executable syntax rather than comments/docstrings to avoid false positives.
        import ast, inspect, rom_v2.domain.dev_data_operations as module
        tree = ast.parse(inspect.getsource(module))
        imported_roots = set()
        called_names = set()
        string_literals = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0].lower() for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0].lower())
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id.lower())
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr.lower())
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                string_literals.add(node.value.lower())
        self.assertTrue({"sqlite3", "aiogram"}.isdisjoint(imported_roots))
        self.assertTrue({"getenv", "execute", "executemany"}.isdisjoint(called_names))
        sql_fragments = ("insert into", "update users", "delete from")
        self.assertFalse(any(fragment in literal for literal in string_literals for fragment in sql_fragments))
if __name__=="__main__": unittest.main()
