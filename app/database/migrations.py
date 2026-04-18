"""Aplica o schema e migrações incrementais (contas/cartões)."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.utils.paths import resource_path


def _table_columns(conn, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows}


def _ensure_accounts_cards_tables(conn) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT    NOT NULL COLLATE NOCASE UNIQUE,
            observacao  TEXT
        );
        CREATE TABLE IF NOT EXISTS cards (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT    NOT NULL,
            account_id  INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
            observacao  TEXT,
            UNIQUE (nome COLLATE NOCASE)
        );
        CREATE INDEX IF NOT EXISTS idx_cards_account ON cards(account_id);
        """
    )


def _migrate_payments_conta_id(conn) -> None:
    cols = _table_columns(conn, "payments")
    if "conta_id" in cols:
        return
    conn.execute("ALTER TABLE payments ADD COLUMN conta_id INTEGER REFERENCES accounts(id)")
    rows = conn.execute(
        "SELECT DISTINCT conta FROM payments WHERE conta IS NOT NULL AND TRIM(conta) != ''"
    ).fetchall()
    for (nome,) in rows:
        if not nome:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO accounts (nome) VALUES (?)",
            (nome.strip(),),
        )
        row = conn.execute(
            "SELECT id FROM accounts WHERE nome = ? COLLATE NOCASE LIMIT 1",
            (nome.strip(),),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE payments SET conta_id = ? WHERE conta = ? AND conta_id IS NULL",
                (row["id"], nome),
            )


def _migrate_installments_cartao_id(conn) -> None:
    cols = _table_columns(conn, "installments")
    if "cartao_id" in cols:
        return
    conn.execute("ALTER TABLE installments ADD COLUMN cartao_id INTEGER REFERENCES cards(id)")
    rows = conn.execute(
        "SELECT DISTINCT cartao FROM installments WHERE cartao IS NOT NULL AND TRIM(cartao) != ''"
    ).fetchall()
    for (nome,) in rows:
        if not nome:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO cards (nome) VALUES (?)",
            (nome.strip(),),
        )
        row = conn.execute(
            "SELECT id FROM cards WHERE nome = ? COLLATE NOCASE LIMIT 1",
            (nome.strip(),),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE installments SET cartao_id = ? WHERE cartao = ? AND cartao_id IS NULL",
                (row["id"], nome),
            )


def _migrate_subscriptions_meio(conn) -> None:
    cols = _table_columns(conn, "subscriptions")
    if "account_id" in cols and "card_id" in cols:
        return
    if "account_id" not in cols:
        conn.execute(
            "ALTER TABLE subscriptions ADD COLUMN account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL"
        )
    if "card_id" not in cols:
        conn.execute(
            "ALTER TABLE subscriptions ADD COLUMN card_id INTEGER REFERENCES cards(id) ON DELETE SET NULL"
        )
    rows = conn.execute(
        """
        SELECT id, conta_cartao FROM subscriptions
         WHERE (account_id IS NULL AND card_id IS NULL)
           AND conta_cartao IS NOT NULL AND TRIM(conta_cartao) != ''
        """
    ).fetchall()
    for r in rows:
        sid = r["id"]
        txt = (r["conta_cartao"] or "").strip()
        if not txt:
            continue
        acc = conn.execute(
            "SELECT id FROM accounts WHERE nome = ? COLLATE NOCASE LIMIT 1",
            (txt,),
        ).fetchone()
        if acc:
            conn.execute(
                "UPDATE subscriptions SET account_id = ?, conta_cartao = NULL WHERE id = ?",
                (acc["id"], sid),
            )
            continue
        crd = conn.execute(
            "SELECT id FROM cards WHERE nome = ? COLLATE NOCASE LIMIT 1",
            (txt,),
        ).fetchone()
        if crd:
            conn.execute(
                "UPDATE subscriptions SET card_id = ?, conta_cartao = NULL WHERE id = ?",
                (crd["id"], sid),
            )


def _ensure_indexes_on_fk_columns(conn) -> None:
    """Cria índices em colunas adicionadas por migração (não podem ir no schema.sql inicial)."""
    cols = _table_columns(conn, "payments")
    if "conta_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_payments_conta_id ON payments(conta_id)"
        )
    cols = _table_columns(conn, "installments")
    if "cartao_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_installments_cartao_id ON installments(cartao_id)"
        )
    cols = _table_columns(conn, "subscriptions")
    if "account_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_account ON subscriptions(account_id)"
        )
    if "card_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_card ON subscriptions(card_id)"
        )


def run_migrations() -> None:
    schema_file = Path(resource_path("app/database/schema.sql"))
    sql = schema_file.read_text(encoding="utf-8")
    with transaction() as conn:
        conn.executescript(sql)
        _ensure_accounts_cards_tables(conn)
        _migrate_payments_conta_id(conn)
        _migrate_installments_cartao_id(conn)
        _migrate_subscriptions_meio(conn)
        _ensure_indexes_on_fk_columns(conn)
