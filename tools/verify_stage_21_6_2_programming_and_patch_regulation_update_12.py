from pathlib import Path
import hashlib,zipfile
from xml.etree import ElementTree as ET
p=Path("ROM_PROGRAMMING_AND_PATCH_REGULATION.docx")
assert p.is_file()
assert hashlib.sha256(p.read_bytes()).hexdigest()=="4201d89d6ba70940d647b2f1481e3a40eb92a5bef1c7e7b1e6f10e979ac2113f"
with zipfile.ZipFile(p) as z: xml=z.read("word/document.xml")
r=ET.fromstring(xml); text=" ".join((n.text or "") for n in r.iter() if n.tag.endswith("}t"))
required=("Update 12","Stage 21.6.2","Stage 21.6 ще не закрито","FINAL OVERRIDE","git add . заборонено","game.db-wal","game.db-shm","API_READY","ADAPTER_CONNECTED","RUNTIME_DISPATCH_VERIFIED","END_TO_END_ACCEPTED","Retry budget","Isolated SQLite snapshot","Patch self-smoke","Audit REVIEW_REQUIRED","Closed-stage namespace")
for token in required: assert token in text,token
assert text.count("Update 12")>=3
print("PASS: Programming and Patch Regulation Update 12 contract")
