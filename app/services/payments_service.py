"""Operações de CRUD para pagamentos."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Protocol, runtime_checkable

from app.database.connection import use
from app.events import app_events
from app.models.payment import Payment
from app.repositories import payments_repo
from app.services import accounts_service


def _validate_origin(payment: Payment) -> None:
    has_acc = payment.conta_id is not None
    has_card = payment.cartao_id is not None
    if has_acc == has_card:
        raise ValueError("Informe conta bancária ou cartão (apenas um)")
    if float(payment.valor) <= 0:
        raise ValueError("Valor do pagamento deve ser maior que zero")


@runtime_checkable
class _PaymentDestination(Protocol):
    def insert(self, conn: sqlite3.Connection, payment: Payment, record_ledger: bool) -> int:
        ...

    def update(
        self,
        conn: sqlite3.Connection,
        payment: Payment,
        prev: Optional[sqlite3.Row],
        *,
        had_ledger: bool,
        had_card: bool,
    ) -> None:
        ...


@dataclass
class _AccountDestination:
    conta_id: int

    def insert(self, conn: sqlite3.Connection, payment: Payment, record_ledger: bool) -> int:
        row = payments_repo.fetch_account_nome(conn, self.conta_id)
        if not row:
            raise ValueError("Conta inválida")
        conta_txt = row["nome"]
        pid = payments_repo.insert_account_payment(
            conn,
            valor=payment.valor,
            descricao=payment.descricao,
            data=payment.data,
            conta_txt=conta_txt,
            conta_id=self.conta_id,
            forma_pagamento=payment.forma_pagamento,
            observacao=payment.observacao,
            category_id=payment.category_id,
        )
        if record_ledger:
            desc = payment.descricao
            if desc and len(desc) > 500:
                desc = desc[:500]
            accounts_service.upsert_transaction(
                self.conta_id,
                -float(payment.valor),
                payment.data,
                "pagamento",
                accounts_service.transaction_key_payment(pid),
                desc,
                conn=conn,
            )
        return pid

    def update(
        self,
        conn: sqlite3.Connection,
        payment: Payment,
        prev: Optional[sqlite3.Row],
        *,
        had_ledger: bool,
        had_card: bool,
    ) -> None:
        if payment.id is None:
            raise ValueError("Pagamento sem id não pode ser atualizado")
        row = payments_repo.fetch_account_nome(conn, self.conta_id)
        if not row:
            raise ValueError("Conta inválida")
        nome_conta = row["nome"]
        payments_repo.update_account_payment(
            conn,
            valor=payment.valor,
            descricao=payment.descricao,
            data=payment.data,
            nome_conta=nome_conta,
            conta_id=self.conta_id,
            forma_pagamento=payment.forma_pagamento,
            observacao=payment.observacao,
            category_id=payment.category_id,
            payment_id=payment.id,
        )
        desc = payment.descricao
        if desc and len(desc) > 500:
            desc = desc[:500]
        if had_ledger or had_card:
            accounts_service.upsert_transaction(
                self.conta_id,
                -float(payment.valor),
                payment.data,
                "pagamento",
                accounts_service.transaction_key_payment(int(payment.id)),
                desc,
                conn=conn,
            )


@dataclass
class _CardDestination:
    cartao_id: int

    def insert(self, conn: sqlite3.Connection, payment: Payment, record_ledger: bool) -> int:
        row = payments_repo.fetch_card_nome(conn, self.cartao_id)
        if not row:
            raise ValueError("Cartão inválido")
        nome_card = row["nome"]
        return payments_repo.insert_card_payment(
            conn,
            valor=payment.valor,
            descricao=payment.descricao,
            data=payment.data,
            nome_card=nome_card,
            cartao_id=self.cartao_id,
            forma_pagamento=payment.forma_pagamento,
            observacao=payment.observacao,
            category_id=payment.category_id,
        )

    def update(
        self,
        conn: sqlite3.Connection,
        payment: Payment,
        prev: Optional[sqlite3.Row],
        *,
        had_ledger: bool,
        had_card: bool,
    ) -> None:
        if payment.id is None:
            raise ValueError("Pagamento sem id não pode ser atualizado")
        row = payments_repo.fetch_card_nome(conn, self.cartao_id)
        if not row:
            raise ValueError("Cartão inválido")
        nome_card = row["nome"]
        payments_repo.update_card_payment(
            conn,
            valor=payment.valor,
            descricao=payment.descricao,
            data=payment.data,
            nome_card=nome_card,
            cartao_id=self.cartao_id,
            forma_pagamento=payment.forma_pagamento,
            observacao=payment.observacao,
            category_id=payment.category_id,
            payment_id=payment.id,
        )


def _destination(payment: Payment) -> _PaymentDestination:
    if payment.conta_id is not None:
        return _AccountDestination(int(payment.conta_id))
    if payment.cartao_id is not None:
        return _CardDestination(int(payment.cartao_id))
    raise ValueError("Informe conta bancária ou cartão (apenas um)")


def list_all(conn: Optional[sqlite3.Connection] = None) -> List[Payment]:
    with use(conn) as c:
        rows = payments_repo.list_all(c)
    return [Payment.from_row(r) for r in rows]


def list_between(
    data_ini: date, data_fim: date, conn: Optional[sqlite3.Connection] = None
) -> List[Payment]:
    with use(conn) as c:
        rows = payments_repo.list_between(c, data_ini, data_fim)
    return [Payment.from_row(r) for r in rows]


def get(payment_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Payment]:
    with use(conn) as c:
        row = payments_repo.get(c, payment_id)
    return Payment.from_row(row) if row else None


def create(
    payment: Payment, record_ledger: bool = True, conn: Optional[sqlite3.Connection] = None
) -> int:
    """record_ledger=False evita movimentação no livro-caixa (ex.: espelho de fixo já debitado em set_month_status)."""
    _validate_origin(payment)
    dest = _destination(payment)
    with use(conn) as c:
        pid = dest.insert(c, payment, record_ledger)
    app_events().payments_changed.emit()
    return pid


def update(payment: Payment, conn: Optional[sqlite3.Connection] = None) -> None:
    if payment.id is None:
        raise ValueError("Pagamento sem id não pode ser atualizado")
    _validate_origin(payment)
    dest = _destination(payment)
    with use(conn) as c:
        prev = payments_repo.fetch_prev_origins(c, payment.id)
        key = accounts_service.transaction_key_payment(payment.id)
        had_card = prev is not None and prev["cartao_id"] is not None
        had_ledger = payments_repo.has_transaction_key(c, key)
        accounts_service.remove_transaction_key(key, conn=c)
        dest.update(c, payment, prev, had_ledger=had_ledger, had_card=had_card)
    app_events().payments_changed.emit()


def delete(payment_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    with use(conn) as c:
        accounts_service.remove_transaction_key(
            accounts_service.transaction_key_payment(payment_id), conn=c
        )
        payments_repo.delete_by_id(c, payment_id)
    app_events().payments_changed.emit()


def delete_mirrors_for_fixed_month(
    nome_fixo: str, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> None:
    """Remove espelhos ``Fixo: … (YYYY-MM)`` criados ao marcar o mês como pago."""
    desc = f"Fixo: {nome_fixo} ({ano_mes})"
    with use(conn) as c:
        ids = payments_repo.select_mirror_payment_ids(c, desc)
    for pid in ids:
        delete(pid)
