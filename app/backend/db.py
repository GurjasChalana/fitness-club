import psycopg2
from psycopg2.extras import RealDictCursor

# DB Connection Config
DB_CONFIG = {
    "host": "localhost",
    "database": "fitness_club",
    "user": "postgres",
    "password": "postgres"
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# --- Execute a query ---
def execute_query(query, params=None, fetch=False):
    conn = None
    result = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        if fetch:
            result = cur.fetchall()
        conn.commit()
        cur.close()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
    return result
