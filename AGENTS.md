# AGENTS.md

Instruções para agentes de IA (Cursor, Codex, Claude Code, etc.) trabalhando neste repositório. Leia antes de abrir PRs ou gerar código.

## Sobre o projeto

App desktop de controle financeiro pessoal em **Python 3.11+ / PySide6 (Qt6) / SQLite**, offline. Entrada em `main.py`; empacotado com PyInstaller para macOS e Windows.

## Comandos essenciais

Use o Makefile sempre que possível:

```bash
make install     # poetry install --no-root
make run         # roda o app (poetry run python main.py)
make check       # valida pyproject e compila todos os .py
make test        # roda pytest (grupo dev: pytest, pytest-qt)
make test-cov    # pytest com cobertura em app/services (requer pytest-cov no grupo dev)
make reset-db    # apaga ~/.controle-financeiro/app.db
make build-mac   # empacota .app
make build-win   # empacota .exe
```

Sem Makefile:

```bash
poetry install && poetry run python main.py
poetry run python -m compileall -q app main.py
poetry install --with dev --no-root && poetry run pytest tests/
```

Testes automatizados: `make test` (BD SQLite temporária via `CONTROLE_FINANCEIRO_DB`). `make check` continua sendo a validação mínima de sintaxe antes de concluir tarefas que toquem em `.py`.

## Arquitetura em camadas

```
main.py
  └─ app/database/migrations.py  (roda sempre no startup)
  └─ app/ui/main_window.py       (QMainWindow + sidebar + QStackedWidget)
       └─ app/ui/*_view.py       (uma view por página)
            └─ app/services/*    (regras de negócio, orquestração, transações)
                 ├─ app/repositories/*  (SQL puro; sem `transaction()` interno)
                 ├─ app/events.py        (AppEvents: sinais por domínio p/ sincronizar UI)
                 ├─ app/utils/mes_ano.py (competência YYYY-MM como value object)
                 └─ app/models/* (dataclasses; sem lógica pesada)
                      └─ app/database/connection.py  (transaction(), use(conn))
```

- **Unit of Work**: funções de service que escrevem no DB aceitam `conn: Optional[sqlite3.Connection] = None` e usam `with use(conn) as c:` (`use` em `connection.py`). Quem abre a transação externa passa a mesma `conn` para evitar transações aninhadas.
- **Chaves do livro-caixa**: `app/services/ledger.py` (`LedgerKey`); `accounts_service.transaction_key_*` delegam para compatibilidade.
- **Competência + dia**: `app/services/competencia_ledger.data_iso_no_mes(ano_mes: str | MesAno, dia)`; `app/services/_monthly_ledger.MonthlyLedgerService` (ABC) com implementações em `*months_service` e `fixed_expenses_service.set_month_status`.

`app/importers/` está reservado para importadores futuros (ex.: OFX/CSV por banco).

Regras:

- **Views (`app/ui/*_view.py`)** chamam apenas `services/`. Nunca importe `sqlite3` nem acesse `connection` em view.
- **Services** recebem/retornam **dataclasses** de `app/models/`; concentram regras, orquestração e transações (`with transaction() as conn:` ou `with use(conn) as c:`). SQL de persistência fica em **`app/repositories/*`**.
- **Repositories** expõem funções com `sqlite3.Connection` já aberta pelo service; sem abrir `transaction()` no repo.
- **Models** são `@dataclass` simples com `from_row` para construir a partir de `sqlite3.Row`.
- **Formatação** (moeda, datas, mês) vive em `app/utils/formatting.py`. Nunca formate `R$` ou datas dentro de view/service — importe utilitários.
- **Gráficos** (matplotlib) vivem em `app/charts/` como funções `plot(ax, ...)` embutidas via `ChartCanvas`.
- **Estilo Qt**: `app/ui/style.qss` (claro) e `app/ui/style_dark.qss` (escuro); troca em `app/ui/theme.py` + menu **Exibir** + `QSettings` (`ui/theme`). Widgets em `app/ui/widgets/` (`KpiCard`, `ChartCanvas`, `CrudPage`, `FormDialog`, `CategoryPicker`, `ReadOnlyTable`, `PaymentConfirmationDialog`, `WrappingHeader`).

## Migrações de schema

1. **Sempre** alterar `app/database/schema.sql` para o estado final desejado (usado em bancos novos).
2. **Sempre** adicionar uma função `_migrate_*` idempotente em `app/database/migrations.py` e chamá-la dentro de `run_migrations()`, para bancos existentes:

```python
def _migrate_cards_dia_pagamento_fatura(conn) -> None:
    cols = _table_columns(conn, "cards")
    if "dia_pagamento_fatura" in cols:
        return
    conn.execute(
        "ALTER TABLE cards ADD COLUMN dia_pagamento_fatura INTEGER NOT NULL DEFAULT 10"
    )
```

3. Atualizar a `@dataclass` do model e os `INSERT/UPDATE` em `repositories/` (e validações em `services/` quando aplicável).
4. Propagar o campo para as views (form dialog + tabela) quando fizer sentido.

## Convenções de código

- **Idioma**: domínio e UI em **português** (labels, colunas de DB como `valor_mensal`, `dia_recebimento`, `ativo`). Tipos/funções em inglês quando for conveniente, mas siga o padrão existente no arquivo.
- `from __future__ import annotations` no topo dos módulos.
- Type hints sempre (`Optional`, `list[...]`, `dict[...]`).
- Imports ordenados: stdlib → `PySide6` → `app.*`.
- **Sem comentários narrativos** ("# Importa X", "# Retorna Y"). Comentário só para **intenção/trade-off** não óbvio.
- **Não introduza** emojis em código ou mensagens de commit a menos que explicitamente pedido.

## Padrões de UI

- Grids do dashboard: 2×4 `QGridLayout` com `setColumnStretch(c, 1)` e `setColumnMinimumWidth(c, 168)`. `KpiCard(compact=True)` tem altura fixa (112) e largura expansível (mín. 168).
- Páginas CRUD herdam de `CrudPage` (em `app/ui/widgets/crud_page.py`); diálogos de formulário herdam de `FormDialog`.
- Sinais de mudança: cada view CRUD emite `data_changed`. `MainWindow._connect_data_changes` encadeia esses sinais para recarregar dashboard, calendário e histórico.
- Alinhamentos e fontes vêm do `style.qss`. Evite `setStyleSheet` inline quando um seletor global resolve.

## Dados e datas

- Todas as datas são `datetime.date` em Python e `TEXT` ISO (`YYYY-MM-DD`) no SQLite. Use `date(col)` em filtros SQL.
- Mês de referência é string `YYYY-MM` (ex.: `fixed_expense_months.ano_mes`, `income_months.ano_mes`).
- Em `income_sources`, `tipo` ∈ `recorrente` | `avulsa` | `parcelada`. O índice único de nome é **parcial** (`WHERE tipo <> 'avulsa'`): rendas avulsas podem repetir o mesmo nome.
- Ao projetar um "dia do mês" (ex.: `dia_recebimento`, `dia_pagamento_fatura`) que não existe no mês alvo, use o **último dia do mês** (helper `_ultimo_dia_mes` em `calendar_service.py`).
- Moeda é `float` em reais; formate sempre via `format_currency`.

## Livro-caixa (saldo em contas)

- Cada conta tem `saldo_inicial` e movimentações na tabela `account_transactions` (campo único `transaction_key` para idempotência).
- Débitos automáticos: pagamentos em conta, fatura de cartão paga, fixo marcado como pago (sem duplicar o espelho em Pagamentos — `payments_service.create(..., record_ledger=False)`), assinaturas em conta e parcelas em conta nas abas **Situação mensal**, renda com conta de crédito ao marcar recebido.
- Ajustes manuais: tela **Contas e cartões** → **Ajustar saldo…**
- Bases de dados antigas: defina o **saldo inicial** de cada conta coerente com o extrato; histórico anterior não é recriado automaticamente no livro-caixa.

## Antes de concluir uma tarefa

1. Rodar `make check` (ou `poetry run python -m compileall -q app main.py`).
2. Chamar `read_lints` / verificar lints no editor para os arquivos tocados.
3. Não editar `poetry.lock` manualmente; se precisar de nova dependência, rode `poetry add <pkg>`.
4. Não commitar o banco (`*.db`) nem artefatos de build (`dist/`, `build/build/`).
5. Não criar arquivos novos se uma edição resolve. Em especial, **não** crie docs/README adicionais sem pedido explícito.

## Fora de escopo por padrão

- Duplicar cenários já cobertos só para inflar cobertura sem pedido explícito.
- Mudar stack (Qt → Tkinter/Electron; SQLite → Postgres).
- Introduzir rede externa; o app é intencionalmente offline.
- Alterar a licença ou o conteúdo de `LICENSE`.

## Onde encontrar

- Repositórios (SQL sem transação): `app/repositories/` — ex.: `payments_repo`, `card_invoices_repo`, `installments_repo`, `subscriptions_repo`, `dashboard_repo`, `income_sources_repo`, `*_months_repo`.
- Schema e migrações: `app/database/schema.sql`, `app/database/migrations.py`
- Regras agregadas do dashboard: `app/services/dashboard_service.py`
- Projeção de eventos (calendário e próximos vencimentos): `app/services/calendar_service.py`
- Faturas de cartão: `app/services/card_invoices_service.py`
- Investimentos: `app/services/investments_service.py`
- Situação mensal (renda, parcelas, assinaturas): `app/services/income_months_service.py`, `app/services/installment_months_service.py`, `app/services/subscription_months_service.py`
- Widgets reutilizáveis: `app/ui/widgets/`
- Testes automatizados: `tests/` (`make test`). Ao alterar `app/services/`, atualize ou acrescente testes em `tests/test_*_service.py` quando mudar regras, validações ou livro-caixa. Cobertura opcional: `poetry add --group dev pytest-cov && poetry lock`, depois `make test-cov` (relatório em `app/services`).
- Ponto de entrada: `main.py`
