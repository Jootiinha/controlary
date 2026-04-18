from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Investment:
    id: Optional[int]
    banco_id: int
    nome: str
    tipo: str
    valor_aplicado: float
    data_aplicacao: str
    rendimento_percentual_aa: Optional[float] = None
    data_vencimento: Optional[str] = None
    category_id: Optional[int] = None
    observacao: Optional[str] = None
    ativo: bool = True
    banco_nome: Optional[str] = None
    categoria_nome: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Investment":
        keys = list(row.keys())
        ativo = bool(row["ativo"]) if "ativo" in keys else True
        r_aa = row["rendimento_percentual_aa"] if "rendimento_percentual_aa" in keys else None
        bn = row["banco_nome"] if "banco_nome" in keys and row["banco_nome"] else None
        catn = row["categoria_nome"] if "categoria_nome" in keys and row["categoria_nome"] else None
        return cls(
            id=row["id"],
            banco_id=row["banco_id"],
            nome=row["nome"],
            tipo=row["tipo"],
            valor_aplicado=float(row["valor_aplicado"] or 0),
            data_aplicacao=row["data_aplicacao"],
            rendimento_percentual_aa=float(r_aa) if r_aa is not None else None,
            data_vencimento=row["data_vencimento"] if "data_vencimento" in keys else None,
            category_id=row["category_id"] if "category_id" in keys else None,
            observacao=row["observacao"] if "observacao" in keys else None,
            ativo=ativo,
            banco_nome=bn,
            categoria_nome=catn,
        )


@dataclass
class InvestmentSnapshot:
    investment_id: int
    data: str
    valor_atual: float

    @classmethod
    def from_row(cls, row) -> "InvestmentSnapshot":
        return cls(
            investment_id=row["investment_id"],
            data=row["data"],
            valor_atual=float(row["valor_atual"] or 0),
        )
