#!/usr/bin/env python3
"""ROM Stage 21.11.1c: implement the API-ready two-location V2 catalog.

Creates pure immutable content/API code, focused tests, a smoke verifier and
contract artifacts. It does not open SQLite, connect runtime/Telegram, mutate
V1 production sources, or add content beyond Початок Шляху and Темний Бір.
"""
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGE = "21.11.1c"
BRANCH = "rewrite/rom-v2"
PARENT = "68443a6b8de0875533db30a6b94123d4f07e7579"
PREREQ = Path("reports/stage_21_11_1b_resolved_location_catalog_parity.json")
SELF = Path("patch/patch_21_11_1c_implement_location_catalog.py")
MODULE = Path("rom_v2/content/location_catalog.py")
TEST = Path("tests_v2/test_location_catalog.py")
TOOL = Path("tools/check_stage_21_11_1c_location_catalog.py")
REPORT = Path("reports/stage_21_11_1c_location_catalog_implementation.json")
DOC = Path("MD/STAGE_21_11_1C_LOCATION_CATALOG_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_11_1c_failure_rollback.json")
TARGETS = (SELF, MODULE, TEST, TOOL, REPORT, DOC)
ALLOWED_DIRTY = {
    SELF.as_posix(), "ROM_FULL_DUMP.txt", FAILURE.as_posix(),
    "reports/stage_21_11_1_failure_rollback.json",
    "reports/stage_21_11_1a_failure_rollback.json",
    "reports/stage_21_11_1b_failure_rollback.json",
    "reports/v2_ci_failure.json", "reports/v2_ci_result.json",
}
PROTECTED = (
    "game.db", "game.db-wal", "game.db-shm", ".env", "rom_v2/.env",
    ".runtime/v2/db/rom_v2.db",
)

class PatchError(RuntimeError):
    """Mandatory implementation/publication gate failure."""


def run(command, root, check=True, env=None):
    process = subprocess.run(command, cwd=root, text=True, capture_output=True,
                             encoding="utf-8", errors="replace", env=env)
    if check and process.returncode:
        raise PatchError(f"command_failed:{command}:{process.stdout[-1500:]}:{process.stderr[-1500:]}")
    return process


def git(root, *args, check=True):
    return run(["git", *args], root, check)


def root_dir():
    for candidate in (Path.cwd(), Path(__file__).resolve().parent.parent):
        if (candidate / ".git").exists() and (candidate / "rom_v2").is_dir():
            return candidate
    raise PatchError("rom_root_not_found")


def sha(path):
    if not path.is_file(): return None
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def protected(root):
    return {name:sha(root/name) for name in PROTECTED}


def load_json(path):
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise PatchError(f"json_object_required:{path}")
    return value


def status_records(root):
    raw=git(root,"status","--porcelain=v1","-z").stdout
    out=[]; parts=raw.split("\0"); i=0
    while i<len(parts):
        record=parts[i]; i+=1
        if not record: continue
        status=record[:2]; path=record[3:].replace("\\","/")
        if status[0] in "RC":
            if i>=len(parts): raise PatchError("invalid_porcelain_rename")
            path=parts[i].replace("\\","/"); i+=1
        out.append((status,path))
    return out


def snapshot(root):
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder=root/"backup"/f"stage_21_11_1c_{stamp}"; state={}
    for relative in TARGETS:
        src=root/relative; state[relative.as_posix()]=src.exists()
        if src.exists():
            dst=folder/relative; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    return folder,state


def restore(root,folder,state):
    git(root,"reset","--mixed",check=False); restored=[]
    if folder is None:return restored
    for relative in TARGETS:
        dst=root/relative; src=folder/relative
        if state.get(relative.as_posix()) and src.exists():
            dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); restored.append(relative.as_posix())
        elif dst.exists(): dst.unlink(); restored.append(f"removed:{relative.as_posix()}")
    return restored


def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+".tmp"); temp.write_text(text,encoding="utf-8",newline="\n"); os.replace(temp,path)


def clean_bytecode(root):
    removed=[]
    for base in (root/"rom_v2",root/"tests_v2",root/"tests",root/"tools"):
        if not base.exists():continue
        for path in base.rglob("*.pyc"):
            removed.append(path.relative_to(root).as_posix()); path.unlink(missing_ok=True)
        for directory in sorted(base.rglob("__pycache__"),key=lambda x:len(x.parts),reverse=True):
            try:directory.rmdir()
            except OSError:pass
    return removed


def module_text():
    return '''"""Canonical immutable V2 catalog for the two V1-parity locations.

This module is pure content. It has no persistence, Telegram, clock or random
source dependency. Stable technical IDs are never reformatted for presentation.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

CITY_NODE_ID = "city"
START_PATH_ID = "start_path"
DARK_FOREST_ID = "dark_forest"
UNKNOWN_LOCATION_NAME = "🧭 Невідома місцевість"

@dataclass(frozen=True, slots=True)
class LocationDefinition:
    """Immutable canonical definition of one huntable location."""
    location_id: str
    name: str
    description: str
    level_min: int
    level_max: int
    unlock_level: int
    boss_name: str
    mob_names: tuple[str, ...]

_START_PATH = LocationDefinition(
    location_id=START_PATH_ID,
    name="🌿 Початок Шляху",
    description=("Перші стежки за межами табору мандрівників. Тут ще не панує справжня темрява, "
                 "але за деревами вже чути рух диких звірів, шурхіт павутини та слабке світіння "
                 "рунічних рослин. Саме тут новачки вчаться виживати, берегти спорядження, "
                 "користуватися зіллями та повертатися до міста перед тим, як ризик стане занадто великим."),
    level_min=1, level_max=5, unlock_level=1, boss_name="🐺 Ватажок зграї",
    mob_names=("🐗 Дикий кабан","🌱 Рунічний паросток","🦡 Лісовий борсук","💎 Рунічний слимак",
               "🦇 Лісовий кажан","🪸 Печерний кровосос","🕷️ Малий павук","🧪 Павук-кислотник",
               "🐺 Молодий вовк","👻 Вовк-примара"),
)
_DARK_FOREST = LocationDefinition(
    location_id=DARK_FOREST_ID,
    name="🌲 Темний Бір",
    description=("Глибша частина лісу, куди не заходять випадкові подорожні. Між старими деревами "
                 "ховаються гоблінські дозори, шамани, берсерки та слуги темних рун. Повітря тут "
                 "важче, а кожен крок може привести до засідки або стародавніх руїн."),
    level_min=6, level_max=10, unlock_level=6, boss_name="👑 Король Гоблінів",
    mob_names=("👺 Малий гоблін","🧪 Гоблін-знахар","🗡️ Гоблін-розвідник","🧙 Гоблін-шаман",
               "🪓 Гоблін-берсерк","🔥 Гоблін-піроман","🛡️ Гоблін-страж","🏹 Гоблін-мисливець",
               "👹 Гоблін-ватажок","💀 Темний гоблін"),
)

LOCATION_ORDER: tuple[str, ...] = (START_PATH_ID, DARK_FOREST_ID)
LOCATIONS: Mapping[str, LocationDefinition] = MappingProxyType({
    START_PATH_ID: _START_PATH,
    DARK_FOREST_ID: _DARK_FOREST,
})
WORLD_NODE_ORDER: tuple[str, ...] = (CITY_NODE_ID, START_PATH_ID, DARK_FOREST_ID)
LOCATION_GRAPH: Mapping[str, tuple[str, ...]] = MappingProxyType({
    CITY_NODE_ID: (START_PATH_ID,),
    START_PATH_ID: (CITY_NODE_ID, DARK_FOREST_ID),
    DARK_FOREST_ID: (START_PATH_ID,),
})

def get_location(location_id: str) -> LocationDefinition | None:
    """Return a canonical location or None; never fabricate an unknown record."""
    return LOCATIONS.get(str(location_id or "").strip())

def require_location(location_id: str) -> LocationDefinition:
    """Return a canonical location and fail closed for unknown technical IDs."""
    normalized=str(location_id or "").strip(); location=LOCATIONS.get(normalized)
    if location is None: raise KeyError(f"unknown location_id: {normalized}")
    return location

def get_location_display_name(location_id: str) -> str:
    """Resolve the exact localized name without leaking/title-casing an ID."""
    return require_location(location_id).name

def is_location_unlocked(location_id: str, player_level: int) -> bool:
    """Apply the V1 unlock threshold for one known location."""
    if isinstance(player_level,bool) or not isinstance(player_level,int) or player_level<1:
        raise ValueError("player_level must be a positive integer")
    return player_level >= require_location(location_id).unlock_level

def get_unlocked_locations(player_level: int) -> tuple[LocationDefinition, ...]:
    """Enumerate unlocked locations in canonical catalog order."""
    if isinstance(player_level,bool) or not isinstance(player_level,int) or player_level<1:
        raise ValueError("player_level must be a positive integer")
    return tuple(LOCATIONS[key] for key in LOCATION_ORDER if player_level>=LOCATIONS[key].unlock_level)

def get_adjacent_nodes(node_id: str) -> tuple[str, ...]:
    """Return static adjacent nodes and fail closed for an unknown world node."""
    normalized=str(node_id or "").strip()
    if normalized not in LOCATION_GRAPH: raise KeyError(f"unknown world node: {normalized}")
    return LOCATION_GRAPH[normalized]

def are_adjacent(from_node: str, to_node: str) -> bool:
    """Check one canonical graph edge without permitting inferred travel."""
    normalized_to=str(to_node or "").strip()
    if normalized_to not in LOCATION_GRAPH: raise KeyError(f"unknown world node: {normalized_to}")
    return normalized_to in get_adjacent_nodes(from_node)

def validate_location_catalog() -> None:
    """Validate IDs, order, levels, references and symmetric graph integrity."""
    if tuple(LOCATIONS) != LOCATION_ORDER: raise ValueError("location order mismatch")
    if set(LOCATION_GRAPH) != set(WORLD_NODE_ORDER): raise ValueError("world graph node mismatch")
    for key, location in LOCATIONS.items():
        if key != location.location_id: raise ValueError(f"location identity mismatch: {key}")
        if not (1 <= location.level_min <= location.level_max): raise ValueError(f"invalid level range: {key}")
        if location.unlock_level != location.level_min: raise ValueError(f"unlock mismatch: {key}")
        if not location.name or not location.description or not location.boss_name or not location.mob_names:
            raise ValueError(f"incomplete location: {key}")
        if len(location.mob_names) != len(set(location.mob_names)): raise ValueError(f"duplicate mob: {key}")
    for node, neighbors in LOCATION_GRAPH.items():
        if len(neighbors) != len(set(neighbors)): raise ValueError(f"duplicate edge: {node}")
        for neighbor in neighbors:
            if node not in LOCATION_GRAPH.get(neighbor, ()): raise ValueError(f"asymmetric edge: {node}->{neighbor}")

validate_location_catalog()
'''


def test_text():
    return '''import importlib
import unittest
from dataclasses import FrozenInstanceError
from rom_v2.content.location_catalog import *

class LocationCatalogTest(unittest.TestCase):
    def test_exact_two_location_identity_order_and_levels(self):
        self.assertEqual(LOCATION_ORDER,("start_path","dark_forest"))
        self.assertEqual(tuple(LOCATIONS),LOCATION_ORDER)
        self.assertEqual(len(LOCATIONS),2)
        start=require_location("start_path"); dark=require_location("dark_forest")
        self.assertEqual((start.name,start.level_min,start.level_max,start.unlock_level),("🌿 Початок Шляху",1,5,1))
        self.assertEqual((dark.name,dark.level_min,dark.level_max,dark.unlock_level),("🌲 Темний Бір",6,10,6))
        self.assertEqual(len(start.mob_names),10); self.assertEqual(len(dark.mob_names),10)
        self.assertEqual(start.boss_name,"🐺 Ватажок зграї"); self.assertEqual(dark.boss_name,"👑 Король Гоблінів")
    def test_immutable_and_restart_stable(self):
        with self.assertRaises(TypeError): LOCATIONS["x"]=require_location("start_path")  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError): require_location("start_path").name="x"  # type: ignore[misc]
        def snapshot(module):
            return (
                module.LOCATION_ORDER,
                tuple((key, location.location_id, location.name, location.description,
                       location.level_min, location.level_max, location.unlock_level,
                       location.boss_name, location.mob_names)
                      for key, location in module.LOCATIONS.items()),
                tuple(module.LOCATION_GRAPH.items()),
            )
        module=importlib.import_module("rom_v2.content.location_catalog")
        before=snapshot(module)
        module=importlib.reload(module)
        after=snapshot(module)
        self.assertEqual(before,after)
    def test_unknown_ids_fail_closed_and_never_leak(self):
        self.assertIsNone(get_location("unknown_zone"))
        for call in (lambda:require_location("unknown_zone"),lambda:get_location_display_name("unknown_zone"),lambda:get_adjacent_nodes("unknown_zone"),lambda:are_adjacent("city","unknown_zone")):
            with self.assertRaises(KeyError): call()
    def test_unlock_boundaries_and_order(self):
        self.assertEqual(tuple(x.location_id for x in get_unlocked_locations(1)),("start_path",))
        self.assertEqual(tuple(x.location_id for x in get_unlocked_locations(5)),("start_path",))
        self.assertEqual(tuple(x.location_id for x in get_unlocked_locations(6)),("start_path","dark_forest"))
        self.assertTrue(is_location_unlocked("start_path",1)); self.assertFalse(is_location_unlocked("dark_forest",5)); self.assertTrue(is_location_unlocked("dark_forest",6))
        for invalid in (0,-1,True,1.0,"6"):
            with self.assertRaises(ValueError): get_unlocked_locations(invalid)  # type: ignore[arg-type]
    def test_exact_symmetric_graph_and_no_direct_city_dark_forest_edge(self):
        self.assertEqual(WORLD_NODE_ORDER,("city","start_path","dark_forest"))
        self.assertEqual(get_adjacent_nodes("city"),("start_path",))
        self.assertEqual(get_adjacent_nodes("start_path"),("city","dark_forest"))
        self.assertEqual(get_adjacent_nodes("dark_forest"),("start_path",))
        self.assertFalse(are_adjacent("city","dark_forest")); self.assertFalse(are_adjacent("dark_forest","city"))
        for node in WORLD_NODE_ORDER:
            for neighbor in get_adjacent_nodes(node): self.assertTrue(are_adjacent(neighbor,node))
    def test_catalog_validation(self):
        self.assertIsNone(validate_location_catalog())

if __name__ == "__main__": unittest.main()
'''


def tool_text():
    return '''#!/usr/bin/env python3
"""Smoke check for Stage 21.11.1c Location Catalog."""
from pathlib import Path
import sys

# Direct execution sets sys.path[0] to ROM/tools. Add the project root so the
# repository-local rom_v2 package resolves without installation or PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rom_v2.content.location_catalog import *

def main():
    validate_location_catalog()
    assert LOCATION_ORDER == ("start_path","dark_forest") and len(LOCATIONS)==2
    assert get_location_display_name("start_path") == "🌿 Початок Шляху"
    assert get_location_display_name("dark_forest") == "🌲 Темний Бір"
    assert tuple(x.location_id for x in get_unlocked_locations(5)) == ("start_path",)
    assert tuple(x.location_id for x in get_unlocked_locations(6)) == ("start_path","dark_forest")
    assert LOCATION_GRAPH == {"city":("start_path",),"start_path":("city","dark_forest"),"dark_forest":("start_path",)}
    try: require_location("third_location")
    except KeyError: pass
    else: raise AssertionError("unknown location did not fail closed")
    print("Stage 21.11.1c Location Catalog smoke: PASS")
    return 0
if __name__ == "__main__": raise SystemExit(main())
'''


def run_ci(root,env):
    temp=root/"reports/.stage_21_11_1c_ci.tmp.json"; temp.unlink(missing_ok=True)
    process=run([sys.executable,"-B","tools/run_v2_ci.py","--project-root",str(root),"--json-out",str(temp)],root,False,env)
    if not temp.is_file():raise PatchError(f"ci_report_missing:{process.stderr[-1000:]}")
    data=load_json(temp);temp.unlink(missing_ok=True)
    if process.returncode or data.get("status")!="PASS":raise PatchError(f"canonical_v2_ci_failed:{json.dumps(data,ensure_ascii=False)}")
    return data


def main():
    root=root_dir(); folder=None; state={}; before=protected(root)
    try:
        contract=load_json(root/PREREQ)
        if git(root,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
        if contract.get("stage")!="21.11.1b" or contract.get("conclusion")!="GO_TO_IMPLEMENTATION" or contract.get("unresolved_contracts")!=[]:
            raise PatchError("invalid_stage_21_11_1b_prerequisite")
        evidence=contract.get("canonical_v1_evidence",{})
        if evidence.get("location_count")!=2 or tuple(evidence.get("catalog_order",()))!=("start_path","dark_forest"):
            raise PatchError("two_location_evidence_missing")
        print("[1/10] [PASS] Stage 21.11.1b zero-unresolved two-location prerequisite verified.")
        if git(root,"branch","--show-current").stdout.strip()!=BRANCH:raise PatchError("wrong_branch")
        if git(root,"diff","--cached","--name-only").stdout.strip():raise PatchError("pre_staged_changes")
        unexpected=sorted(path for status,path in status_records(root) if path not in ALLOWED_DIRTY or (path!=SELF.as_posix() and status[0]!=" "))
        if unexpected:raise PatchError(f"unexpected_dirty:{unexpected}")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        folder,state=snapshot(root);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
        write(root/MODULE,module_text());write(root/TEST,test_text());write(root/TOOL,tool_text())
        print("[4/10] [PASS] Immutable two-location catalog, localized resolver, unlock API and world graph implemented.")
        for target in (SELF,MODULE,TEST,TOOL):py_compile.compile(str(root/target),doraise=True)
        print("[5/10] [PASS] Python compile gate passed for patch, implementation, tests and smoke tool.")
        env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0"
        targeted=run([sys.executable,"-B","-m","unittest",TEST.as_posix(),"-v"],root,False,env)
        if targeted.returncode:raise PatchError(f"targeted_tests_failed:{targeted.stdout}:{targeted.stderr}")
        smoke=run([sys.executable,"-B",TOOL.as_posix()],root,False,env)
        if smoke.returncode or "PASS" not in smoke.stdout:raise PatchError(f"smoke_failed:{smoke.stdout}:{smoke.stderr}")
        print("[6/10] [PASS] Two-location identity, immutability, restart, unlock, graph and fail-closed tests passed.")
        removed=clean_bytecode(root);ci=run_ci(root,env)
        print(f"[7/10] [PASS] Canonical six-gate V2 CI passed after removing {len(removed)} bytecode artifact(s).")
        after=protected(root)
        if before!=after:raise PatchError(f"protected_runtime_changed:{sorted(k for k in before if before[k]!=after[k])}")
        print("[8/10] [PASS] V1 sources, unrelated V2 sources, DB sidecars and protected configuration remained byte-identical.")
        report={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"source_contract":PREREQ.as_posix(),"implementation":MODULE.as_posix(),"tests":TEST.as_posix(),"smoke_tool":TOOL.as_posix(),"locations":[{"location_id":"start_path","name":"🌿 Початок Шляху","level_min":1,"level_max":5,"unlock_level":1},{"location_id":"dark_forest","name":"🌲 Темний Бір","level_min":6,"level_max":10,"unlock_level":6}],"world_graph":{"city":["start_path"],"start_path":["city","dark_forest"],"dark_forest":["start_path"]},"implemented":["immutable_two_location_catalog","stable_technical_ids","localized_names_without_id_fallback","level_unlock_policy","symmetric_world_graph","unknown_id_fail_closed","restart_stability","content_validation"],"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED","removed_bytecode_before_ci":removed,"canonical_v2_ci":ci,"backup_path":folder.relative_to(root).as_posix()}
        write(root/REPORT,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        doc='''# Stage 21.11.1c - Location Catalog implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED**\n\n## Implemented catalog\n\n1. `start_path` - **🌿 Початок Шляху**, levels 1-5, unlock level 1.\n2. `dark_forest` - **🌲 Темний Бір**, levels 6-10, unlock level 6.\n\nNo third location, inferred content or changed V1 threshold was added. The static graph is `city <-> start_path <-> dark_forest`. Unknown IDs fail closed and are never title-cased into user-facing text.\n\n## Scope\n\nImplemented a pure immutable content module, localized lookup, unlock enumeration, graph API, internal validation, focused unit tests and a smoke verifier. SQLite, Telegram/runtime wiring and production adapters remain disconnected.\n'''
        write(root/DOC,doc)
        print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
        expected={x.as_posix() for x in TARGETS};git(root,"add","-f","--",*sorted(expected))
        staged={x.strip().replace("\\","/") for x in git(root,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
        if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
        result=git(root,"commit","-m","Stage 21.11.1c: implement Location Catalog",check=False)
        if result.returncode:raise PatchError(f"commit_failed:{result.stdout}:{result.stderr}")
        commit=git(root,"rev-parse","HEAD").stdout.strip();changed={x.strip().replace("\\","/") for x in git(root,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x.strip()}
        if changed!=expected:raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root/FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Location Catalog implementation committed: {commit}")
        print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})")
        print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED")
        print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
    except Exception as error:
        restored=restore(root,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],root,False)
        failure={"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","failed_at_utc":datetime.now(timezone.utc).isoformat(),"reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False}
        write(root/FAILURE,json.dumps(failure,ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1

if __name__=="__main__":raise SystemExit(main())
