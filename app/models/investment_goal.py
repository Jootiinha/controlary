from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class InvestmentGoal:
    id: Optional[int]
    nome: str
    valor_alvo: float
    category_id: Optional[int] = None
    data_alvo: Optional[str] = None
    observacao: Optional[str] = None
    ativo: bool = True
    categoria_nome: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "InvestmentGoal":
        keys = list(row.keys())
        ativo = bool(row["ativo"]) if "ativo" in keys else True
        catn = (
            row["categoria_nome"]
            if "categoria_nome" in keys and row["categoria_nome"]
            else None
        )
        da = row["data_alvo"] if "data_alvo" in keys and row["data_alvo"] else None
        obs = row["observacao"] if "observacao" in keys and row["observacao"] else None
        cid = row["category_id"] if "category_id" in keys else None
        return cls(
            id=row["id"],
            nome=row["nome"],
            valor_alvo=float(row["valor_alvo"] or 0),
            category_id=int(cid) if cid is not None else None,
            data_alvo=da,
            observacao=obs,
            ativo=ativo,
            categoria_nome=catn,
        )
