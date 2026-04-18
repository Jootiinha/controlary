from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Card:
    id: Optional[int]
    nome: str
    account_id: Optional[int] = None
    observacao: Optional[str] = None
    conta_nome: Optional[str] = None  # preenchido em JOINs

    @classmethod
    def from_row(cls, row) -> "Card":
        keys = list(row.keys())
        conta = row["conta_nome"] if "conta_nome" in keys else None
        return cls(
            id=row["id"],
            nome=row["nome"],
            account_id=row["account_id"] if "account_id" in keys else None,
            observacao=row["observacao"] if "observacao" in keys else None,
            conta_nome=conta,
        )
