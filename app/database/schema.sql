CREATE TABLE IF NOT EXISTS accounts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    observacao     TEXT,
    saldo_inicial  REAL    NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS account_transactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id       INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    data             TEXT    NOT NULL,
    valor            REAL    NOT NULL,
    origem           TEXT    NOT NULL,
    transaction_key  TEXT    NOT NULL UNIQUE,
    descricao        TEXT
);

CREATE INDEX IF NOT EXISTS idx_account_transactions_account_data
    ON account_transactions(account_id, data);

CREATE TABLE IF NOT EXISTS categories (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    tipo_sugerido  TEXT,
    cor            TEXT,
    ativo          INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_categories_ativo ON categories(ativo);

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
    cartao_id       INTEGER REFERENCES cards(id),
    forma_pagamento TEXT    NOT NULL,
    observacao      TEXT,
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    CHECK (NOT (conta_id IS NOT NULL AND cartao_id IS NOT NULL)),
    CHECK (valor > 0)
);

CREATE INDEX IF NOT EXISTS idx_payments_data ON payments(data);

CREATE TABLE IF NOT EXISTS installments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_fatura     TEXT    NOT NULL,
    cartao          TEXT,
    cartao_id       INTEGER REFERENCES cards(id),
    account_id      INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    mes_referencia  TEXT    NOT NULL,
    valor_parcela   REAL    NOT NULL,
    total_parcelas  INTEGER NOT NULL,
    parcelas_pagas  INTEGER NOT NULL DEFAULT 0,
    status          TEXT    NOT NULL DEFAULT 'ativo',
    observacao      TEXT,
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    CHECK (valor_parcela > 0),
    CHECK (total_parcelas > 0),
    CHECK (parcelas_pagas >= 0),
    CHECK (parcelas_pagas <= total_parcelas),
    CHECK (status IN ('ativo', 'quitado')),
    CHECK (NOT (cartao_id IS NOT NULL AND account_id IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status);
CREATE INDEX IF NOT EXISTS idx_installments_mes ON installments(mes_referencia);

CREATE TABLE IF NOT EXISTS installment_months (
    installment_id INTEGER NOT NULL REFERENCES installments(id) ON DELETE CASCADE,
    ano_mes        TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'pendente',
    paid_at        TEXT,
    PRIMARY KEY (installment_id, ano_mes),
    CHECK (status IN ('pendente', 'pago'))
);

CREATE INDEX IF NOT EXISTS idx_installment_months_mes ON installment_months(ano_mes);

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
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    CHECK (valor_mensal > 0),
    CHECK (dia_cobranca BETWEEN 1 AND 31),
    CHECK (status IN ('ativa', 'pausada', 'cancelada')),
    CHECK (NOT (account_id IS NOT NULL AND card_id IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

CREATE TABLE IF NOT EXISTS subscription_months (
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    ano_mes         TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'pendente',
    paid_at         TEXT,
    PRIMARY KEY (subscription_id, ano_mes),
    CHECK (status IN ('pendente', 'pago'))
);

CREATE INDEX IF NOT EXISTS idx_subscription_months_mes ON subscription_months(ano_mes);

CREATE TABLE IF NOT EXISTS fixed_expenses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    valor_mensal    REAL    NOT NULL,
    dia_referencia  INTEGER NOT NULL,
    forma_pagamento TEXT    NOT NULL,
    conta_id        INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    observacao      TEXT,
    ativo           INTEGER NOT NULL DEFAULT 1,
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    CHECK (dia_referencia BETWEEN 1 AND 31),
    CHECK (valor_mensal > 0)
);

CREATE TABLE IF NOT EXISTS fixed_expense_months (
    fixed_expense_id INTEGER NOT NULL REFERENCES fixed_expenses(id) ON DELETE CASCADE,
    ano_mes          TEXT    NOT NULL,
    status           TEXT    NOT NULL DEFAULT 'pendente',
    valor_efetivo    REAL,
    PRIMARY KEY (fixed_expense_id, ano_mes),
    CHECK (status IN ('pendente', 'pago'))
);

CREATE INDEX IF NOT EXISTS idx_fixed_expense_months_mes ON fixed_expense_months(ano_mes);

CREATE TABLE IF NOT EXISTS income_sources (
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
    CHECK (valor_mensal > 0),
    CHECK (dia_recebimento BETWEEN 1 AND 31),
    CHECK (tipo = 'recorrente' OR mes_referencia IS NOT NULL),
    CHECK (tipo <> 'parcelada' OR (
        total_parcelas IS NOT NULL AND total_parcelas >= 1
        AND parcelas_recebidas >= 0 AND parcelas_recebidas <= total_parcelas
    ))
);

CREATE INDEX IF NOT EXISTS idx_income_sources_ativo ON income_sources(ativo);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_income_sources_nome_non_avulsa
    ON income_sources(nome COLLATE NOCASE) WHERE tipo <> 'avulsa';

CREATE TABLE IF NOT EXISTS income_months (
    income_source_id INTEGER NOT NULL REFERENCES income_sources(id) ON DELETE CASCADE,
    ano_mes          TEXT    NOT NULL,
    status           TEXT    NOT NULL DEFAULT 'pendente',
    recebido_em      TEXT,
    valor_efetivo    REAL,
    conta_recebimento_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    PRIMARY KEY (income_source_id, ano_mes),
    CHECK (status IN ('pendente', 'recebido'))
);

CREATE INDEX IF NOT EXISTS idx_income_months_mes ON income_months(ano_mes);

CREATE TABLE IF NOT EXISTS card_invoices (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cartao_id           INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    ano_mes             TEXT    NOT NULL,
    valor_total         REAL    NOT NULL DEFAULT 0,
    status              TEXT    NOT NULL DEFAULT 'aberta',
    pago_em             TEXT,
    conta_pagamento_id  INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    observacao          TEXT,
    historico             INTEGER NOT NULL DEFAULT 0,
    UNIQUE (cartao_id, ano_mes),
    CHECK (status IN ('aberta', 'fechada', 'paga'))
);

CREATE INDEX IF NOT EXISTS idx_card_invoices_mes ON card_invoices(ano_mes);

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
);

CREATE INDEX IF NOT EXISTS idx_investments_banco ON investments(banco_id);
CREATE INDEX IF NOT EXISTS idx_investments_ativo ON investments(ativo);

CREATE TABLE IF NOT EXISTS investment_snapshots (
    investment_id INTEGER NOT NULL REFERENCES investments(id) ON DELETE CASCADE,
    data          TEXT    NOT NULL,
    valor_atual   REAL    NOT NULL,
    PRIMARY KEY (investment_id, data)
);

CREATE INDEX IF NOT EXISTS idx_investment_snapshots_data ON investment_snapshots(data);
