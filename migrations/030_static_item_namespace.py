# ROM Stage 18.1.8a: idempotent static item namespace migration.
import sqlite3

MAPPING = {201: 401, 202: 402, 203: 403, 204: 404, 301: 501, 401: 601, 402: 602, 501: 701, 502: 702, 503: 703, 504: 704, 505: 705, 506: 706, 507: 707, 508: 708, 509: 709, 510: 710, 511: 711, 512: 712, 513: 713, 514: 714, 515: 715, 516: 716, 517: 717, 518: 718, 519: 719, 520: 720, 521: 721, 522: 722, 523: 723, 524: 724, 525: 725, 526: 726, 527: 727, 528: 728, 900: 501, 10000: 502, 50000: 503}
DIRECT_ITEM_COLUMNS = (('auction_lots', 'item_ref_id'), ('character_name_changes', 'item_id'), ('crystal_shop_purchases', 'item_id'), ('inventory', 'item_id'), ('inventory_runes', 'rune_item_id'), ('player_trade_offers', 'item_id'))
TEMP_OFFSET = 900000000

def _q(name):
    return '"' + str(name).replace('"', '""') + '"'

def _columns(conn, table):
    return {str(r[1]) for r in conn.execute(f"PRAGMA table_info({_q(table)})")}

def _stage_18_1_8f_canonical_state(conn):
    legacy_ids = (201,202,203,204,301,900,10000,50000)
    canonical_ids = (401,402,403,404,501,502,503,601,602,*range(701,729))
    legacy = int(conn.execute("SELECT COUNT(*) FROM items WHERE id IN (%s)" % ','.join('?' for _ in legacy_ids), legacy_ids).fetchone()[0])
    present = {int(row[0]) for row in conn.execute("SELECT id FROM items WHERE id IN (%s)" % ','.join('?' for _ in canonical_ids), canonical_ids)}
    return legacy, present == set(canonical_ids)

def migrate(conn):
    legacy_count, canonical_complete = _stage_18_1_8f_canonical_state(conn)
    if canonical_complete:
        if conn.execute("SELECT 1 FROM items WHERE id=900").fetchone():
            for table, column in DIRECT_ITEM_COLUMNS:
                if column in _columns(conn, table):
                    conn.execute(f"UPDATE {_q(table)} SET {_q(column)}=501 WHERE {_q(column)}=900")
            conn.execute("DELETE FROM items WHERE id=900")
            if not conn.in_transaction:
                conn.commit()
        return {"success": True, "already_canonical": True, "legacy_900_reconciled": bool(legacy_count), "mapping_entries": len(MAPPING)}
    own_transaction = not conn.in_transaction
    fk_before = int(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    if own_transaction:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("BEGIN IMMEDIATE")
    try:
        # Phase 0: merge legacy row 900 into canonical old identity 301 before renumbering.
        legacy_exists = conn.execute("SELECT 1 FROM items WHERE id=900").fetchone()
        canonical_old_exists = conn.execute("SELECT 1 FROM items WHERE id=301").fetchone()
        if legacy_exists:
            if not canonical_old_exists:
                conn.execute("UPDATE items SET id=301 WHERE id=900")
            else:
                for table, column in DIRECT_ITEM_COLUMNS:
                    if column in _columns(conn, table):
                        conn.execute(f"UPDATE {_q(table)} SET {_q(column)}=301 WHERE {_q(column)}=900")
                conn.execute("DELETE FROM items WHERE id=900")
        effective_mapping = {old: new for old, new in MAPPING.items() if old != 900}
        present = {int(r[0]) for r in conn.execute("SELECT id FROM items WHERE id IN (%s)" % ','.join('?' for _ in effective_mapping), tuple(effective_mapping))}
        # Phase 1: unique source identities move to temporary IDs.
        for table, column in DIRECT_ITEM_COLUMNS:
            if column not in _columns(conn, table):
                continue
            for old in present:
                conn.execute(f"UPDATE {_q(table)} SET {_q(column)}=? WHERE {_q(column)}=?", (TEMP_OFFSET + old, old))
        for old in present:
            conn.execute("UPDATE items SET id=? WHERE id=?", (TEMP_OFFSET + old, old))
        # Phase 2: temporary IDs move to final canonical IDs.
        for old, new in effective_mapping.items():
            temp = TEMP_OFFSET + old
            if not conn.execute("SELECT 1 FROM items WHERE id=?", (temp,)).fetchone():
                continue
            conn.execute("UPDATE items SET id=? WHERE id=?", (new, temp))
            for table, column in DIRECT_ITEM_COLUMNS:
                if column in _columns(conn, table):
                    conn.execute(f"UPDATE {_q(table)} SET {_q(column)}=? WHERE {_q(column)}=?", (new, temp))
        if own_transaction:
            conn.commit()
    except Exception:
        if own_transaction:
            conn.rollback()
        raise
    finally:
        if own_transaction:
            conn.execute(f"PRAGMA foreign_keys={fk_before}")
    return {"success": True, "mapping_entries": len(MAPPING)}

def run(conn):
    return migrate(conn)
