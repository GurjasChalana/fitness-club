import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# DB Connection Config
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "fitness_club"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

# SQLAlchemy engine/session (ORM path)
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@contextmanager
def get_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_conn():
    """Raw psycopg2 connection (legacy)."""
    return psycopg2.connect(**DB_CONFIG)


# --- Execute a query ---
def execute_query(query, params=None, fetch=False):
    """Retained for ad-hoc SQL usage; prefer SQLAlchemy sessions."""
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
