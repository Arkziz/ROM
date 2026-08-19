#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "systems" / "rune_system.py"


def require(value, message):
    if not value:
        raise AssertionError(message)


def load_function():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_add_stack_quantity_in_transaction"
    ]
    require(len(functions) == 1, "transactional stack helper must be unique")
    namespace = {}
    exec(ast.get_source_segment(source, functions[0]), namespace)
    return namespace["_add_stack_quantity_in_transaction"], source


def make_db(capacity=40):
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY, bag_slots INTEGER)")
    conn.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, name TEXT, max_stack INTEGER)")
    conn.execute("CREATE TABLE inventory(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_id INTEGER, quantity INTEGER)")
    conn.execute("INSERT INTO users(user_id,bag_slots) VALUES(1,?)", (capacity,))
    conn.execute("INSERT INTO items(id,name,max_stack) VALUES(501,'Руна',10)")
    return conn


def quantities(conn):
    return [row[0] for row in conn.execute(
        "SELECT quantity FROM inventory WHERE user_id=1 AND item_id=501 ORDER BY id"
    ).fetchall()]


def main():
    add, source = load_function()

    # Full bag, but the rune fits into an existing partial stack.
    conn = make_db(40)
    conn.execute("INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,501,9)")
    for index in range(39):
        conn.execute("INSERT INTO items(id,name,max_stack) VALUES(?,?,1)", (1000+index, f'X{index}'))
        conn.execute("INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,?,1)", (1000+index,))
    result = add(conn, 1, 501, 1)
    require(result.get("success"), result)
    require(quantities(conn) == [10], quantities(conn))
    require(result.get("required_new_rows") == 0, result)

    # Full bag, new row required. No partial mutation may remain.
    conn = make_db(40)
    conn.execute("INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,501,9)")
    for index in range(39):
        conn.execute("INSERT INTO items(id,name,max_stack) VALUES(?,?,1)", (2000+index, f'Y{index}'))
        conn.execute("INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,?,1)", (2000+index,))
    before = quantities(conn)
    result = add(conn, 1, 501, 2)
    require(not result.get("success") and result.get("code") == "bag_full", result)
    require(quantities(conn) == before, "capacity failure partially mutated a stack")

    # One free slot and boundary crossing.
    conn = make_db(40)
    conn.execute("INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,501,8)")
    for index in range(38):
        conn.execute("INSERT INTO items(id,name,max_stack) VALUES(?,?,1)", (3000+index, f'Z{index}'))
        conn.execute("INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,?,1)", (3000+index,))
    result = add(conn, 1, 501, 5)
    require(result.get("success"), result)
    require(quantities(conn) == [10, 3], quantities(conn))

    require(source.count("# ROM 17.4.1 RUNE TRANSACTIONAL STACK CAPACITY RECOVERY") == 1, "marker")
    print("[PASS] Stage 17.4.1 rune transactional stack capacity")


if __name__ == "__main__":
    main()
