from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Subscription:
    id: Optional[int]
    nome: str
    categoria: Optional[str]
    valor_mensal: float
    dia_cobranca: int
    forma_pagamento: str
    status: str = "ativa"
    observacao: Optional[str] = None
    account_id: Optional[int] = None
    card_id: Optional[int] = None
    meio_label: Optional[str] = None  # exibição: nome da conta ou cartão

    @classmethod
    def from_row(cls, row) -> "Subscription":
        keys = list(row.keys())
        aid = row["account_id"] if "account_id" in keys else None
        cid = row["card_id"] if "card_id" in keys else None
        label = None
        if "meio_label" in keys and row["meio_label"]:
            label = row["meio_label"]
        elif "conta_cartao" in keys and row["conta_cartao"]:
            label = row["conta_cartao"]
        return cls(
            id=row["id"],
            nome=row["nome"],
            categoria=row["categoria"],
            valor_mensal=row["valor_mensal"],
            dia_cobranca=row["dia_cobranca"],
            forma_pagamento=row["forma_pagamento"],
            status=row["status"],
            observacao=row["observacao"],
            account_id=aid,
            card_id=cid,
            meio_label=label,
        )
