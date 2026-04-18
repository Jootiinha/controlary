from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Installment:
    id: Optional[int]
    nome_fatura: str
    cartao_id: Optional[int]
    mes_referencia: str
    valor_parcela: float
    total_parcelas: int
    parcelas_pagas: int = 0
    status: str = "ativo"
    observacao: Optional[str] = None
    cartao_nome: Optional[str] = None  # JOIN

    @property
    def valor_total(self) -> float:
        return round(self.valor_parcela * self.total_parcelas, 2)

    @property
    def parcelas_restantes(self) -> int:
        return max(self.total_parcelas - self.parcelas_pagas, 0)

    @property
    def saldo_devedor(self) -> float:
        return round(self.valor_parcela * self.parcelas_restantes, 2)

    @classmethod
    def from_row(cls, row) -> "Installment":
        keys = list(row.keys())
        cid = row["cartao_id"] if "cartao_id" in keys else None
        cnome = None
        if "cartao_nome" in keys and row["cartao_nome"]:
            cnome = row["cartao_nome"]
        elif "cartao" in keys and row["cartao"]:
            cnome = row["cartao"]
        return cls(
            id=row["id"],
            nome_fatura=row["nome_fatura"],
            cartao_id=cid,
            mes_referencia=row["mes_referencia"],
            valor_parcela=row["valor_parcela"],
            total_parcelas=row["total_parcelas"],
            parcelas_pagas=row["parcelas_pagas"],
            status=row["status"],
            observacao=row["observacao"],
            cartao_nome=cnome,
        )
