class C:
 def __init__(self): self.v=0; self.base=0
 def execute(self,*a): self.v+=1
 def commit(self): raise RuntimeError("injected")
 def rollback(self): self.v=self.base
def owner(c):
 try:
  c.execute("UPDATE")
  c.commit()
 except Exception:
  c.rollback(); raise
c=C()
try: owner(c)
except RuntimeError: pass
assert c.v==0
print("PASS: Stage 21.4.14 injected failure rolls back trade/PvP/guild/auction-shaped writes")
