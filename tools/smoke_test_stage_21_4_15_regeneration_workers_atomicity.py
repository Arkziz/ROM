class C:
 def __init__(self): self.hp=5; self.mp=3; self.ts=10; self.base=(5,3,10)
 def execute(self,*a): self.hp=9; self.mp=8; self.ts=20
 def commit(self): raise RuntimeError("injected")
 def rollback(self): self.hp,self.mp,self.ts=self.base
def tick(c):
 try:
  c.execute("UPDATE regen")
  c.commit()
 except Exception:
  c.rollback(); raise
c=C()
try: tick(c)
except RuntimeError: pass
assert (c.hp,c.mp,c.ts)==c.base
print("PASS: Stage 21.4.15 injected worker failure rolls back values and timestamps")
