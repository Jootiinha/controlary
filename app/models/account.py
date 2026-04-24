from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Account:
    id: Optional[int]
    nome: str
    observacao: Optional[str] = None
    saldo_inicial: float = 0.0
    saldo_atual: Optional[float] = None  # preenchido em listagens quando calculado

    @classmethod
    def unknown(cls, label: str = "—") -> "Account":
        return cls(id=None, nome=label, observacao=None, saldo_inicial=0.0, saldo_atual=None)

    @classmethod
    def from_row(cls, row) -> "Account":
        keys = list(row.keys())
        saldo_ini = float(row["saldo_inicial"]) if "saldo_inicial" in keys else 0.0
        saldo_at = float(row["saldo_atual"]) if "saldo_atual" in keys and row["saldo_atual"] is not None else None
        return cls(
            id=row["id"],
            nome=row["nome"],
            observacao=row["observacao"],
            saldo_inicial=saldo_ini,
            saldo_atual=saldo_at,
        )
