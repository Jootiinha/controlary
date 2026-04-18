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
    cartao_id: Optional[int] = None
    category_id: Optional[int] = None
    conta_nome: Optional[str] = None
    cartao_nome: Optional[str] = None
    categoria_nome: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Payment":
        keys = list(row.keys())
        cid = row["conta_id"] if "conta_id" in keys else None
        nome = None
        if "conta_nome" in keys and row["conta_nome"]:
            nome = row["conta_nome"]
        elif "conta" in keys and row["conta"]:
            nome = row["conta"]
        cartao_id = row["cartao_id"] if "cartao_id" in keys else None
        cnome = row["cartao_nome"] if "cartao_nome" in keys and row["cartao_nome"] else None
        cat_id = row["category_id"] if "category_id" in keys else None
        catn = row["categoria_nome"] if "categoria_nome" in keys and row["categoria_nome"] else None
        return cls(
            id=row["id"],
            valor=row["valor"],
            descricao=row["descricao"],
            data=row["data"],
            conta_id=cid,
            forma_pagamento=row["forma_pagamento"],
            observacao=row["observacao"],
            cartao_id=cartao_id,
            category_id=cat_id,
            conta_nome=nome,
            cartao_nome=cnome,
            categoria_nome=catn,
        )
