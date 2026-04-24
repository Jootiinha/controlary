from __future__ import annotations

from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.account import Account
from app.services import accounts_service


def test_use_reuses_outer_connection(test_db_path: Path) -> None:
    _ = test_db_path
    with transaction() as outer:
        accounts_service.create(Account(id=None, nome="C1", saldo_inicial=0.0), conn=outer)
        rows = outer.execute("SELECT id FROM accounts").fetchall()
        assert len(rows) == 1
