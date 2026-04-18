CREATE TABLE IF NOT EXISTS accounts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    observacao  TEXT
);

CREATE TABLE IF NOT EXISTS cards (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                  TEXT    NOT NULL,
    account_id            INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    observacao            TEXT,
    dia_pagamento_fatura  INTEGER NOT NULL DEFAULT 10,
    UNIQUE (nome COLLATE NOCASE),
    CHECK (dia_pagamento_fatura BETWEEN 1 AND 31)
);

CREATE INDEX IF NOT EXISTS idx_cards_account ON cards(account_id);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    valor           REAL    NOT NULL,
    descricao       TEXT    NOT NULL,
    data            TEXT    NOT NULL,
    conta           TEXT,
    conta_id        INTEGER REFERENCES accounts(id),
    forma_pagamento TEXT    NOT NULL,
    observacao      TEXT
);

CREATE INDEX IF NOT EXISTS idx_payments_data ON payments(data);
-- idx_payments_conta_id criado em migrations.py após existir a coluna conta_id

CREATE TABLE IF NOT EXISTS installments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_fatura     TEXT    NOT NULL,
    cartao          TEXT,
    cartao_id       INTEGER REFERENCES cards(id),
    mes_referencia  TEXT    NOT NULL,
    valor_parcela   REAL    NOT NULL,
    total_parcelas  INTEGER NOT NULL,
    parcelas_pagas  INTEGER NOT NULL DEFAULT 0,
    status          TEXT    NOT NULL DEFAULT 'ativo',
    observacao      TEXT,
    CHECK (total_parcelas > 0),
    CHECK (parcelas_pagas >= 0),
    CHECK (parcelas_pagas <= total_parcelas),
    CHECK (status IN ('ativo', 'quitado'))
);

CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status);
-- idx_installments_cartao_id criado em migrations.py após existir cartao_id
CREATE INDEX IF NOT EXISTS idx_installments_mes ON installments(mes_referencia);

CREATE TABLE IF NOT EXISTS subscriptions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    categoria       TEXT,
    valor_mensal    REAL    NOT NULL,
    dia_cobranca    INTEGER NOT NULL,
    forma_pagamento TEXT    NOT NULL,
    conta_cartao    TEXT,
    account_id      INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    card_id         INTEGER REFERENCES cards(id) ON DELETE SET NULL,
    status          TEXT    NOT NULL DEFAULT 'ativa',
    observacao      TEXT,
    CHECK (dia_cobranca BETWEEN 1 AND 31),
    CHECK (status IN ('ativa', 'pausada', 'cancelada')),
    CHECK (NOT (account_id IS NOT NULL AND card_id IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
-- índices em account_id/card_id criados em migrations.py após as colunas existirem

CREATE TABLE IF NOT EXISTS fixed_expenses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    valor_mensal    REAL    NOT NULL,
    dia_referencia  INTEGER NOT NULL,
    forma_pagamento TEXT    NOT NULL,
    conta_id        INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    observacao      TEXT,
    ativo           INTEGER NOT NULL DEFAULT 1,
    CHECK (dia_referencia BETWEEN 1 AND 31),
    CHECK (valor_mensal >= 0)
);

CREATE TABLE IF NOT EXISTS fixed_expense_months (
    fixed_expense_id INTEGER NOT NULL REFERENCES fixed_expenses(id) ON DELETE CASCADE,
    ano_mes          TEXT    NOT NULL,
    status           TEXT    NOT NULL DEFAULT 'pendente',
    PRIMARY KEY (fixed_expense_id, ano_mes),
    CHECK (status IN ('pendente', 'pago'))
);

CREATE INDEX IF NOT EXISTS idx_fixed_expense_months_mes ON fixed_expense_months(ano_mes);

CREATE TABLE IF NOT EXISTS income_sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    valor_mensal    REAL    NOT NULL,
    ativo           INTEGER NOT NULL DEFAULT 1,
    dia_recebimento INTEGER NOT NULL DEFAULT 5,
    observacao      TEXT,
    CHECK (valor_mensal >= 0),
    CHECK (dia_recebimento BETWEEN 1 AND 31)
);

CREATE INDEX IF NOT EXISTS idx_income_sources_ativo ON income_sources(ativo);
