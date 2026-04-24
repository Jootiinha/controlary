# Controle Financeiro

App desktop para controle de gastos pessoais, feito em **Python + PySide6 + SQLite**.
Roda 100% offline, com persistência local e interface nativa moderna.

## Funcionalidades

- **Dashboard** com KPIs do mês corrente (gasto previsto unifica faturas/recorrentes/fixos e mostra o realizado em subtítulo; saldo fim do mês = renda mensal + saldos em contas − gasto previsto)
  - Fluxo: renda mensal, gasto previsto no mês, margem de fluxo, saldos em contas e saldo fim do mês (est.)
  - Compromissos: investimentos, fixos pendentes, assinaturas
  - Tabela de **próximos vencimentos** (14 dias), gráfico anual e quebra por conta/forma de pagamento
- **Renda**: fontes **recorrentes**, **avulsas** e **parceladas** (com competência e marcação recebido/pendente por mês), dia de recebimento e status ativa/inativa
- **Contas e cartões**: cadastro base, livro-caixa (`saldo_inicial` + movimentações), com dia de pagamento da fatura por cartão
- **Categorias**: cadastro com cor e tipo sugerido; vínculo opcional em pagamentos, parcelamentos, assinaturas, fixos e investimentos
- **Pagamentos**: CRUD com valor, descrição, data, conta/cartão, categoria, forma e observação
- **Parcelamentos** (cartão de crédito): situação mensal (pago/pendente por competência); vencimento segue o dia de pagamento da fatura do cartão
- **Assinaturas** recorrentes: status ativa/pausada/cancelada, dia de cobrança, valor mensal e situação mensal
- **Gastos fixos**: cadastro com valor mensal, dia de vencimento e marcação de pago/pendente por mês (com valor efetivo opcional)
- **Faturas de cartão**: competência por cartão, valor total, status e pagamento com conta
- **Investimentos**: aplicações por conta, snapshots de valor ao longo do tempo e visão consolidada
- **Calendário**: visão mensal com marcação dos dias que têm eventos (pagamentos, rendas, assinaturas, fixos e parcelas)
- **Tema claro ou escuro** (menu **Exibir**; preferência em `QSettings`)
- **Histórico e análises** com tabela de transações + gráficos embedados (matplotlib):
  - **Renda vs despesa**
  - **Fluxo acumulado**
  - **Comprometimento %** (renda)
  - **Custo de vida** (gastos por mês)
  - **Evolução da fatura**
  - **Categorias** (livro-caixa e custo de vida)
  - **Saldo devedor** (parcelamentos)
  - **Investimentos** (visão geral)

## Stack

- Python ≥ 3.11 (`<3.14`)
- [PySide6](https://doc.qt.io/qtforpython-6/) (Qt 6)
- SQLite (via `sqlite3` da stdlib)
- [matplotlib](https://matplotlib.org/) (backend `QtAgg`)
- [mplcursors](https://mplcursors.readthedocs.io/) (interação nos gráficos)
- [Pillow](https://python-pillow.org/) (geração de ícones)
- [Poetry](https://python-poetry.org/) para dependências
- [PyInstaller](https://pyinstaller.org/) para empacotamento
- **Dev**: [pytest](https://pytest.org/) e [pytest-qt](https://pytest-qt.readthedocs.io/) (grupo `dev` no Poetry)

## Estrutura

```
controlary/
├── app/
│   ├── ui/              # QMainWindow, views, theme.py, style.qss / style_dark.qss
│   │   ├── widgets/     # card, chart_canvas, crud_page, form_dialog,
│   │   │                # category_picker, readonly_table, payment_confirmation_dialog, wrapping_header
│   │   ├── main_window.py
│   │   ├── dashboard_view.py
│   │   ├── income_sources_view.py
│   │   ├── accounts_cards_view.py
│   │   ├── categories_view.py
│   │   ├── payments_view.py
│   │   ├── installments_view.py
│   │   ├── subscriptions_view.py
│   │   ├── fixed_expenses_view.py
│   │   ├── card_invoices_view.py
│   │   ├── calendar_view.py
│   │   ├── history_view.py
│   │   ├── investments_view.py
│   │   └── style.qss
│   ├── models/          # Account, Card, Category, Payment, Installment,
│   │                    # Subscription, FixedExpense, IncomeSource,
│   │                    # CardInvoice, Investment, …
│   ├── database/        # connection.py, schema.sql, migrations.py
│   ├── repositories/    # SQL por domínio (sem transação própria)
│   ├── services/        # regras, orquestração, transações; chamam repositories
│   ├── events.py        # AppEvents (sinais p/ sincronizar UI após mudanças)
│   ├── charts/          # funções plot(ax, …) matplotlib (renda_vs_despesa,
│   │                    # category_month_views, …)
│   ├── importers/       # reservado para importadores (ex.: banks/)
│   └── utils/           # formatação, mes_ano (YYYY-MM), paths
├── tests/               # pytest (dashboard, views, serviços)
├── assets/              # icon.png, icon.ico, icon.icns
├── build/
│   ├── controle-financeiro.spec   # spec PyInstaller
│   ├── build_macos.sh
│   ├── build_windows.bat
│   └── make_icon.py               # gera ícones placeholder
├── main.py
├── pyproject.toml
├── AGENTS.md            # instruções para agentes de IA
└── README.md
```

## Requisitos

- **Python 3.11 ou superior** (até 3.13)
- **Poetry 1.8+** (recomendo 2.x) — instale em <https://python-poetry.org/docs/#installation>

## Comandos Make

O `Makefile` na raiz concentra os comandos do dia a dia. Rode `make help` para ver a lista.

| Comando             | O que faz                                                           |
| ------------------- | ------------------------------------------------------------------- |
| `make help`         | Lista todos os alvos disponíveis                                    |
| `make install`      | Instala dependências de runtime via Poetry (`poetry install --no-root`) |
| `make install-all`  | Instala runtime + grupo `build` (inclui PyInstaller)                |
| `make run`          | Roda o app localmente (`poetry run python main.py`)                 |
| `make test`         | Roda a suíte pytest (`poetry install --with dev` se necessário)     |
| `make test-cov`     | Pytest com cobertura em `app/services` (exige `pytest-cov` no grupo dev) |
| `make icon`         | Gera os ícones placeholder em `assets/` (`.png`, `.ico`, `.icns`)   |
| `make build-mac`    | Empacota o app para macOS (`dist/ControleFinanceiro.app`)           |
| `make build-win`    | Empacota o app para Windows (`dist\ControleFinanceiro.exe`)         |
| `make check`        | Valida o `pyproject.toml` e compila todos os `.py`                  |
| `make reset-db`     | Apaga o banco em `~/.controle-financeiro/app.db`                    |
| `make clean`        | Remove `build/`, `dist/`, caches e arquivos `.pyc`                  |

Fluxo típico para começar a desenvolver:

```bash
make install
make run
```

## Rodar localmente (sem Make)

Caso prefira chamar o Poetry direto:

```bash
poetry install               # cria venv em .venv/ e instala deps
poetry run python main.py    # abre a janela
```

O banco SQLite é criado automaticamente em:

- **macOS / Linux**: `~/.controle-financeiro/app.db`
- **Windows**: `%USERPROFILE%\.controle-financeiro\app.db`

Para usar outro caminho basta exportar `CONTROLE_FINANCEIRO_DB`:

```bash
CONTROLE_FINANCEIRO_DB=/tmp/teste.db poetry run python main.py
```

## Ícone do aplicativo

Já existe um ícone placeholder em `assets/` (`icon.png`, `icon.ico`, `icon.icns`).

Para **regenerar** o placeholder (um cifrão com fundo gradiente azul):

```bash
poetry install --with build
poetry run python build/make_icon.py
```

Para **usar seu próprio ícone**, substitua os três arquivos em `assets/` mantendo os nomes:

- `assets/icon.png` — 1024×1024 (fonte)
- `assets/icon.ico` — usado no Windows (multi-size)
- `assets/icon.icns` — usado no macOS

Dicas para converter:

```bash
# PNG -> ICNS (macOS)
poetry run python build/make_icon.py   # já faz tudo a partir do icon.png

# PNG -> ICO (qualquer OS, via Pillow)
python -c "from PIL import Image; Image.open('assets/icon.png').save('assets/icon.ico', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
```

## Empacotamento (desktop app)

### Pré-requisito comum

```bash
poetry install --with build
```

### macOS → `dist/ControleFinanceiro.app`

```bash
bash build/build_macos.sh
```

Equivalente manual:

```bash
poetry run pyinstaller build/controle-financeiro.spec --noconfirm
```

Para fixar no desktop / Applications:

```bash
cp -R dist/ControleFinanceiro.app /Applications/
```

### Windows → `dist\ControleFinanceiro.exe`

Em um **PowerShell ou cmd.exe** (não WSL):

```bat
build\build_windows.bat
```

Equivalente manual:

```bat
poetry run pyinstaller build\controle-financeiro.spec --noconfirm
```

Para criar atalho no Desktop, clique com o botão direito no `.exe` → **Enviar para → Área de Trabalho**.

### Comando PyInstaller "pronto" (sem usar o `.spec`)

Caso prefira linha única, equivalente aproximado:

```bash
# macOS
poetry run pyinstaller --noconfirm --windowed --name "ControleFinanceiro" \
    --icon assets/icon.icns \
    --add-data "app/database/schema.sql:app/database" \
    --add-data "app/ui/style.qss:app/ui" \
    --add-data "assets:assets" \
    main.py
```

```bat
REM Windows
poetry run pyinstaller --noconfirm --windowed --name "ControleFinanceiro" ^
    --icon assets\icon.ico ^
    --add-data "app\database\schema.sql;app\database" ^
    --add-data "app\ui\style.qss;app\ui" ^
    --add-data "assets;assets" ^
    main.py
```

> O `.spec` é recomendado porque já faz `BUNDLE` no macOS (gerando `.app`) e centraliza a configuração.

## Banco de dados

Schema em [app/database/schema.sql](app/database/schema.sql). Tabelas principais:

- `accounts(id, nome, observacao, saldo_inicial)` — contas; movimentações em **`account_transactions`** (`data`, `valor`, `origem`, **`transaction_key`** único para idempotência)
- `categories(id, nome, tipo_sugerido, cor, ativo)` — categorias; **`category_id`** opcional em `payments`, `installments`, `subscriptions`, `fixed_expenses`, `investments`
- `cards(id, nome, account_id, dia_pagamento_fatura, observacao)` — cartões e dia do vencimento da fatura
- **`income_sources`**: `tipo` ∈ `recorrente` | `avulsa` | `parcelada`; `mes_referencia`, `total_parcelas`, `parcelas_recebidas` conforme o tipo; índice único de nome **apenas para não-avulsas** (avulsas podem repetir nome)
- **`income_months`**: `(income_source_id, ano_mes)` com status recebido/pendente
- `payments(..., conta_id, cartao_id, category_id, …)` — pagamentos lançados
- `installments(..., cartao_id, category_id, …)` + **`installment_months`**: situação por competência
- `subscriptions(..., account_id, card_id, category_id, …)` + **`subscription_months`**
- `fixed_expenses(..., category_id, …)` + **`fixed_expense_months`** (incl. `valor_efetivo` opcional)
- **`card_invoices`**: fatura por `(cartao_id, ano_mes)`, valor, status, conta de pagamento
- **`investments`** + **`investment_snapshots`**: posições e histórico de valor

Migrações incrementais em [app/database/migrations.py](app/database/migrations.py) garantem compatibilidade com bancos antigos.

Na primeira execução, cadastre contas e cartões em **Contas e cartões** antes de lançar pagamentos ou parcelamentos.

Para fazer backup do seu banco:

```bash
cp ~/.controle-financeiro/app.db ~/Desktop/app-backup-$(date +%Y%m%d).db
```

## Melhorias futuras

- **Importação OFX/CSV** dos extratos (estrutura reservada em `app/importers/`)
- **Exportar** relatórios em CSV/PDF
- **Múltiplas moedas** com conversão automática
- **Backup automático** (rotação diária em `~/.controle-financeiro/backups/`)
- **Metas mensais** por categoria com alerta ao atingir X%
- **Notificações** de cobranças próximas (assinaturas e parcelas do mês)
- **Autenticação local** opcional (senha/fingerprint)
- **Sincronização** opcional via Dropbox/iCloud Drive (apontando o DB para uma pasta sincronizada)

## Licença

Uso pessoal — adapte como quiser.