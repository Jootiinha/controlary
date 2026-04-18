from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class IncomeSource:
    id: Optional[int]
    nome: str
    valor_mensal: float
    ativo: bool = True
    dia_recebimento: int = 5
    observacao: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "IncomeSource":
        keys = list(row.keys())
        ativo = bool(row["ativo"]) if "ativo" in keys else True
        dia = int(row["dia_recebimento"]) if "dia_recebimento" in keys else 5
        return cls(
            id=row["id"],
            nome=row["nome"],
            valor_mensal=float(row["valor_mensal"]),
            ativo=ativo,
            dia_recebimento=dia,
            observacao=row["observacao"] if "observacao" in keys else None,
        )
