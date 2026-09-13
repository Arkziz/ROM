"""
Location management module.
"""

from .connection import conn, cursor


def get_current_location(user_id):
    cursor.execute("""
    SELECT current_location
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return "start_path"

    if row[0] is None or row[0] == "":
        return "start_path"

    return row[0]

def set_current_location(user_id, location_id):
    cursor.execute("""
    UPDATE users
    SET current_location=?
    WHERE user_id=?
    """, (location_id, user_id))

    conn.commit()
