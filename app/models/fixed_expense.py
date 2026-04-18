from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class FixedExpense:
    id: Optional[int]
    nome: str
    valor_mensal: float
    dia_referencia: int
    forma_pagamento: str
    conta_id: Optional[int] = None
    observacao: Optional[str] = None
    ativo: bool = True
    conta_nome: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "FixedExpense":
        keys = list(row.keys())
        ativo = bool(row["ativo"]) if "ativo" in keys else True
        cn = row["conta_nome"] if "conta_nome" in keys and row["conta_nome"] else None
        return cls(
            id=row["id"],
            nome=row["nome"],
            valor_mensal=row["valor_mensal"],
            dia_referencia=row["dia_referencia"],
            forma_pagamento=row["forma_pagamento"],
            conta_id=row["conta_id"] if "conta_id" in keys else None,
            observacao=row["observacao"] if "observacao" in keys else None,
            ativo=ativo,
            conta_nome=cn,
        )
