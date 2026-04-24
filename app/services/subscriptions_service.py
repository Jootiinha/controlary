"""Operações de CRUD para assinaturas recorrentes."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.database.connection import use
from app.events import app_events
from app.models.subscription import Subscription
from app.repositories import subscriptions_repo
from app.services import accounts_service
from app.services.competencia_ledger import data_iso_no_mes


def list_all(conn: Optional[sqlite3.Connection] = None) -> List[Subscription]:
    with use(conn) as c:
        rows = subscriptions_repo.list_all_joined(c)
    return [Subscription.from_row(r) for r in rows]


def get(sub_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Subscription]:
    with use(conn) as c:
        row = subscriptions_repo.get_joined(c, sub_id)
    return Subscription.from_row(row) if row else None


def _legacy_categoria(conn: sqlite3.Connection, sub: Subscription) -> Optional[str]:
    if sub.category_id is None:
        return sub.categoria
    r = subscriptions_repo.fetch_category_nome(conn, int(sub.category_id))
    return str(r["nome"]) if r else sub.categoria


def create(sub: Subscription, conn: Optional[sqlite3.Connection] = None) -> int:
    with use(conn) as c:
        label = _meio_label(c, sub.account_id, sub.card_id)
        cat_txt = _legacy_categoria(c, sub)
        pid = subscriptions_repo.insert_subscription(
            c,
            nome=sub.nome,
            categoria=cat_txt,
            valor_mensal=float(sub.valor_mensal),
            dia_cobranca=int(sub.dia_cobranca),
            forma_pagamento=sub.forma_pagamento,
            conta_cartao=label,
            account_id=sub.account_id,
            card_id=sub.card_id,
            status=sub.status,
            observacao=sub.observacao,
            category_id=sub.category_id,
        )
    app_events().subscriptions_changed.emit()
    return pid


def update(sub: Subscription, conn: Optional[sqlite3.Connection] = None) -> None:
    if sub.id is None:
        raise ValueError("Assinatura sem id não pode ser atualizada")
    before = get(sub.id, conn=conn)
    if before is None:
        raise ValueError("Assinatura não encontrada")
    meio_changed = (before.account_id or 0) != (sub.account_id or 0) or (
        (before.card_id or 0) != (sub.card_id or 0)
    )
    valor_changed = before.valor_mensal != sub.valor_mensal

    with use(conn) as c:
        label = _meio_label(c, sub.account_id, sub.card_id)
        cat_txt = _legacy_categoria(c, sub)
        subscriptions_repo.update_subscription(
            c,
            sub_id=int(sub.id),
            nome=sub.nome,
            categoria=cat_txt,
            valor_mensal=float(sub.valor_mensal),
            dia_cobranca=int(sub.dia_cobranca),
            forma_pagamento=sub.forma_pagamento,
            conta_cartao=label,
            account_id=sub.account_id,
            card_id=sub.card_id,
            status=sub.status,
            observacao=sub.observacao,
            category_id=sub.category_id,
        )

        if meio_changed:
            accounts_service.remove_transaction_keys_like_prefix(
                f"subscription:{sub.id}:", conn=c
            )

        if sub.account_id and sub.status == "ativa":
            resync = (not meio_changed and valor_changed) or (
                meio_changed
                and before.account_id is not None
                and sub.account_id is not None
            )
            if resync:
                sid = int(sub.id)
                aid = int(sub.account_id)
                for r in subscriptions_repo.list_paid_ano_meses(c, sid):
                    ym = str(r["ano_mes"])
                    data = data_iso_no_mes(ym, int(sub.dia_cobranca or 5))
                    accounts_service.upsert_transaction(
                        aid,
                        -float(sub.valor_mensal),
                        data,
                        "assinatura",
                        accounts_service.transaction_key_subscription(sid, ym),
                        None,
                        conn=c,
                    )
    app_events().subscriptions_changed.emit()


def _meio_label(
    conn: sqlite3.Connection,
    account_id: Optional[int],
    card_id: Optional[int],
) -> Optional[str]:
    if account_id:
        r = subscriptions_repo.fetch_account_nome(conn, int(account_id))
        return str(r["nome"]) if r else None
    if card_id:
        r = subscriptions_repo.fetch_card_nome(conn, int(card_id))
        return str(r["nome"]) if r else None
    return None


def delete(sub_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    with use(conn) as c:
        accounts_service.remove_transaction_keys_like_prefix(
            f"subscription:{sub_id}:", conn=c
        )
        subscriptions_repo.delete_by_id(c, sub_id)
    app_events().subscriptions_changed.emit()


def total_active(conn: Optional[sqlite3.Connection] = None) -> tuple[int, float]:
    with use(conn) as c:
        row = subscriptions_repo.row_total_active(c)
    return int(row["qtd"] or 0), float(row["total"] or 0)


def sum_active_not_on_card(conn: Optional[sqlite3.Connection] = None) -> float:
    """Soma assinaturas ativas pagas em conta (sem cartão)."""
    with use(conn) as c:
        return subscriptions_repo.sum_active_not_on_card(c)
