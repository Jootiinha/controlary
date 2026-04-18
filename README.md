# Controle Financeiro

App desktop para controle de gastos pessoais, feito em **Python + PySide6 + SQLite**.
Roda 100% offline, com persistência local e interface nativa moderna.

## Funcionalidades

- **Dashboard** com KPIs do mês (gasto, previsto, assinaturas, parcelamentos, saldo devedor, quebra por conta e forma de pagamento)
- **Pagamentos**: CRUD com valor, descrição, data, conta, forma e observação
- **Parcelamentos** (cartão de crédito): cálculo automático de valor total, parcelas restantes, saldo devedor e status (ativo/quitado)
- **Assinaturas** recorrentes: status ativa/pausada/cancelada, dia de cobrança, valor mensal
- **Histórico** com tabela de transações + gráficos embedados (matplotlib):
  - Gastos por mês (últimos 12 meses)
  - Evolução da fatura por mês de referência
  - Distribuição por categoria
  - Projeção do saldo devedor

## Stack

- Python ≥ 3.11
- [PySide6](https://doc.qt.io/qtforpython-6/) (Qt 6)
- SQLite (via `sqlite3` da stdlib)
- [matplotlib](https://matplotlib.org/) (backend `QtAgg`)
- [Poetry](https://python-poetry.org/) para dependências
- [PyInstaller](https://pyinstaller.org/) para empacotamento

## Estrutura

```
controle-financeiro/
├── app/
│   ├── ui/              # QMainWindow, views e widgets reutilizáveis
│   │   ├── widgets/     # card, chart_canvas, form_dialog, crud_page
│   │   ├── main_window.py
│   │   ├── dashboard_view.py
│   │   ├── accounts_cards_view.py   # cadastro de contas e cartões
│   │   ├── payments_view.py
│   │   ├── installments_view.py
│   │   ├── subscriptions_view.py
│   │   ├── history_view.py
│   │   └── style.qss
│   ├── models/          # Account, Card, Payment, Installment, Subscription
│   ├── database/        # connection.py, schema.sql, migrations.py
│   ├── services/        # regras de negócio e queries agregadas
│   ├── charts/          # funções que desenham em um Axes matplotlib
│   └── utils/           # formatação, resolução de paths
├── assets/              # icon.png, icon.ico, icon.icns
├── build/
│   ├── controle-financeiro.spec   # spec PyInstaller
│   ├── build_macos.sh
│   ├── build_windows.bat
│   └── make_icon.py               # gera ícones placeholder
├── main.py
├── pyproject.toml
└── README.md
```

## Requisitos

- **Python 3.11 ou superior**
- **Poetry 1.8+** (recomendo 2.x) — instale em <https://python-poetry.org/docs/#installation>

## Comandos Make

O `Makefile` na raiz concentra os comandos do dia a dia. Rode `make help` para ver a lista.

| Comando             | O que faz                                                           |
| ------------------- | ------------------------------------------------------------------- |
| `make help`         | Lista todos os alvos disponíveis                                    |
| `make install`      | Instala dependências de runtime via Poetry (`poetry install --no-root`) |
| `make install-all`  | Instala runtime + grupo `build` (inclui PyInstaller)                |
| `make run`          | Roda o app localmente (`poetry run python main.py`)                 |
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

- `accounts(id, nome, observacao)` — contas bancárias cadastradas
- `cards(id, nome, account_id, observacao)` — cartões (opcionalmente vinculados a uma conta)
- `payments(..., conta_id → accounts, conta texto legado espelhado)` — pagamentos usam **conta** da lista
- `installments(..., cartao_id → cards, cartao texto legado espelhado)` — parcelamentos usam **cartão** da lista
- `subscriptions(..., account_id, card_id, conta_cartao legado)` — vínculo opcional com conta **ou** cartão (nunca os dois)

Na primeira execução, cadastre contas e cartões em **Contas e cartões** antes de lançar pagamentos ou parcelamentos. A migração copia textos antigos para novas tabelas quando possível.

Para fazer backup do seu banco:

```bash
cp ~/.controle-financeiro/app.db ~/Desktop/app-backup-$(date +%Y%m%d).db
```

## Melhorias futuras

- **Importação OFX/CSV** dos extratos bancários
- **Exportar** relatórios em CSV/PDF
- **Categorização** configurável (tabela `categories` com cor e ícone)
- **Múltiplas moedas** com conversão automática
- **Backup automático** (rotação diária em `~/.controle-financeiro/backups/`)
- **Modo escuro** (segunda QSS alternável)
- **Metas mensais** por categoria com alerta ao atingir X%
- **Notificações** de cobranças próximas (assinaturas e parcelas do mês)
- **Autenticação local** opcional (senha/fingerprint)
- **Sincronização** opcional via Dropbox/iCloud Drive (apontando o DB para uma pasta sincronizada)

## Licença

Uso pessoal — adapte como quiser.
