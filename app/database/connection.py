"""Gerenciamento de conexão com o SQLite."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional

from app.utils.paths import database_path


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(database_path()), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 8000;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except sqlite3.OperationalError:
        pass
    return conn


@contextmanager
def use(conn: Optional[sqlite3.Connection]) -> Iterator[sqlite3.Connection]:
    """Reutiliza ``conn`` ou abre uma transação nova (Unit of Work)."""
    if conn is not None:
        yield conn
        return
    with transaction() as c:
        yield c


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
