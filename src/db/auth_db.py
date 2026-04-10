import traceback
from psycopg2.extras import RealDictCursor

from src.db.connection import get_connection
from src.security.auth import hash_password



def get_user_by_username(username: str):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, username, password_hash, role, is_active, created_at
            FROM users
            WHERE username = %s
            LIMIT 1;
        """, (username,))

        return cur.fetchone()
    except Exception:
        traceback.print_exc()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def create_user(username: str, password: str, role: str = "user"):
    conn = None
    cur = None
    try:
        if role not in ("admin", "user"):
            raise ValueError("role must be 'admin' or 'user'")

        password_hash = hash_password(password)

        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            RETURNING id, username, role, is_active, created_at;
        """, (username, password_hash, role))

        created_user = cur.fetchone()
        conn.commit()

        if created_user:
            return created_user

        # If user already exists, return existing record
        cur.execute("""
            SELECT id, username, role, is_active, created_at
            FROM users
            WHERE username = %s
            LIMIT 1;
        """, (username,))
        return cur.fetchone()

    except Exception:
        if conn:
            conn.rollback()
        traceback.print_exc()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


