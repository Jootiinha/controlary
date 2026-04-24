from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Card:
    id: Optional[int]
    nome: str
    account_id: Optional[int] = None
    observacao: Optional[str] = None
    dia_pagamento_fatura: int = 10
    conta_nome: Optional[str] = None  # preenchido em JOINs

    @classmethod
    def unknown(cls, label: str = "—") -> "Card":
        return cls(
            id=None,
            nome=label,
            account_id=None,
            observacao=None,
            dia_pagamento_fatura=10,
            conta_nome=None,
        )

    @classmethod
    def from_row(cls, row) -> "Card":
        keys = list(row.keys())
        conta = row["conta_nome"] if "conta_nome" in keys else None
        dia = int(row["dia_pagamento_fatura"]) if "dia_pagamento_fatura" in keys else 10
        return cls(
            id=row["id"],
            nome=row["nome"],
            account_id=row["account_id"] if "account_id" in keys else None,
            observacao=row["observacao"] if "observacao" in keys else None,
            dia_pagamento_fatura=dia,
            conta_nome=conta,
        )
