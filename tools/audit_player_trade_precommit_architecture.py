#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, ast, hashlib, json, re, sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FILES=("handlers/player_interaction.py","systems/player_interaction_system.py","handlers/auction_house.py","systems/auction_house_system.py","db.py","main.py","keyboards.py")
TABLES=("player_activity_sessions","player_interaction_requests","player_trades","player_trade_offers","player_trade_events","player_trade_history","inventory_reservations")
ACTIVE=("editing","confirming","committing")
TERMINAL=("completed","cancelled","expired","failed")

def sha256(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def exists(conn,name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None

def columns(conn,name):
    return [r[1] for r in conn.execute(f'PRAGMA table_info("{name}")')] if exists(conn,name) else []

def indexes(conn,name):
    return [r[1] for r in conn.execute(f'PRAGMA index_list("{name}")')] if exists(conn,name) else []

def funcs(tree):
    return Counter(n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)))

def attr_assignments(tree,name):
    out=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign): targets=n.targets
        elif isinstance(n,ast.AnnAssign): targets=[n.target]
        else: continue
        if any(isinstance(t,ast.Attribute) and t.attr==name for t in targets): out.append(n.lineno)
    return out

def finding(items,severity,code,message,evidence=None):
    row={"severity":severity,"code":code,"message":message}
    if evidence is not None: row["evidence"]=evidence
    items.append(row)

def source_audit(root,findings):
    data={}
    for rel in FILES:
        p=root/rel
        if not p.exists():
            data[rel]={"exists":False}; finding(findings,"CRITICAL","missing_file",f"Відсутній {rel}"); continue
        text=p.read_text(encoding="utf-8-sig")
        try: tree=ast.parse(text,filename=str(p))
        except SyntaxError as exc:
            data[rel]={"exists":True,"syntax_valid":False,"error":str(exc)}; finding(findings,"CRITICAL","syntax_error",f"{rel}: {exc}"); continue
        count=funcs(tree)
        row={"exists":True,"syntax_valid":True,"size":p.stat().st_size,"sha256":sha256(p),"duplicate_top_level_functions":{k:v for k,v in sorted(count.items()) if v>1}}
        data[rel]=row
        if rel=="handlers/player_interaction.py":
            assigns=attr_assignments(tree,"process_new_updates")
            guard=count.get("_install_player_trade_handler_level_navigation_guard_12_6_6",0)
            old=count.get("install_player_trade_navigation_lock_12_6_4",0)
            regs=count.get("register_player_interaction_handlers",0)
            prefixes=re.findall(r'pi:[a-z0-9_]+:',text)
            duplicates={k:v for k,v in Counter(prefixes).items() if v>12}
            row.update({"process_new_updates_assignments":assigns,"handler_level_guard_count":guard,"dispatcher_lock_count":old,"register_function_count":regs,"high_frequency_callback_prefixes":duplicates,"has_status_noop":"def trade_status_noop(message):" in text,"has_continue_handling":"ContinueHandling" in text,"has_inline_refresh":"🔄 Оновити" in text and "pi:te:open:" in text,"has_amount_input":"TRADE_AMOUNT_INPUT_STATE_12_6_3" in text})
            if assigns: finding(findings,"CRITICAL","dispatcher_wrapper","Trade navigation змінює process_new_updates",assigns)
            if old: finding(findings,"CRITICAL","obsolete_lock","Застарілий dispatcher lock досі існує",old)
            if guard!=1: finding(findings,"CRITICAL","handler_guard_count","Очікується один handler-level guard",guard)
            if regs>1: finding(findings,"REVIEW","layered_registration","register_player_interaction_handlers має історичні wrapper-рівні; фінально бажана консолідація",regs)
            for ok,label in ((row["has_status_noop"],"status no-op"),(row["has_continue_handling"],"ContinueHandling"),(row["has_inline_refresh"],"inline Refresh"),(row["has_amount_input"],"amount input")):
                if not ok: finding(findings,"CRITICAL","missing_handler_contract",f"Відсутній контракт: {label}")
        if rel=="systems/player_interaction_system.py":
            required=("create_player_trade_from_accepted_request","cancel_player_trade","expire_stale_player_trades","recover_active_player_trades_after_restart","get_active_player_trade","get_player_trade_editor_state","set_player_trade_item_offer","remove_player_trade_item_offer","set_player_trade_gold_offer","reserve_inventory_for_trade","release_trade_inventory_reservations","get_item_trade_policy")
            missing=[x for x in required if count.get(x,0)<1]
            atomic=any(count.get(x,0) for x in ("complete_player_trade","commit_player_trade","finalize_player_trade","execute_player_trade_commit"))
            row.update({"required_trade_functions":{x:count.get(x,0) for x in required},"missing_required_trade_functions":missing,"has_begin_immediate":"BEGIN IMMEDIATE" in text.upper(),"has_atomic_commit_api":bool(atomic)})
            if missing: finding(findings,"CRITICAL","missing_domain_api","Відсутні API trade foundation",missing)
            if not atomic: finding(findings,"INFO","atomic_commit_pending","Atomic commit ще не реалізовано, очікувано до 12.7.0")
    return data

def database_audit(root,findings):
    p=root/"game.db"
    if not p.exists(): finding(findings,"CRITICAL","missing_db","Відсутня game.db"); return {"exists":False}
    conn=sqlite3.connect(f"file:{p.as_posix()}?mode=ro",uri=True)
    try:
        quick=conn.execute("PRAGMA quick_check").fetchone()[0]; fk=conn.execute("PRAGMA foreign_key_check").fetchall()
        out={"exists":True,"quick_check":quick,"foreign_key_issue_count":len(fk),"tables":{},"status_counts":{},"orphan_counts":{}}
        if quick!="ok": finding(findings,"CRITICAL","quick_check",str(quick))
        if fk: finding(findings,"CRITICAL","foreign_keys","Foreign-key issues",len(fk))
        for table in TABLES:
            present=exists(conn,table); out["tables"][table]={"exists":present,"columns":columns(conn,table),"indexes":indexes(conn,table)}
            if not present: finding(findings,"CRITICAL","missing_table",f"Відсутня таблиця {table}")
        if exists(conn,"player_trades"):
            required={"id","request_id","initiator_user_id","recipient_user_id","status","revision","initiator_ready","recipient_ready","initiator_confirmed","recipient_confirmed","expires_at","completed_at","cancelled_at","cancel_reason"}
            missing=sorted(required-set(columns(conn,"player_trades"))); out["tables"]["player_trades"]["missing_precommit_columns"]=missing
            if missing: finding(findings,"CRITICAL","schema_not_ready","player_trades не готова до confirmation state machine",missing)
            for status in ACTIVE+TERMINAL: out["status_counts"][status]=conn.execute("SELECT COUNT(*) FROM player_trades WHERE status=?",(status,)).fetchone()[0]
        if exists(conn,"inventory_reservations") and exists(conn,"player_trades"):
            sql=("SELECT COUNT(*) FROM inventory_reservations r LEFT JOIN player_trades t ON r.reservation_type='player_trade' AND r.reference_id=t.id "
                 "WHERE r.reservation_type='player_trade' AND (t.id IS NULL OR t.status IN ('completed','cancelled','expired','failed'))")
            n=conn.execute(sql).fetchone()[0]; out["orphan_counts"]["trade_reservations"]=n
            if n: finding(findings,"CRITICAL","orphan_reservations","Є orphan trade reservations",n)
        if exists(conn,"player_activity_sessions") and exists(conn,"player_trades"):
            sql=("SELECT COUNT(*) FROM player_activity_sessions s LEFT JOIN player_trades t ON s.activity_type='trade' AND CAST(s.reference_id AS INTEGER)=t.id "
                 "WHERE s.activity_type='trade' AND (t.id IS NULL OR t.status NOT IN ('editing','confirming','committing'))")
            n=conn.execute(sql).fetchone()[0]; out["orphan_counts"]["trade_sessions"]=n
            if n: finding(findings,"CRITICAL","orphan_sessions","Є orphan trade activity sessions",n)
        return out
    finally: conn.close()

def readiness(result,findings):
    h=result["source"].get("handlers/player_interaction.py",{}); s=result["source"].get("systems/player_interaction_system.py",{}); d=result["database"]
    checks={"handler_level_guard":h.get("handler_level_guard_count")==1,"no_dispatcher_wrapper":not h.get("process_new_updates_assignments") and h.get("dispatcher_lock_count")==0,"status_noop":bool(h.get("has_status_noop")),"inline_refresh":bool(h.get("has_inline_refresh")),"manual_amount_input":bool(h.get("has_amount_input")),"trade_domain_api":not s.get("missing_required_trade_functions"),"trade_schema":all(d.get("tables",{}).get(t,{}).get("exists") for t in TABLES),"ready_confirm_columns":not d.get("tables",{}).get("player_trades",{}).get("missing_precommit_columns"),"database_integrity":d.get("quick_check")=="ok" and d.get("foreign_key_issue_count")==0,"no_orphan_state":not any(d.get("orphan_counts",{}).values()),"atomic_commit_pending":not s.get("has_atomic_commit_api")}
    result["readiness"]=checks; core=[k for k in checks if k!="atomic_commit_pending"]; result["ready_for_12_7"]=all(checks[k] for k in core)
    if not result["ready_for_12_7"]: finding(findings,"CRITICAL","not_ready", "Є блокери перед 12.7",[k for k in core if not checks[k]])

def markdown(result):
    L=["# Stage 12.6.7: Pre-commit Architecture Audit","",f"- **Дата:** {result['generated_at']}",f"- **Verdict:** `{result['verdict']}`",f"- **Готовність до 12.7:** `{'YES' if result['ready_for_12_7'] else 'NO'}`","- **Режим:** read-only; gameplay mutations = 0; database writes = 0","","## Архітектурні результати",""]
    for k,v in result["readiness"].items(): L.append(f"- {'✅' if v else '❌'} `{k}`")
    L += ["","## Findings",""]
    for x in result["findings"]: L.append(f"- **{x['severity']} / {x['code']}**: {x['message']}"+(f" Evidence: `{json.dumps(x['evidence'],ensure_ascii=False)}`" if 'evidence' in x else ""))
    L += ["","## Обов'язковий план для 12.7.0","","1. Редагувати поточні function blocks на місці, без нових override-визначень.","2. Явні переходи: `editing → confirming → committing → completed`.","3. Будь-яка зміна offer збільшує `revision` і скидає ready/confirmed обох.","4. Фінальний transfer виконується однією транзакцією `BEGIN IMMEDIATE`.","5. До transfer повторно перевірити ownership, quantity, reservations, item policy, gold і bag capacity.","6. Commit має бути ідемпотентним після `completed`.","7. Успіх записує events/history, звільняє sessions/reservations і повертає `main_kb()`.","","## Зафіксовані нюанси","","- Історичні register-wrapper рівні допускаються як REVIEW, але мають бути консолідовані до фіналу Stage 12.","- Atomic commit ще не реалізований, що очікувано до 12.7.0.","- Inline `🔄 Оновити` залишається необхідним для синхронізації двох учасників.",""]
    return "\n".join(L)

def run(root):
    findings=[]; result={"stage":"12.6.7","generated_at":datetime.now(timezone.utc).isoformat(),"mode":"read_only","gameplay_mutations":0,"database_writes":0,"source":source_audit(root,findings),"database":database_audit(root,findings),"findings":findings}
    readiness(result,findings); sev={x["severity"] for x in findings}; result["verdict"]="FAIL" if "CRITICAL" in sev else ("REVIEW" if "REVIEW" in sev else "PASS"); return result

def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",default=str(Path(__file__).resolve().parents[1])); p.add_argument("--json",default="PLAYER_TRADE_12_6_7_PRECOMMIT_ARCHITECTURE_AUDIT.json"); p.add_argument("--markdown",default="PLAYER_TRADE_12_6_7_PRECOMMIT_ARCHITECTURE_AUDIT.md"); a=p.parse_args(); root=Path(a.root).resolve(); result=run(root)
    (root/a.json).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8"); (root/a.markdown).write_text(markdown(result),encoding="utf-8")
    print("[OK] Player trade pre-commit architecture audit"); print(f"- verdict: {result['verdict']}"); print(f"- ready for 12.7: {'YES' if result['ready_for_12_7'] else 'NO'}"); print(f"- findings: {len(result['findings'])}"); print("- gameplay mutations: 0"); print("- database writes: 0"); print(f"- JSON: {a.json}"); print(f"- Markdown: {a.markdown}")
    for x in result["findings"]: print(f"  [{x['severity']}] {x['code']}: {x['message']}")
    if result["verdict"]=="FAIL": raise SystemExit(1)
if __name__=="__main__": main()
