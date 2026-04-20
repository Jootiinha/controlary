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
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nome           TEXT    NOT NULL COLLATE NOCASE UNIQUE,
            observacao     TEXT,
            saldo_inicial  REAL    NOT NULL DEFAULT 0
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


DEFAULT_DIA_PAGAMENTO_FATURA = 10
DEFAULT_DIA_RECEBIMENTO_RENDA = 5


def _migrate_cards_dia_pagamento_fatura(conn) -> None:
    cols = _table_columns(conn, "cards")
    if "dia_pagamento_fatura" in cols:
        return
    conn.execute(
        f"""
        ALTER TABLE cards ADD COLUMN dia_pagamento_fatura INTEGER NOT NULL
            DEFAULT {DEFAULT_DIA_PAGAMENTO_FATURA}
        """
    )


def _migrate_income_sources_dia_recebimento(conn) -> None:
    cols = _table_columns(conn, "income_sources")
    if "dia_recebimento" in cols:
        return
    conn.execute(
        f"""
        ALTER TABLE income_sources ADD COLUMN dia_recebimento INTEGER NOT NULL
            DEFAULT {DEFAULT_DIA_RECEBIMENTO_RENDA}
        """
    )


def _ensure_indexes_on_fk_columns(conn) -> None:
    """Cria índices em colunas adicionadas por migração (não podem ir no schema.sql inicial)."""
    cols = _table_columns(conn, "payments")
    if "conta_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_payments_conta_id ON payments(conta_id)"
        )
    if "cartao_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_payments_cartao_id ON payments(cartao_id)"
        )
    if "category_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_payments_category ON payments(category_id)"
        )
    cols = _table_columns(conn, "installments")
    if "cartao_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_installments_cartao_id ON installments(cartao_id)"
        )
    if "category_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_installments_category ON installments(category_id)"
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
    if "category_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_category ON subscriptions(category_id)"
        )
    cols = _table_columns(conn, "fixed_expenses")
    if "category_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_fixed_expenses_category ON fixed_expenses(category_id)"
        )
    cols = _table_columns(conn, "installments")
    if "account_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_installments_account ON installments(account_id)"
        )
    cols = _table_columns(conn, "income_sources")
    if "account_id" in cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_income_sources_account ON income_sources(account_id)"
        )


def _migrate_categories_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nome           TEXT    NOT NULL COLLATE NOCASE UNIQUE,
            tipo_sugerido  TEXT,
            cor            TEXT,
            ativo          INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_categories_ativo ON categories(ativo)"
    )


def _seed_default_categories(conn) -> None:
    row = conn.execute("SELECT COUNT(*) AS n FROM categories").fetchone()
    if row and int(row["n"] or 0) > 0:
        return
    defaults = [
        ("Streaming", "assinatura"),
        ("Software", "assinatura"),
        ("Música", "assinatura"),
        ("Academia", "assinatura"),
        ("Jogos", "assinatura"),
        ("Educação", "assinatura"),
        ("Notícias", "assinatura"),
        ("Mercado", "pagamento"),
        ("Transporte", "pagamento"),
        ("Saúde", "pagamento"),
        ("Moradia", "fixo"),
        ("Serviços", "fixo"),
        ("Outros", None),
    ]
    for nome, tipo in defaults:
        conn.execute(
            "INSERT OR IGNORE INTO categories (nome, tipo_sugerido, ativo) VALUES (?, ?, 1)",
            (nome, tipo),
        )


def _migrate_category_id_columns(conn) -> None:
    for table in ("subscriptions", "fixed_expenses", "installments"):
        cols = _table_columns(conn, table)
        if "category_id" in cols:
            continue
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL"
        )


def _migrate_subscriptions_category_legacy(conn) -> None:
    cols = _table_columns(conn, "subscriptions")
    if "category_id" not in cols:
        return
    rows = conn.execute(
        """
        SELECT id, categoria FROM subscriptions
         WHERE categoria IS NOT NULL AND TRIM(categoria) != ''
           AND category_id IS NULL
        """
    ).fetchall()
    for r in rows:
        nome = (r["categoria"] or "").strip()
        if not nome:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO categories (nome, tipo_sugerido, ativo) VALUES (?, 'assinatura', 1)",
            (nome,),
        )
        crow = conn.execute(
            "SELECT id FROM categories WHERE nome = ? COLLATE NOCASE LIMIT 1",
            (nome,),
        ).fetchone()
        if crow:
            conn.execute(
                "UPDATE subscriptions SET category_id = ? WHERE id = ?",
                (crow["id"], r["id"]),
            )


def _migrate_default_category_where_null(conn) -> None:
    row = conn.execute(
        "SELECT id FROM categories WHERE nome = 'Outros' COLLATE NOCASE LIMIT 1"
    ).fetchone()
    if not row:
        return
    oid = int(row["id"])
    for table in ("payments", "subscriptions", "fixed_expenses", "installments"):
        cols = _table_columns(conn, table)
        if "category_id" not in cols:
            continue
        conn.execute(
            f"UPDATE {table} SET category_id = ? WHERE category_id IS NULL",
            (oid,),
        )


def _migrate_payments_cartao_and_category(conn) -> None:
    cols = _table_columns(conn, "payments")
    if "cartao_id" not in cols:
        conn.execute(
            "ALTER TABLE payments ADD COLUMN cartao_id INTEGER REFERENCES cards(id)"
        )
    if "category_id" not in cols:
        conn.execute(
            "ALTER TABLE payments ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL"
        )


def _migrate_card_invoices_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS card_invoices (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            cartao_id           INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
            ano_mes             TEXT    NOT NULL,
            valor_total         REAL    NOT NULL DEFAULT 0,
            status              TEXT    NOT NULL DEFAULT 'aberta',
            pago_em             TEXT,
            conta_pagamento_id  INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
            observacao          TEXT,
            UNIQUE (cartao_id, ano_mes),
            CHECK (status IN ('aberta', 'fechada', 'paga'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_card_invoices_mes ON card_invoices(ano_mes)"
    )


def _migrate_accounts_saldo_e_transacoes(conn) -> None:
    cols = _table_columns(conn, "accounts")
    if "saldo_inicial" not in cols:
        conn.execute(
            "ALTER TABLE accounts ADD COLUMN saldo_inicial REAL NOT NULL DEFAULT 0"
        )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS account_transactions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id       INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            data             TEXT    NOT NULL,
            valor            REAL    NOT NULL,
            origem           TEXT    NOT NULL,
            transaction_key  TEXT    NOT NULL UNIQUE,
            descricao        TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_account_transactions_account_data
            ON account_transactions(account_id, data)
        """
    )


def _migrate_income_sources_account_id(conn) -> None:
    cols = _table_columns(conn, "income_sources")
    if "account_id" not in cols:
        conn.execute(
            "ALTER TABLE income_sources ADD COLUMN account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL"
        )


def _migrate_income_sources_avulsas_parceladas(conn) -> None:
    cols = _table_columns(conn, "income_sources")
    if "tipo" not in cols:
        conn.execute(
            "ALTER TABLE income_sources ADD COLUMN tipo TEXT NOT NULL DEFAULT 'recorrente'"
        )
    if "mes_referencia" not in cols:
        conn.execute("ALTER TABLE income_sources ADD COLUMN mes_referencia TEXT")
    if "total_parcelas" not in cols:
        conn.execute("ALTER TABLE income_sources ADD COLUMN total_parcelas INTEGER")
    if "parcelas_recebidas" not in cols:
        conn.execute(
            "ALTER TABLE income_sources ADD COLUMN parcelas_recebidas INTEGER NOT NULL DEFAULT 0"
        )
    if "forma_recebimento" not in cols:
        conn.execute("ALTER TABLE income_sources ADD COLUMN forma_recebimento TEXT")


def _income_sources_has_global_unique_nome(conn) -> bool:
    indexes = conn.execute("PRAGMA index_list(income_sources)").fetchall()
    for idx in indexes:
        if not int(idx["unique"]):
            continue
        partial = int(idx["partial"]) if "partial" in idx.keys() else 0
        if partial:
            continue
        cols = conn.execute(f"PRAGMA index_info({idx['name']})").fetchall()
        col_names = [c["name"] for c in cols]
        if col_names == ["nome"]:
            return True
    return False


def _migrate_income_sources_relax_nome_unique(conn) -> None:
    """Permite nomes duplicados em rendas avulsas (mantém unicidade para recorrentes/parceladas)."""
    if _income_sources_has_global_unique_nome(conn):
        conn.executescript(
            """
            PRAGMA foreign_keys = OFF;
            CREATE TABLE income_sources_new (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                nome                TEXT    NOT NULL COLLATE NOCASE,
                valor_mensal        REAL    NOT NULL,
                ativo               INTEGER NOT NULL DEFAULT 1,
                dia_recebimento     INTEGER NOT NULL DEFAULT 5,
                account_id          INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                observacao          TEXT,
                tipo                TEXT    NOT NULL DEFAULT 'recorrente'
                                    CHECK (tipo IN ('recorrente', 'avulsa', 'parcelada')),
                mes_referencia      TEXT,
                total_parcelas      INTEGER,
                parcelas_recebidas  INTEGER NOT NULL DEFAULT 0,
                forma_recebimento   TEXT,
                CHECK (valor_mensal >= 0),
                CHECK (dia_recebimento BETWEEN 1 AND 31),
                CHECK (tipo = 'recorrente' OR mes_referencia IS NOT NULL),
                CHECK (tipo <> 'parcelada' OR (
                    total_parcelas IS NOT NULL AND total_parcelas >= 1
                    AND parcelas_recebidas >= 0 AND parcelas_recebidas <= total_parcelas
                ))
            );
            INSERT INTO income_sources_new (
                id, nome, valor_mensal, ativo, dia_recebimento, account_id, observacao,
                tipo, mes_referencia, total_parcelas, parcelas_recebidas, forma_recebimento
            )
            SELECT id, nome, valor_mensal, ativo, dia_recebimento, account_id, observacao,
                   tipo, mes_referencia, total_parcelas, parcelas_recebidas, forma_recebimento
              FROM income_sources;
            DROP TABLE income_sources;
            ALTER TABLE income_sources_new RENAME TO income_sources;
            CREATE INDEX IF NOT EXISTS idx_income_sources_ativo ON income_sources(ativo);
            CREATE INDEX IF NOT EXISTS idx_income_sources_account ON income_sources(account_id);
            PRAGMA foreign_keys = ON;
            """
        )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uniq_income_sources_nome_non_avulsa "
        "ON income_sources(nome COLLATE NOCASE) WHERE tipo <> 'avulsa'"
    )


def _migrate_installments_account_id(conn) -> None:
    cols = _table_columns(conn, "installments")
    if "account_id" not in cols:
        conn.execute(
            "ALTER TABLE installments ADD COLUMN account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL"
        )


def _migrate_month_tracking_tables(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subscription_months (
            subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
            ano_mes         TEXT    NOT NULL,
            status          TEXT    NOT NULL DEFAULT 'pendente',
            paid_at         TEXT,
            PRIMARY KEY (subscription_id, ano_mes),
            CHECK (status IN ('pendente', 'pago'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_subscription_months_mes ON subscription_months(ano_mes)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS installment_months (
            installment_id INTEGER NOT NULL REFERENCES installments(id) ON DELETE CASCADE,
            ano_mes        TEXT    NOT NULL,
            status         TEXT    NOT NULL DEFAULT 'pendente',
            paid_at        TEXT,
            PRIMARY KEY (installment_id, ano_mes),
            CHECK (status IN ('pendente', 'pago'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_installment_months_mes ON installment_months(ano_mes)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS income_months (
            income_source_id INTEGER NOT NULL REFERENCES income_sources(id) ON DELETE CASCADE,
            ano_mes          TEXT    NOT NULL,
            status           TEXT    NOT NULL DEFAULT 'pendente',
            recebido_em      TEXT,
            PRIMARY KEY (income_source_id, ano_mes),
            CHECK (status IN ('pendente', 'recebido'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_income_months_mes ON income_months(ano_mes)"
    )


def _migrate_fixed_expense_months_valor_efetivo(conn) -> None:
    cols = _table_columns(conn, "fixed_expense_months")
    if "valor_efetivo" in cols:
        return
    conn.execute(
        "ALTER TABLE fixed_expense_months ADD COLUMN valor_efetivo REAL"
    )


def _migrate_income_months_valor_efetivo(conn) -> None:
    cols = _table_columns(conn, "income_months")
    if "valor_efetivo" in cols:
        return
    conn.execute("ALTER TABLE income_months ADD COLUMN valor_efetivo REAL")


def _migrate_income_sources_drop_global_unique_nome(conn) -> None:
    """Remove índice UNIQUE global em nome (permite avulsas homônimas); garante índice parcial."""
    rows = conn.execute("PRAGMA index_list(income_sources)").fetchall()
    for r in rows:
        name = r["name"]
        if not int(r["unique"]):
            continue
        partial = int(r["partial"]) if "partial" in r.keys() else 0
        if partial:
            continue
        cols = conn.execute(f"PRAGMA index_info({name})").fetchall()
        if len(cols) == 1 and cols[0]["name"] == "nome":
            conn.execute(f'DROP INDEX IF EXISTS "{name}"')
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uniq_income_sources_nome_non_avulsa "
        "ON income_sources(nome COLLATE NOCASE) WHERE tipo <> 'avulsa'"
    )


def _migrate_investments_tables(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS investments (
            id                       INTEGER PRIMARY KEY AUTOINCREMENT,
            banco_id                 INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            nome                     TEXT    NOT NULL,
            tipo                     TEXT    NOT NULL,
            valor_aplicado           REAL    NOT NULL DEFAULT 0,
            rendimento_percentual_aa REAL,
            data_aplicacao           TEXT    NOT NULL,
            data_vencimento          TEXT,
            category_id              INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            observacao               TEXT,
            ativo                    INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS investment_snapshots (
            investment_id INTEGER NOT NULL REFERENCES investments(id) ON DELETE CASCADE,
            data          TEXT    NOT NULL,
            valor_atual   REAL    NOT NULL,
            PRIMARY KEY (investment_id, data)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_investments_banco ON investments(banco_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_investments_ativo ON investments(ativo)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_investment_snapshots_data ON investment_snapshots(data)"
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
        _migrate_cards_dia_pagamento_fatura(conn)
        _migrate_income_sources_dia_recebimento(conn)
        _migrate_categories_table(conn)
        _seed_default_categories(conn)
        _migrate_category_id_columns(conn)
        _migrate_subscriptions_category_legacy(conn)
        _migrate_payments_cartao_and_category(conn)
        _migrate_default_category_where_null(conn)
        _migrate_card_invoices_table(conn)
        _migrate_investments_tables(conn)
        _migrate_accounts_saldo_e_transacoes(conn)
        _migrate_income_sources_account_id(conn)
        _migrate_income_sources_avulsas_parceladas(conn)
        _migrate_income_sources_relax_nome_unique(conn)
        _migrate_income_sources_drop_global_unique_nome(conn)
        _migrate_installments_account_id(conn)
        _migrate_month_tracking_tables(conn)
        _migrate_fixed_expense_months_valor_efetivo(conn)
        _migrate_income_months_valor_efetivo(conn)
        _ensure_indexes_on_fk_columns(conn)
