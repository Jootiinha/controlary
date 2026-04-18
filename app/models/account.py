from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Account:
    id: Optional[int]
    nome: str
    observacao: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Account":
        return cls(
            id=row["id"],
            nome=row["nome"],
            observacao=row["observacao"],
        )
