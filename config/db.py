import os
import logging
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not defined in environment variables")

# Initialize connection pool with autocommit=True for Supabase PgBouncer compatibility
# PgBouncer (port 6543) in transaction mode conflicts with psycopg3 implicit transactions
db_pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    open=True,
    kwargs={"row_factory": dict_row, "autocommit": True, "prepare_threshold": None}
)

def get_db():
    """Context manager or dependency to get a connection from the pool."""
    with db_pool.connection() as conn:
        yield conn

def query_db(query: str, params: list = None, fetch_one: bool = False, fetch_all: bool = False):
    """Executes a query and handles cursor lifecycle."""
    try:
        with db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or [])
                if fetch_one:
                    return cur.fetchone()
                if fetch_all:
                    return cur.fetchall()
                # If query returns rows (e.g. INSERT ... RETURNING)
                if cur.description:
                    try:
                        return cur.fetchall()
                    except Exception:
                        pass
                return None
    except Exception as e:
        logger.error(f"query_db error | query={query[:80]} | error={e}")
        raise
