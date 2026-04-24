"""Template comum competência + livro-caixa (subclasses em *months_service / fixed)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import sqlite3

from app.services.competencia_ledger import data_iso_no_mes
from app.utils.mes_ano import MesAno

__all__ = ["data_iso_no_mes", "MonthlyLedgerService"]


class MonthlyLedgerService(ABC):
    """Marca competência mensal e sincroniza débito/crédito no livro-caixa."""

    @abstractmethod
    def set_status(
        self,
        entity_id: int,
        ano_mes: MesAno,
        marcado: bool,
        *,
        conn: Optional[sqlite3.Connection] = None,
        **kwargs: Any,
    ) -> None:
        ...
