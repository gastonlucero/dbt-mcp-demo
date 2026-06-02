import contextlib
import logging

import psycopg2

from src.config import settings

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def get_cursor():
    """PostgreSQL connection with 15-second statement timeout."""
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            connect_timeout=5,
        )
        cursor = conn.cursor()
        cursor.execute("SET statement_timeout = '15s'")
        yield cursor
    except psycopg2.OperationalError as e:
        logger.error("Postgres connection failed: %s", str(e))
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
