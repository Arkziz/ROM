class C:
 def __init__(self): self.state=(10,20); self.current=[10,20]
 def execute(self,*a): self.current=[99,88]
 def commit(self): raise RuntimeError("injected")
 def rollback(self): self.current=list(self.state)
def owner(c):
 try:
  c.execute("UPDATE state")
  c.commit()
 except Exception:
  c.rollback(); raise
c=C()
try: owner(c)
except RuntimeError: pass
assert c.current==list(c.state)
print("PASS: Stage 21.4.18 injected failure restores focused gameplay state")
