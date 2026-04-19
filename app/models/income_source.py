from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


def _advance_month(ym: str, delta: int = 1) -> str:
    y, m = map(int, ym.split("-"))
    m += delta
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}"


def competencias_parcelada(mes_inicio: str, total: int) -> list[str]:
    out: list[str] = []
    cur = mes_inicio
    for _ in range(total):
        out.append(cur)
        cur = _advance_month(cur, 1)
    return out


@dataclass
class IncomeSource:
    id: Optional[int]
    nome: str
    valor_mensal: float
    ativo: bool = True
    dia_recebimento: int = 5
    account_id: Optional[int] = None
    conta_nome: Optional[str] = None
    observacao: Optional[str] = None
    tipo: str = "recorrente"
    mes_referencia: Optional[str] = None
    total_parcelas: Optional[int] = None
    parcelas_recebidas: int = 0
    forma_recebimento: Optional[str] = None

    @property
    def parcelas_restantes(self) -> int:
        if self.tipo != "parcelada" or self.total_parcelas is None:
            return 0
        return max(self.total_parcelas - self.parcelas_recebidas, 0)

    def competencias(self) -> list[str]:
        if self.tipo == "recorrente":
            return []
        if self.tipo == "avulsa" and self.mes_referencia:
            return [self.mes_referencia]
        if self.tipo == "parcelada" and self.mes_referencia and self.total_parcelas:
            return competencias_parcelada(self.mes_referencia, self.total_parcelas)
        return []

    @classmethod
    def from_row(cls, row) -> "IncomeSource":
        keys = list(row.keys())
        ativo = bool(row["ativo"]) if "ativo" in keys else True
        dia = int(row["dia_recebimento"]) if "dia_recebimento" in keys else 5
        aid = row["account_id"] if "account_id" in keys else None
        cn = row["conta_nome"] if "conta_nome" in keys and row["conta_nome"] else None
        tipo = row["tipo"] if "tipo" in keys else "recorrente"
        mr = row["mes_referencia"] if "mes_referencia" in keys else None
        tp = row["total_parcelas"] if "total_parcelas" in keys else None
        pr = int(row["parcelas_recebidas"]) if "parcelas_recebidas" in keys else 0
        fr = row["forma_recebimento"] if "forma_recebimento" in keys else None
        return cls(
            id=row["id"],
            nome=row["nome"],
            valor_mensal=float(row["valor_mensal"]),
            ativo=ativo,
            dia_recebimento=dia,
            account_id=aid,
            conta_nome=cn,
            observacao=row["observacao"] if "observacao" in keys else None,
            tipo=tipo or "recorrente",
            mes_referencia=mr,
            total_parcelas=int(tp) if tp is not None else None,
            parcelas_recebidas=pr,
            forma_recebimento=fr if fr else None,
        )
