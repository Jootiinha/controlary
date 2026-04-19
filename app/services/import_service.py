"""Importação de extratos e faturas (OFX/CSV) com revisão e idempotência."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from app.database.connection import transaction
from app.importers.base import ImportPreview, ParsedTransaction
from app.importers.registry import detect_and_parse
from app.models.payment import Payment
from app.services import (
    accounts_service,
    card_invoices_service,
    categories_service,
    import_rules_service,
    payments_service,
)


@dataclass
class EnrichedRow:
    transaction: ParsedTransaction
    already_imported: bool
    suggested_category_id: int | None


def preview_file(
    path: Path | str,
    kind: Literal["fatura", "extrato"] | None,
) -> tuple[ImportPreview, list[EnrichedRow]]:
    p = Path(path)
    prev = detect_and_parse(p, kind)
    existing = payments_service.existing_external_ids()
    rows: list[EnrichedRow] = []
    for tx in prev.transactions:
        aid = import_rules_service.match_category(tx.descricao)
        rows.append(
            EnrichedRow(
                transaction=tx,
                already_imported=tx.external_id in existing,
                suggested_category_id=aid,
            )
        )
    return prev, rows


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def commit_extrato(
    account_id: int,
    file_name: str,
    banco: str | None,
    lines: list[tuple[ParsedTransaction, int | None, str]],
) -> int:
    """Uma entrada por linha a importar: (tx, category_id, descricao editada)."""
    if not lines:
        raise ValueError("Nenhuma linha para importar")
    default_cat = categories_service.default_category_id()
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO import_batches (
                kind, source_label, banco, target_id, ano_mes, file_name,
                imported_at, total, n_items
            ) VALUES ('extrato', ?, ?, ?, NULL, ?, ?, 0, 0)
            """,
            (
                file_name,
                banco,
                account_id,
                file_name,
                _now_iso(),
            ),
        )
        batch_id = int(cur.lastrowid)

        total = 0.0
        n_pay = 0
        n_cred = 0

        for tx, cat_id, descricao in lines:
            cat = cat_id if cat_id is not None else default_cat
            dtxt = descricao.strip() or tx.descricao
            if tx.valor < 0:
                amt = abs(float(tx.valor))
                pay = Payment(
                    id=None,
                    valor=amt,
                    descricao=dtxt,
                    data=tx.data.isoformat(),
                    conta_id=account_id,
                    cartao_id=None,
                    forma_pagamento="Importação",
                    observacao=None,
                    category_id=cat,
                    external_id=tx.external_id,
                    import_batch_id=batch_id,
                )
                payments_service.insert_payment(pay, conn, record_ledger=True)
                total += amt
                n_pay += 1
            elif tx.valor > 0:
                cred = float(tx.valor)
                accounts_service.upsert_transaction(
                    account_id,
                    cred,
                    tx.data.isoformat(),
                    "import_extrato",
                    accounts_service.transaction_key_import_credit(
                        batch_id, tx.external_id
                    ),
                    dtxt,
                    conn=conn,
                )
                total += cred
                n_cred += 1

        n_items = n_pay + n_cred
        conn.execute(
            """
            UPDATE import_batches SET total = ?, n_items = ? WHERE id = ?
            """,
            (round(total, 2), n_items, batch_id),
        )
        return batch_id


def commit_fatura(
    cartao_id: int,
    ano_mes: str,
    file_name: str,
    banco: str | None,
    lines: list[tuple[ParsedTransaction, int | None, str]],
) -> int:
    if not lines:
        raise ValueError("Nenhuma linha para importar")
    default_cat = categories_service.default_category_id()
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO import_batches (
                kind, source_label, banco, target_id, ano_mes, file_name,
                imported_at, total, n_items
            ) VALUES ('fatura', ?, ?, ?, ?, ?, ?, 0, 0)
            """,
            (
                file_name,
                banco,
                cartao_id,
                ano_mes,
                file_name,
                _now_iso(),
            ),
        )
        batch_id = int(cur.lastrowid)

        total_imp = 0.0
        n_items = 0

        for tx, cat_id, descricao in lines:
            amt = abs(float(tx.valor))
            if amt < 0.005:
                continue
            cat = cat_id if cat_id is not None else default_cat
            dtxt = descricao.strip() or tx.descricao
            pay = Payment(
                id=None,
                valor=amt,
                descricao=dtxt,
                data=tx.data.isoformat(),
                conta_id=None,
                cartao_id=cartao_id,
                forma_pagamento="Importação",
                observacao=None,
                category_id=cat,
                external_id=tx.external_id,
                import_batch_id=batch_id,
            )
            payments_service.insert_payment(pay, conn, record_ledger=False)
            total_imp += amt
            n_items += 1

        sug = card_invoices_service.suggested_total_conn(conn, cartao_id, ano_mes)
        card_invoices_service.upsert_invoice_conn(
            conn,
            cartao_id,
            ano_mes,
            sug,
            "aberta",
            None,
        )

        conn.execute(
            """
            UPDATE import_batches SET total = ?, n_items = ? WHERE id = ?
            """,
            (round(total_imp, 2), n_items, batch_id),
        )
        return batch_id


def learn_rule(padrao: str, padrao_tipo: str, category_id: int, prioridade: int = 10) -> int:
    return import_rules_service.insert_rule(padrao, padrao_tipo, category_id, prioridade)


def list_batches(limit: int = 50) -> list[dict]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT id, kind, source_label, banco, target_id, ano_mes, file_name,
                   imported_at, total, n_items
              FROM import_batches
             ORDER BY imported_at DESC, id DESC
             LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def undo_batch(batch_id: int) -> None:
    kind: str | None = None
    target_id: int | None = None
    ano_mes: str | None = None
    with transaction() as conn:
        row = conn.execute(
            "SELECT kind, target_id, ano_mes FROM import_batches WHERE id = ?",
            (batch_id,),
        ).fetchone()
        if not row:
            raise ValueError("Lote não encontrado")
        kind = str(row["kind"])
        target_id = int(row["target_id"])
        ano_mes = row["ano_mes"]

        pids = conn.execute(
            "SELECT id FROM payments WHERE import_batch_id = ?",
            (batch_id,),
        ).fetchall()
        for r in pids:
            pid = int(r["id"])
            accounts_service.remove_transaction_key(
                accounts_service.transaction_key_payment(pid), conn=conn
            )
            conn.execute("DELETE FROM payments WHERE id = ?", (pid,))

        conn.execute(
            """
            DELETE FROM account_transactions
             WHERE transaction_key LIKE ?
            """,
            (f"import_credit:{batch_id}:%",),
        )

        conn.execute("DELETE FROM import_batches WHERE id = ?", (batch_id,))

    if kind == "fatura" and ano_mes and target_id is not None:
        card_invoices_service.upsert(
            target_id,
            ano_mes,
            card_invoices_service.suggested_total(target_id, ano_mes),
            "aberta",
            None,
        )
