from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


def schedule_parcel_amounts(valor_total_contrato: float, n_parcels: int) -> list[float]:
    """Distribui o total em n parcelas com soma exata em centavos (resto nas primeiras)."""
    n = max(int(n_parcels), 0)
    if n <= 0:
        return []
    cents_total = int(round(float(valor_total_contrato) * 100))
    base = cents_total // n
    rem = cents_total % n
    out: list[float] = []
    for i in range(n):
        c = base + (1 if i < rem else 0)
        out.append(round(c / 100.0, 2))
    return out


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
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    cartao_nome: Optional[str] = None
    account_nome: Optional[str] = None
    categoria_nome: Optional[str] = None

    def _amounts_por_competencia(self) -> list[float]:
        n = int(self.total_parcelas)
        if n <= 0:
            return []
        total_contrato = round(float(self.valor_parcela) * n, 2)
        return schedule_parcel_amounts(total_contrato, n)

    @property
    def valor_total(self) -> float:
        s = self._amounts_por_competencia()
        return round(sum(s), 2) if s else 0.0

    @property
    def parcelas_restantes(self) -> int:
        return max(self.total_parcelas - self.parcelas_pagas, 0)

    @property
    def saldo_devedor(self) -> float:
        s = self._amounts_por_competencia()
        if not s:
            return 0.0
        pp = min(max(int(self.parcelas_pagas), 0), len(s))
        return round(sum(s[pp:]), 2)

    @property
    def meio_label(self) -> str:
        if self.cartao_nome:
            return self.cartao_nome
        if self.account_nome:
            return f"Conta · {self.account_nome}"
        return "—"

    @classmethod
    def from_row(cls, row) -> "Installment":
        keys = list(row.keys())
        cid = row["cartao_id"] if "cartao_id" in keys else None
        aid = row["account_id"] if "account_id" in keys else None
        cnome = None
        if "cartao_nome" in keys and row["cartao_nome"]:
            cnome = row["cartao_nome"]
        elif "cartao" in keys and row["cartao"]:
            cnome = row["cartao"]
        anome = row["account_nome"] if "account_nome" in keys and row["account_nome"] else None
        cat_id = row["category_id"] if "category_id" in keys else None
        catn = row["categoria_nome"] if "categoria_nome" in keys and row["categoria_nome"] else None
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
            category_id=cat_id,
            account_id=aid,
            cartao_nome=cnome,
            account_nome=anome,
            categoria_nome=catn,
        )
