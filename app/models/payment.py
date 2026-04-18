from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Payment:
    id: Optional[int]
    valor: float
    descricao: str
    data: str
    conta_id: Optional[int]
    forma_pagamento: str
    observacao: Optional[str] = None
    conta_nome: Optional[str] = None  # JOIN / exibição

    @classmethod
    def from_row(cls, row) -> "Payment":
        keys = list(row.keys())
        cid = row["conta_id"] if "conta_id" in keys else None
        nome = None
        if "conta_nome" in keys and row["conta_nome"]:
            nome = row["conta_nome"]
        elif "conta" in keys and row["conta"]:
            nome = row["conta"]
        return cls(
            id=row["id"],
            valor=row["valor"],
            descricao=row["descricao"],
            data=row["data"],
            conta_id=cid,
            forma_pagamento=row["forma_pagamento"],
            observacao=row["observacao"],
            conta_nome=nome,
        )
