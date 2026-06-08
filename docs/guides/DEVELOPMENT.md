# Development Guide

Guia completo para desenvolvimento do Controle Financeiro Web usando Poetry e Makefile.

---

## 📋 Pré-requisitos

- **Python 3.11+** - https://www.python.org/downloads/
- **Node.js 18+** - https://nodejs.org/
- **Poetry** - https://python-poetry.org/docs/#installation
- **Git** - https://git-scm.com/

### Verificar Instalações

```bash
python --version        # Python 3.11+
node --version         # Node 18+
npm --version          # npm 9+
poetry --version       # Poetry 1.7+
git --version          # Git 2.0+
```

---

## 🚀 Setup Inicial

### 1. Clone e Configure

```bash
# Clone o repositório
git clone <repo>
cd controle-financeiro

# Configure variáveis de ambiente
cp .env.example .env

# Ver todos os comandos disponíveis
make help
```

### 2. Instale Dependências

```bash
# Opção 1: Instalar tudo (recomendado)
make install-dev

# Opção 2: Instalar apenas para produção
make install

# Opção 3: Instalar manualmente
make backend-install-dev
make frontend-install
```

### 3. Verifique a Instalação

```bash
make status
# Deve mostrar ✓ para Backend, Frontend e Docker
```

---

## 💻 Desenvolvimento Local

### Iniciar Backend e Frontend Simultaneamente

**Terminal 1 - Backend**:
```bash
make backend-dev
# Acesse: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Terminal 2 - Frontend**:
```bash
make frontend-dev
# Acesse: http://localhost:5173
```

### Ou tudo junto com Docker

```bash
make dev-docker
# Frontend: http://localhost
# Backend: http://localhost:8000
```

---

## 🧪 Testes

### Rodar Testes

```bash
# Testes simples
make backend-test

# Com cobertura (gera relatório HTML)
make backend-test-cov

# Exibir cobertura em HTML
open backend/htmlcov/index.html
```

### Executar Testes Específicos

```bash
cd backend
poetry run pytest tests/test_auth.py -v
poetry run pytest tests/test_payments.py::test_create_payment -v
```

---

## 🔍 Code Quality

### Linting e Formatting

```bash
# Verificar código com ruff
make backend-lint

# Formatar código com black
make backend-format

# Type checking com mypy
make backend-typecheck

# Rodar todos os checks
make backend-all-checks
```

### Automaticamente (Git Hooks)

Para rodar checks automaticamente ao fazer commit, crie um `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd backend
poetry run ruff check app/
poetry run black --check app/
poetry run pytest
```

---

## 📊 Database

### Migrations com Alembic

```bash
# Ver status
poetry run alembic current

# Aplicar migration pendente
make db-migrate

# Criar nova migration
make db-migrate-create MESSAGE="Add new column to users"

# Voltar para versão anterior
poetry run alembic downgrade -1
```

### Resetar Banco

```bash
# ⚠️ CUIDADO: Apaga todos os dados!
make db-reset

# Depois, aplicar migrations novamente
make db-migrate
```

---

## 🐳 Docker

### Desenvolvimento com Docker

```bash
# Build imagens
make docker-build

# Iniciar containers
make docker-up

# Parar containers
make docker-down

# Reiniciar containers
make docker-restart

# Ver logs
make docker-logs
make docker-logs-backend
make docker-logs-frontend

# Acessar shell dentro do container
make docker-shell-backend
make docker-shell-frontend
```

### Reconstruir Após Mudança de Dependências

```bash
make docker-down
make docker-build
make docker-up
```

---

## 📝 Estrutura de Diretórios

```
controle-financeiro/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── models/            # SQLAlchemy models
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── middleware/        # CSRF, security headers
│   │   ├── utils/             # Utilities (auth, rate limit)
│   │   └── database/          # Database setup
│   ├── tests/                 # Test files
│   ├── migrations/            # Alembic migrations
│   ├── pyproject.toml         # Poetry dependencies
│   ├── main.py                # FastAPI app entry point
│   └── config.py              # Configuration
│
├── frontend/                  # Vue.js 3 SPA
│   ├── src/
│   │   ├── components/        # Vue components
│   │   ├── views/             # Page views
│   │   ├── stores/            # Pinia store modules
│   │   ├── api/               # API client
│   │   ├── styles/            # Tailwind styles
│   │   ├── main.js            # Entry point
│   │   ├── App.vue            # Root component
│   │   └── router.js          # Vue Router config
│   ├── package.json           # npm dependencies
│   ├── vite.config.js         # Vite configuration
│   └── public/                # Static assets
│
├── Makefile                   # Development commands
├── docker-compose.yml         # Docker services
├── README.md                  # Project overview
├── DEVELOPMENT.md             # This file
├── SECURITY.md                # Security guide
└── .env.example               # Environment template
```

---

## 🔧 Configuração

### Variáveis de Ambiente

Crie `.env` baseado em `.env.example`:

```env
# Backend
ENVIRONMENT=development
DATABASE_URL=sqlite:///./controle_financeiro.db
JWT_SECRET_KEY=seu-secret-key-aqui-min-32-chars
LOG_LEVEL=DEBUG
SQLALCHEMY_ECHO=true

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000
VITE_APP_NAME=Controle Financeiro
```

### Configuração IDE

#### VS Code

Extensões recomendadas:
- Python (Microsoft)
- Pylance (Microsoft)
- Ruff (Astral Software)
- Black Formatter (Microsoft)
- Vue (Volar)
- Prettier
- EditorConfig (EditorConfig)

`settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    }
  },
  "[vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  }
}
```

#### PyCharm

1. **Interpreter**: `backend/.venv/bin/python`
2. **Tools → Python Integrated Tools → Default test runner**: pytest
3. **Tools → Python Integrated Tools → Package manager**: Poetry
4. **Languages & Frameworks → JavaScript → Prettier**: ativar

---

## 🐛 Troubleshooting

### Erro: "Poetry not found"

```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Adicionar ao PATH (macOS/Linux)
export PATH="$HOME/.local/bin:$PATH"

# Verificar
poetry --version
```

### Erro: "Python 3.11+ required"

```bash
# Verificar versão
python --version

# Se < 3.11, instalar nova versão
# macOS
brew install python@3.11

# Ubuntu
sudo apt-get install python3.11
```

### Erro: "Node modules not found"

```bash
make frontend-install
```

### Erro: "Database locked"

```bash
# Remover lock se houver
rm backend/data/*.db-journal

# Ou resetar completamente
make db-reset
```

### Backend não conecta ao banco

```bash
# Criar diretório
mkdir -p backend/data

# Aplicar migrations
make db-migrate
```

### Porta 8000 já em uso

```bash
# Matar processo na porta
lsof -ti:8000 | xargs kill -9

# Ou usar outra porta
cd backend && poetry run uvicorn main:app --reload --port 8001
```

---

## 📚 Recursos Úteis

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Vue 3**: https://vuejs.org/
- **Pinia**: https://pinia.vuejs.org/
- **Poetry**: https://python-poetry.org/docs/
- **Pytest**: https://docs.pytest.org/

---

## 🤝 Contributing

### Workflow

1. **Crie um branch**: `git checkout -b feature/sua-feature`
2. **Faça as mudanças**: Implemente sua feature
3. **Teste**: `make backend-test`
4. **Lint**: `make backend-lint`
5. **Format**: `make backend-format`
6. **Commit**: `git commit -m "Add feature description"`
7. **Push**: `git push origin feature/sua-feature`
8. **PR**: Abra um Pull Request

### Padrões de Código

- **Python**: Black (100 char) + Ruff
- **JavaScript**: Prettier + ESLint
- **Commits**: Conventional Commits

### Antes de Fazer Push

```bash
# Rodar todos os checks
make backend-all-checks

# Verificar se tudo passa
make docker-build
make docker-up
```

---

## 🔐 Security

Para questões de segurança, veja [SECURITY.md](./SECURITY.md) e [SECURITY_MAINTENANCE.md](./SECURITY_MAINTENANCE.md).

---

**Última atualização**: Junho 2024
**Versão**: 1.0.0
