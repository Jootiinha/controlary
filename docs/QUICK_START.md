# 🚀 Quick Start - 5 Minutes

Get the Controle Financeiro Web application running in 5 minutes.

---

## ⚡ Ultra Quick (3 steps)

```bash
# Step 1: Clone and setup
git clone <repo>
cd controle-financeiro
cp .env.example .env

# Step 2: Install everything
make install-dev

# Step 3: Start development
make backend-dev      # Terminal 1: Backend
make frontend-dev     # Terminal 2: Frontend
```

**Done!** 🎉
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📋 Prerequisites (1 minute)

Verify you have:
```bash
python --version      # 3.11+
node --version        # 18+
npm --version         # 9+
poetry --version      # 1.7+
```

**Don't have Poetry?**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

---

## 🛠️ Installation (2 minutes)

```bash
# Navigate to project
cd controle-financeiro

# Copy environment template
cp .env.example .env

# Install all dependencies
make install-dev

# Verify status
make status
```

Expected output:
```
Backend: ✓ Installed
Frontend: ✓ Installed
Docker: ✗ No containers (optional)
```

---

## ▶️ Run Application (1 minute)

### Option 1: Local Development (Recommended for coding)

**Terminal 1 - Backend**:
```bash
make backend-dev
# Output: Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 - Frontend**:
```bash
make frontend-dev
# Output: VITE running on http://localhost:5173
```

### Option 2: Docker (Recommended for full stack)

```bash
make docker-up
# Wait for "healthy" status

# Access:
# Frontend: http://localhost
# Backend: http://localhost:8000
```

### Option 3: Manual (Advanced)

```bash
# Backend
cd backend
poetry run uvicorn main:app --reload

# Frontend (in another terminal)
cd frontend
npm run dev
```

---

## ✅ Verify It Works

1. **Frontend loads**
   - Open http://localhost:5173 or http://localhost
   - See Controle Financeiro UI

2. **Backend is running**
   - Open http://localhost:8000/health
   - Should see: `{"status":"healthy",...}`

3. **API docs available**
   - Open http://localhost:8000/docs
   - See Swagger interface

4. **Can login** (optional)
   - Register a test account
   - Try creating an account
   - Try creating a payment

---

## 📚 Next Steps

### Want to develop?
→ Read **[guides/DEVELOPMENT.md](./guides/DEVELOPMENT.md)**

### Want to understand the code?
→ Read **[architecture/ARCHITECTURE.md](./architecture/ARCHITECTURE.md)**

### Want to deploy?
→ Read **[deployment/DEPLOYMENT.md](./deployment/DEPLOYMENT.md)**

### Want to run tests?
```bash
make backend-test         # Run tests
make backend-test-cov     # With coverage
```

### Want to check code quality?
```bash
make backend-lint         # Lint code
make backend-format       # Format code
make backend-typecheck    # Type check
```

---

## 🆘 Quick Troubleshooting

### Port 8000 already in use
```bash
lsof -ti:8000 | xargs kill -9
make backend-dev
```

### Port 5173 already in use
```bash
make frontend-dev      # Tries alternate port
```

### Dependencies not installed
```bash
make install-dev       # Install everything
```

### Docker not running
```bash
docker-compose up      # Start Docker first
```

### Still stuck?
→ Read **[development/TROUBLESHOOTING.md](./development/TROUBLESHOOTING.md)**

---

## 📋 Common Commands

```bash
# Development
make backend-dev              # Start backend
make frontend-dev             # Start frontend
make backend-test             # Run tests

# Quality
make backend-lint             # Check code
make backend-format           # Format code

# Docker
make docker-up                # Start containers
make docker-down              # Stop containers

# Help
make help                     # See all commands
```

---

## 🎯 What You Get

✅ **Backend API**
- FastAPI with async support
- JWT authentication
- 15+ entities (accounts, payments, cards, etc.)
- Analytics & KPIs
- Full audit logging
- Rate limiting & CSRF protection

✅ **Frontend**
- Vue.js 3 SPA
- Real-time data binding
- Responsive design
- Charts & analytics
- User authentication

✅ **Security**
- Password hashing (Bcrypt)
- CSRF protection
- Rate limiting
- Input validation
- Audit logs

✅ **Developer Experience**
- Hot reload (changes auto-refresh)
- TypeScript support (optional)
- Comprehensive tests (50+)
- 95%+ test coverage
- Makefile for all tasks

---

## 💡 Pro Tips

### Tip 1: Use Make for everything
```bash
make help      # See all available commands
```

### Tip 2: Run tests before committing
```bash
make backend-test
make backend-lint
```

### Tip 3: Format code automatically
```bash
make backend-format
```

### Tip 4: Monitor logs
```bash
make docker-logs       # All logs
make docker-logs-backend   # Backend only
```

### Tip 5: Reset database if needed
```bash
make db-reset          # Warns you!
make db-migrate        # Reapply migrations
```

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **README.md** | Project overview |
| **docs/README.md** | Documentation index |
| **docs/guides/** | Step-by-step guides |
| **docs/security/** | Security documentation |
| **docs/deployment/** | Production setup |

---

## ✨ You're Ready!

You've successfully set up Controle Financeiro Web! 🎉

### What's next?

**Option A: Explore the UI**
- http://localhost:5173 or http://localhost
- Create some test accounts
- Play with features

**Option B: Start coding**
- Read docs/guides/DEVELOPMENT.md
- Make code changes
- See hot reload in action

**Option C: Read the docs**
- Review docs/architecture/
- Understand the design
- Learn how it all works

---

## 🔗 Quick Links

| Link | Purpose |
|------|---------|
| http://localhost:5173 | Frontend (dev) |
| http://localhost | Frontend (docker) |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | API documentation |
| http://localhost:8000/health | Health check |

---

## ⏱️ Time Check

Expected time breakdown:
- Prerequisites check: 1 min
- Installation: 2 min
- Running app: 1 min
- Verification: 1 min
- **Total: ~5 minutes** ✅

---

**Next**: Read **[guides/DEVELOPMENT.md](./guides/DEVELOPMENT.md)** for detailed development guide.

---

**Questions?** See [docs/README.md](./README.md) for more documentation.
