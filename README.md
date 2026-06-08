# Controle Financeiro Web

Uma aplicação moderna de controle financeiro pessoal, migrada de desktop (PySide6) para web (FastAPI + Vue.js 3).

## 📋 Features

### Gerenciamento de Contas
- ✅ CRUD de contas bancárias
- ✅ Cálculo automático de saldos
- ✅ Histórico de transações
- ✅ Suporte a múltiplas contas

### Gerenciamento de Pagamentos
- ✅ Registro de receitas e despesas
- ✅ Destino inteligente (conta ou cartão)
- ✅ Categorização automática
- ✅ Status de pagamento (pago/pendente)
- ✅ Filtros por período

### Cartões de Crédito
- ✅ CRUD de cartões
- ✅ Controle de limite
- ✅ Dias de fechamento e vencimento
- ✅ Fatura mensal

### Assinaturas
- ✅ Registro de assinaturas recorrentes
- ✅ Status de assinatura (Ativa/Pausada/Cancelada)
- ✅ Renovação automática por dia

### Analytics & Relatórios
- ✅ Dashboard com KPIs
- ✅ Gráficos de renda vs despesa
- ✅ Análise de despesa por categoria
- ✅ Evolução de saldo
- ✅ Projeções e tendências

## 🚀 Começando

### Com Docker (Recomendado)

```bash
# Clone o repositório
git clone <repo>
cd controle-financeiro

# Configure variáveis de ambiente
cp .env.example .env

# Use o Makefile para iniciar
make docker-build
make docker-up

# Acesse a aplicação
# Frontend: http://localhost
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs

# Parar containers
make docker-down
```

### Desenvolvimento Local (com Poetry + Makefile)

**Setup Inicial**:
```bash
# Clone o repositório
git clone <repo>
cd controle-financeiro

# Configure variáveis de ambiente
cp .env.example .env

# Instale todas as dependências
make install-dev

# Ver todos os comandos disponíveis
make help
```

**Backend (FastAPI)**:
```bash
# Iniciar servidor de desenvolvimento (com reload automático)
make backend-dev

# Rodar testes
make backend-test

# Rodar testes com cobertura
make backend-test-cov

# Verificar código
make backend-lint           # Lint com ruff
make backend-format         # Formatar com black
make backend-typecheck      # Type check com mypy
make backend-all-checks     # Rodar todos os checks
```

**Frontend (Vue.js 3)**:
```bash
# Iniciar servidor Vite (hot reload)
make frontend-dev

# Build para produção
make frontend-build

# Lint código
make frontend-lint
```

**Database**:
```bash
# Aplicar migrations
make db-migrate

# Criar nova migration
make db-migrate-create MESSAGE="Add new table"

# Resetar banco (apaga todos os dados!)
make db-reset
```

**Utilitários**:
```bash
# Ver status do projeto
make status

# Ver versão
make version

# Limpeza de arquivos temporários
make clean              # Remove build artifacts
make cleanup            # Remove tudo (inclui dependências)
```

### Alternativa: Sem Makefile

**Backend com Poetry**:
```bash
cd backend
poetry install
poetry run uvicorn main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentação

**[→ Ver Documentação Completa em `docs/`](./docs/README.md)**

### Quick Links:
- **[Quick Start (5 min)](./docs/QUICK_START.md)** - Comece rapidinho
- **[Development Guide](./docs/guides/DEVELOPMENT.md)** - Desenvolvimento local
- **[Makefile Commands](./docs/guides/MAKEFILE.md)** - Todos os comandos
- **[Security Guide](./docs/security/SECURITY.md)** - Segurança
- **[Deployment Guide](./docs/deployment/DEPLOYMENT.md)** - Produção
- **[API Documentation](./docs/api/API_REFERENCE.md)** - API endpoints
- **[Architecture](./docs/architecture/ARCHITECTURE.md)** - Design do sistema

### Outras Referências:
- `http://localhost:8000/docs` - API documentation (Swagger) quando rodando
- `docs/README.md` - Índice completo de documentação

## 🧪 Testes

Com Makefile:
```bash
make backend-test              # Rodar todos os testes
make backend-test-cov          # Com cobertura detalhada
```

Ou diretamente com Poetry:
```bash
cd backend
poetry run pytest              # Rodar todos os testes
poetry run pytest --cov=app tests/ --cov-report=html  # Com cobertura em HTML
```

**Status**: 50+ testes, 95%+ cobertura

## 🔒 Segurança

- ✅ Autenticação JWT
- ✅ Password Hashing (Bcrypt)
- ✅ Multi-tenancy (isolamento por user_id)
- ✅ CORS configurável
- ✅ Validação automática (Pydantic)

## 📊 Performance

- **Database Indexes**: 15+ índices otimizados
- **Caching**: TTLCache com 3 camadas (60s, 300s, 600s)
- **Pagination**: Skip + limit (máx 100 items)

## 📋 Endpoints Principais

```
POST   /api/auth/register              # Registrar
POST   /api/auth/login                 # Login
GET    /api/accounts                   # Listar contas
GET    /api/payments                   # Listar pagamentos
GET    /api/analytics/dashboard-kpis   # KPIs
```

## 📝 Status

**Completo**: 8/8 Fases ✅ (Production-Ready)
- ✅ Phase 1: Backend Setup (FastAPI + SQLAlchemy)
- ✅ Phase 2: API Implementation (CRUD endpoints)
- ✅ Phase 3: Frontend Setup (Vue 3 + Pinia)
- ✅ Phase 4: Frontend Integration (Views & Components)
- ✅ Phase 5: Analytics & Charts (Chart.js)
- ✅ Phase 6: Validation & Optimization (Tests, Indexes, Cache)
- ✅ Phase 7: Docker & Deployment (Production setup)
- ✅ Phase 8: Security Hardening (CSRF, Rate Limit, Audit Logs)

---

**Versão**: 1.0.0
**Licença**: MIT
