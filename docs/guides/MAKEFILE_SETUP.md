# Makefile & Poetry Setup - Quick Reference

**Data**: Junho 2024
**Versão**: 1.0.0

---

## O Que Mudou

A partir desta atualização, o projeto agora usa:

1. **Poetry** - Gerenciador de dependências Python moderno (em vez de pip + requirements.txt)
2. **Makefile** - Simplifica execução de comandos comuns
3. **Melhor estrutura de desenvolvimento** - `.editorconfig`, `.gitignore` configurados

---

## 📦 Instalação Rápida

```bash
# 1. Clone e configure
git clone <repo>
cd controle-financeiro
cp .env.example .env

# 2. Instale tudo
make install-dev

# 3. Verifique
make status

# 4. Comece a desenvolver
make backend-dev      # Terminal 1: Backend
make frontend-dev     # Terminal 2: Frontend
```

---

## 🎯 Comandos Principais

### Setup
```bash
make install            # Instalar dependências
make install-dev        # Instalar com dev tools
```

### Backend (FastAPI)
```bash
make backend-dev        # Iniciar servidor (port 8000)
make backend-test       # Rodar testes
make backend-test-cov   # Testes + cobertura
make backend-lint       # Verificar código
make backend-format     # Formatar código
```

### Frontend (Vue.js)
```bash
make frontend-dev       # Iniciar dev server (port 5173)
make frontend-build     # Build para produção
```

### Docker
```bash
make docker-build       # Build imagens
make docker-up          # Iniciar containers
make docker-down        # Parar containers
make docker-logs        # Ver logs
```

### Limpeza
```bash
make clean              # Remove build artifacts
make cleanup            # Remove tudo (dependências também)
```

---

## 📁 Arquivos Novos/Modificados

### Novos Arquivos
- ✅ `Makefile` - 300+ linhas de comandos de desenvolvimento
- ✅ `backend/pyproject.toml` - Dependências Python com Poetry
- ✅ `.gitignore` - Ignora arquivos desnecessários
- ✅ `.editorconfig` - Padronização de estilo
- ✅ `DEVELOPMENT.md` - Guia de desenvolvimento
- ✅ `MAKEFILE_SETUP.md` - Este arquivo

### Modificados
- ✅ `README.md` - Atualizado com comandos Makefile/Poetry

---

## 🔄 Migração de pip para Poetry

### Backend

**Antes** (pip):
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Depois** (Poetry):
```bash
make install-dev
make backend-dev
```

### Equivalência de Comandos

| pip | Poetry |
|-----|--------|
| `pip install` | `poetry install` |
| `pip install -e .` | `poetry install` |
| `pip list` | `poetry show` |
| `pip freeze` | `poetry export` |
| `pip install pkg` | `poetry add pkg` |
| `pip install --dev pkg` | `poetry add --group dev pkg` |

### Por que Poetry?

✅ **Lock file** - `poetry.lock` garante versões exatas (like npm)
✅ **Dependency resolution** - Resolve conflitos automaticamente
✅ **Scripts** - Comandos customizados (veja `pyproject.toml`)
✅ **Virtual env** - Gerencia automaticamente
✅ **Publicação** - Fácil publicar no PyPI
✅ **Moderno** - Padrão da comunidade Python

---

## 📋 Fluxo de Desenvolvimento Típico

### Dia 1: Setup
```bash
git clone <repo>
cd controle-financeiro
cp .env.example .env
make install-dev
make status
```

### Dia 2+: Desenvolvimento
```bash
# Terminal 1
make backend-dev

# Terminal 2
make frontend-dev

# Terminal 3 (quando precisa testar)
make backend-test
```

### Antes de Push
```bash
make backend-lint
make backend-format
make backend-test
git add .
git commit -m "feature: description"
git push origin feature-branch
```

---

## 🐳 Docker Development

```bash
# Começar
make docker-build
make docker-up

# Monitorar
make docker-logs

# Parar
make docker-down

# Reiniciar (após mudança)
make docker-restart
```

**Acesso**:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## ⚙️ Customizar Makefile

Para adicionar novo comando, edite `Makefile`:

```makefile
novo-comando: ## Descrição do comando
	@echo "$(CYAN)Executando...$(NC)"
	cd backend && poetry run seu-comando
	@echo "$(GREEN)✓ Pronto!$(NC)"
```

Então use:
```bash
make novo-comando
```

---

## 🔍 Troubleshooting

### "Poetry not found"
```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

### "Make not found" (Windows)
Instale: https://www.gnu.org/software/make/

Ou use WSL (recomendado)

### Port 8000 já em uso
```bash
# Matar processo
lsof -ti:8000 | xargs kill -9

# Ou ver qual processo usa
lsof -i :8000
```

---

## 📖 Recursos

- `DEVELOPMENT.md` - Guia completo de desenvolvimento
- `README.md` - Overview do projeto
- `SECURITY.md` - Guia de segurança
- `Makefile` - Todos os comandos disponíveis

---

## ✅ Checklist de Migração

Se você tem um projeto antigo com pip:

- [ ] Backup do projeto antigo
- [ ] Instalar Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- [ ] Copiar `backend/pyproject.toml` novo
- [ ] Deletar `backend/requirements.txt` (ou guardar como referência)
- [ ] Rodar `make install-dev`
- [ ] Testar: `make backend-test`
- [ ] Confirmar que tudo funciona
- [ ] Commit do novo setup

---

## 📞 Suporte

- Veja `Makefile` para todos os comandos: `make help`
- Veja `DEVELOPMENT.md` para desenvolvimento detalhado
- Veja `README.md` para overview do projeto

---

**Status**: ✅ **Pronto para Uso**

O projeto está totalmente configurado com Poetry + Makefile. Comece com `make install-dev`!
