from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CardInvoice:
    id: Optional[int]
    cartao_id: int
    ano_mes: str
    valor_total: float
    status: str
    pago_em: Optional[str] = None
    conta_pagamento_id: Optional[int] = None
    observacao: Optional[str] = None
    cartao_nome: Optional[str] = None
    historico: bool = False

    @classmethod
    def from_row(cls, row) -> "CardInvoice":
        keys = list(row.keys())
        cn = row["cartao_nome"] if "cartao_nome" in keys and row["cartao_nome"] else None
        hist = (
            bool(row["historico"])
            if "historico" in keys and row["historico"] is not None
            else False
        )
        return cls(
            id=row["id"],
            cartao_id=row["cartao_id"],
            ano_mes=row["ano_mes"],
            valor_total=float(row["valor_total"] or 0),
            status=row["status"],
            pago_em=row["pago_em"] if "pago_em" in keys else None,
            conta_pagamento_id=row["conta_pagamento_id"]
            if "conta_pagamento_id" in keys
            else None,
            observacao=row["observacao"] if "observacao" in keys else None,
            cartao_nome=cn,
            historico=hist,
        )
