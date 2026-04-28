"""CRUD de contas bancárias e livro-caixa (account_transactions)."""
from __future__ import annotations

import sqlite3
import uuid
from typing import List, Optional

from app.database.connection import transaction, use
from app.events import app_events
from app.models.account import Account
from app.repositories import account_transactions_repo, accounts_repo
from app.services.ledger import LedgerKey

_TRANSFER_ORIGEM = "transferencia"


def upsert_transaction(
    account_id: int,
    valor: float,
    data: str,
    origem: str,
    transaction_key: str,
    descricao: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Insere ou substitui movimentação com a mesma transaction_key (idempotente)."""

    def _run(c: sqlite3.Connection) -> int:
        if not account_transactions_repo.account_exists(c, account_id):
            raise ValueError("Conta inválida")
        account_transactions_repo.delete_by_key(c, transaction_key)
        return account_transactions_repo.insert_transaction(
            c,
            account_id=account_id,
            data=data,
            valor=valor,
            origem=origem,
            transaction_key=transaction_key,
            descricao=descricao,
        )

    with use(conn) as c:
        return _run(c)


def remove_transaction_key(
    transaction_key: str, conn: Optional[sqlite3.Connection] = None
) -> None:
    def _run(c: sqlite3.Connection) -> None:
        account_transactions_repo.delete_by_key(c, transaction_key)

    with use(conn) as c:
        _run(c)


def remove_transaction_keys_like_prefix(
    prefix: str, conn: Optional[sqlite3.Connection] = None
) -> None:
    """Remove movimentações cujo transaction_key começa com prefix (ex.: 'fixed:3:')."""

    def _run(c: sqlite3.Connection) -> None:
        account_transactions_repo.delete_keys_like_prefix(c, prefix)

    with use(conn) as c:
        _run(c)


def transaction_key_payment(payment_id: int) -> str:
    return LedgerKey.payment(payment_id)


def transaction_key_invoice(invoice_id: int) -> str:
    return LedgerKey.invoice(invoice_id)


def transaction_key_fixed(fe_id: int, ano_mes: str) -> str:
    return LedgerKey.fixed(fe_id, ano_mes)


def transaction_key_subscription(sub_id: int, ano_mes: str) -> str:
    return LedgerKey.subscription(sub_id, ano_mes)


def transaction_key_installment(inst_id: int, ano_mes: str) -> str:
    return LedgerKey.installment(inst_id, ano_mes)


def transaction_key_income(src_id: int, ano_mes: str) -> str:
    return LedgerKey.income(src_id, ano_mes)


def current_balance(account_id: int, conn: Optional[sqlite3.Connection] = None) -> float:
    """Saldo até hoje: saldo_inicial + soma das movimentações com data <= hoje."""

    def _run(c: sqlite3.Connection) -> float:
        base = account_transactions_repo.fetch_saldo_inicial(c, account_id)
        if base is None:
            return 0.0
        t = account_transactions_repo.sum_for_account_until_today(c, account_id)
        return round(base + t, 2)

    with use(conn) as c:
        return _run(c)


def sum_balances(conn: Optional[sqlite3.Connection] = None) -> float:
    """Soma dos saldos atuais de todas as contas."""

    def _run(c: sqlite3.Connection) -> float:
        total = 0.0
        for aid in account_transactions_repo.list_account_ids(c):
            total += current_balance(aid, c)
        return round(total, 2)

    with use(conn) as c:
        return _run(c)


def post_adjustment(
    account_id: int,
    valor_delta: float,
    data: str,
    descricao: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Ajuste manual (+ ou -)."""
    key = f"adjustment:{uuid.uuid4().hex}"
    return upsert_transaction(
        account_id,
        valor_delta,
        data,
        "ajuste",
        key,
        descricao,
        conn=conn,
    )


def post_transfer(
    from_account_id: int,
    to_account_id: int,
    valor: float,
    data_iso: str,
    descricao: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    if from_account_id == to_account_id:
        raise ValueError("Origem e destino devem ser contas diferentes")
    v = float(valor)
    if v <= 0:
        raise ValueError("Valor deve ser maior que zero")

    def _run(c: sqlite3.Connection) -> None:
        uid = uuid.uuid4().hex
        row_from = accounts_repo.get(c, from_account_id)
        row_to = accounts_repo.get(c, to_account_id)
        if row_from is None or row_to is None:
            raise ValueError("Conta inválida")
        if descricao and descricao.strip():
            desc = descricao.strip()
        else:
            fn = str(row_from["nome"])
            tn = str(row_to["nome"])
            desc = f"Transferência: {fn} → {tn}"
        va = abs(v)
        upsert_transaction(
            from_account_id,
            -va,
            data_iso,
            _TRANSFER_ORIGEM,
            LedgerKey.transfer_debit(uid),
            desc,
            conn=c,
        )
        upsert_transaction(
            to_account_id,
            va,
            data_iso,
            _TRANSFER_ORIGEM,
            LedgerKey.transfer_credit(uid),
            desc,
            conn=c,
        )

    if conn is not None:
        _run(conn)
    else:
        with transaction() as c:
            _run(c)
    app_events().accounts_changed.emit()


def list_all(conn: Optional[sqlite3.Connection] = None) -> List[Account]:
    with use(conn) as c:
        rows = accounts_repo.list_all(c)
    return [Account.from_row(r) for r in rows]


def get(account_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Account]:
    with use(conn) as c:
        row = accounts_repo.get(c, account_id)
    return Account.from_row(row) if row else None


def get_or_unknown(
    account_id: Optional[int], label: str = "—", conn: Optional[sqlite3.Connection] = None
) -> Account:
    if account_id is None:
        return Account.unknown(label)
    acc = get(account_id, conn=conn)
    return acc if acc is not None else Account.unknown(label)


def create(acc: Account, conn: Optional[sqlite3.Connection] = None) -> int:
    with use(conn) as c:
        pid = accounts_repo.insert(
            c,
            nome=acc.nome.strip(),
            observacao=acc.observacao,
            saldo_inicial=float(acc.saldo_inicial),
        )
    app_events().accounts_changed.emit()
    return pid


def update(acc: Account, conn: Optional[sqlite3.Connection] = None) -> None:
    if acc.id is None:
        raise ValueError("Conta sem id")
    with use(conn) as c:
        accounts_repo.update(
            c,
            account_id=int(acc.id),
            nome=acc.nome.strip(),
            observacao=acc.observacao,
            saldo_inicial=float(acc.saldo_inicial),
        )
    app_events().accounts_changed.emit()


def delete(account_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    if count_references(account_id, conn=conn) > 0:
        raise ValueError(
            "Esta conta está em uso (pagamentos, assinaturas, cartões, livro-caixa ou outros "
            "vínculos). Altere ou mova os registros antes de excluir."
        )
    with use(conn) as c:
        accounts_repo.delete(c, account_id)
    app_events().accounts_changed.emit()


def count_references(account_id: int, conn: Optional[sqlite3.Connection] = None) -> int:
    with use(conn) as c:
        return accounts_repo.count_references(c, account_id)


def sum_debits_in_month(ano_mes: str, conn: Optional[sqlite3.Connection] = None) -> float:
    """Soma valores negativos (saídas) no mês YYYY-MM em todas as contas."""

    def _run(c: sqlite3.Connection) -> float:
        return round(account_transactions_repo.sum_debits_in_month(c, ano_mes), 2)

    with use(conn) as c:
        return _run(c)


def list_ledger_rows(
    limit: int = 500, conn: Optional[sqlite3.Connection] = None
) -> list[dict[str, object]]:
    """Linhas recentes do livro-caixa para exibição na UI."""

    def _run(c: sqlite3.Connection) -> list[dict[str, object]]:
        rows = account_transactions_repo.list_recent_with_account(c, limit=limit)
        out: list[dict[str, object]] = []
        for r in rows:
            out.append({
                "id": int(r["id"]),
                "account_id": int(r["account_id"]),
                "conta_nome": str(r["conta_nome"] or ""),
                "data": str(r["data"] or ""),
                "valor": float(r["valor"] or 0),
                "origem": str(r["origem"] or ""),
                "descricao": r["descricao"],
                "transaction_key": str(r["transaction_key"] or ""),
            })
        return out

    with use(conn) as c:
        return _run(c)
