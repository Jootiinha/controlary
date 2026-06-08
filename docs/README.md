# 📚 Controle Financeiro - Documentation

Complete documentation for the Controle Financeiro Web application.

---

## 🗂️ Documentation Structure

```
docs/
├── README.md                    # This file
├── QUICK_START.md              # Get started in 5 minutes
├── guides/                     # User & developer guides
│   ├── MAKEFILE.md            # Makefile command reference
│   ├── DEVELOPMENT.md         # Development workflow
│   ├── POETRY.md              # Poetry package management
│   └── DATABASE.md            # Database & migrations
├── security/                  # Security documentation
│   ├── SECURITY.md            # Security best practices
│   ├── SECURITY_IMPLEMENTATION.md   # Technical details
│   ├── SECURITY_MAINTENANCE.md      # Operations & scanning
│   └── SECURITY_INDEX.md      # Security features index
├── deployment/                # Production deployment
│   ├── DEPLOYMENT.md          # Docker & production setup
│   ├── DOCKER.md              # Docker configuration
│   └── PRODUCTION_CHECKLIST.md # Pre-deployment checklist
├── architecture/              # Architecture & design
│   ├── ARCHITECTURE.md        # System architecture
│   ├── DATABASE_SCHEMA.md     # Database design
│   └── API_DESIGN.md          # API design patterns
├── api/                       # API documentation
│   ├── API_REFERENCE.md       # Endpoint reference
│   ├── AUTHENTICATION.md      # Auth flow
│   └── ERROR_CODES.md         # Error handling
└── development/              # Technical deep dives
    ├── PHASES.md             # Implementation phases
    ├── TECH_STACK.md         # Technology stack
    └── TROUBLESHOOTING.md    # Common issues
```

---

## 📖 Getting Started

### New to the Project?
1. Start with **[QUICK_START.md](./QUICK_START.md)** - 5 minutes
2. Read **[guides/DEVELOPMENT.md](./guides/DEVELOPMENT.md)** - Full setup
3. Check **[guides/MAKEFILE.md](./guides/MAKEFILE.md)** - Available commands

### Setting Up Locally?
- **[guides/POETRY.md](./guides/POETRY.md)** - Dependency management
- **[guides/DATABASE.md](./guides/DATABASE.md)** - Database setup
- **[guides/DEVELOPMENT.md](./guides/DEVELOPMENT.md)** - Full workflow

### Deploying to Production?
- **[deployment/DEPLOYMENT.md](./deployment/DEPLOYMENT.md)** - Production setup
- **[deployment/DOCKER.md](./deployment/DOCKER.md)** - Docker configuration
- **[deployment/PRODUCTION_CHECKLIST.md](./deployment/PRODUCTION_CHECKLIST.md)** - Pre-deployment

### Concerned About Security?
- **[security/SECURITY.md](./security/SECURITY.md)** - Best practices
- **[security/SECURITY_IMPLEMENTATION.md](./security/SECURITY_IMPLEMENTATION.md)** - Technical details
- **[security/SECURITY_MAINTENANCE.md](./security/SECURITY_MAINTENANCE.md)** - Operations

### Building an Integration?
- **[api/API_REFERENCE.md](./api/API_REFERENCE.md)** - Endpoint reference
- **[api/AUTHENTICATION.md](./api/AUTHENTICATION.md)** - Auth flow
- **[api/ERROR_CODES.md](./api/ERROR_CODES.md)** - Error handling

---

## 📋 Quick Command Reference

```bash
# Setup
make install-dev              # Install everything

# Development
make backend-dev              # Start backend (port 8000)
make frontend-dev             # Start frontend (port 5173)

# Testing
make backend-test             # Run tests
make backend-test-cov         # Tests with coverage

# Code quality
make backend-lint             # Check code
make backend-format           # Format code

# Docker
make docker-up                # Start containers
make docker-down              # Stop containers

# Help
make help                     # See all commands
```

See **[guides/MAKEFILE.md](./guides/MAKEFILE.md)** for complete reference.

---

## 🔍 Documentation Index

### By Role

**👨‍💻 Developers**
- [QUICK_START.md](./QUICK_START.md) - Get started
- [guides/DEVELOPMENT.md](./guides/DEVELOPMENT.md) - Development workflow
- [guides/MAKEFILE.md](./guides/MAKEFILE.md) - Commands
- [development/TROUBLESHOOTING.md](./development/TROUBLESHOOTING.md) - Help

**🔒 Security Team**
- [security/SECURITY.md](./security/SECURITY.md) - Best practices
- [security/SECURITY_IMPLEMENTATION.md](./security/SECURITY_IMPLEMENTATION.md) - Details
- [security/SECURITY_MAINTENANCE.md](./security/SECURITY_MAINTENANCE.md) - Operations

**🚀 DevOps / SRE**
- [deployment/DEPLOYMENT.md](./deployment/DEPLOYMENT.md) - Production setup
- [deployment/DOCKER.md](./deployment/DOCKER.md) - Docker config
- [deployment/PRODUCTION_CHECKLIST.md](./deployment/PRODUCTION_CHECKLIST.md) - Checklist

**🏗️ Architects**
- [architecture/ARCHITECTURE.md](./architecture/ARCHITECTURE.md) - System design
- [architecture/DATABASE_SCHEMA.md](./architecture/DATABASE_SCHEMA.md) - Data model
- [development/TECH_STACK.md](./development/TECH_STACK.md) - Technology stack

**📚 API Consumers**
- [api/API_REFERENCE.md](./api/API_REFERENCE.md) - Endpoints
- [api/AUTHENTICATION.md](./api/AUTHENTICATION.md) - Auth
- [api/ERROR_CODES.md](./api/ERROR_CODES.md) - Errors

---

## 📊 Documentation Statistics

| Category | Files | Lines | Topics |
|----------|-------|-------|--------|
| Guides | 4 | 800+ | Development, Poetry, Makefile, Database |
| Security | 4 | 2,200+ | Best practices, Implementation, Operations |
| Deployment | 3 | 1,200+ | Docker, Production, Checklist |
| Architecture | 3 | 1,000+ | System design, Database, API |
| API | 3 | 600+ | Reference, Auth, Errors |
| Development | 3 | 800+ | Phases, Stack, Troubleshooting |
| **Total** | **20+** | **6,600+** | **Complete coverage** |

---

## 🔗 Important Sections

### Setup & Installation
- [QUICK_START.md](./QUICK_START.md) - 5 minute setup
- [guides/POETRY.md](./guides/POETRY.md) - Dependency management
- [guides/DATABASE.md](./guides/DATABASE.md) - Database initialization

### Development
- [guides/DEVELOPMENT.md](./guides/DEVELOPMENT.md) - Full workflow
- [guides/MAKEFILE.md](./guides/MAKEFILE.md) - Available commands
- [development/TROUBLESHOOTING.md](./development/TROUBLESHOOTING.md) - Common issues

### Security
- [security/SECURITY.md](./security/SECURITY.md) - Practices
- [security/SECURITY_IMPLEMENTATION.md](./security/SECURITY_IMPLEMENTATION.md) - Technical
- [deployment/PRODUCTION_CHECKLIST.md](./deployment/PRODUCTION_CHECKLIST.md) - Pre-deploy

### Deployment
- [deployment/DEPLOYMENT.md](./deployment/DEPLOYMENT.md) - Full guide
- [deployment/DOCKER.md](./deployment/DOCKER.md) - Docker setup
- [deployment/PRODUCTION_CHECKLIST.md](./deployment/PRODUCTION_CHECKLIST.md) - Checklist

### API
- [api/API_REFERENCE.md](./api/API_REFERENCE.md) - Endpoints
- [api/AUTHENTICATION.md](./api/AUTHENTICATION.md) - Auth flows
- [api/ERROR_CODES.md](./api/ERROR_CODES.md) - Error handling

---

## 🚀 Common Workflows

### "I want to start developing"
```
1. Read: QUICK_START.md
2. Run: make install-dev
3. Run: make backend-dev (Terminal 1)
4. Run: make frontend-dev (Terminal 2)
5. Read: guides/DEVELOPMENT.md
```

### "I need to deploy to production"
```
1. Read: deployment/DEPLOYMENT.md
2. Review: deployment/PRODUCTION_CHECKLIST.md
3. Ensure: security/SECURITY.md compliance
4. Configure: deployment/DOCKER.md
5. Deploy: docker-compose up -d
```

### "I'm building an integration"
```
1. Read: api/API_REFERENCE.md
2. Auth: api/AUTHENTICATION.md
3. Errors: api/ERROR_CODES.md
4. Test: Using Swagger at /docs
```

### "I need to troubleshoot something"
```
1. Check: development/TROUBLESHOOTING.md
2. Check logs: make docker-logs
3. Re-read: guides/DEVELOPMENT.md
4. Ask: See SUPPORT section below
```

---

## ❓ Support

- **General Questions**: Read QUICK_START.md and guides/
- **Development Help**: See development/TROUBLESHOOTING.md
- **Security Concerns**: See security/SECURITY_MAINTENANCE.md for disclosure
- **Bug Reports**: Create GitHub Issue (security issues: security@yourdomain.com)

---

## 📌 Key Facts

- **Language**: Python 3.11+ (Backend), JavaScript (Frontend)
- **Framework**: FastAPI + Vue.js 3
- **Database**: SQLite
- **Security**: JWT, Bcrypt, CSRF, Rate Limiting, Audit Logging
- **Deployment**: Docker + Docker Compose
- **Development**: Poetry + Makefile

---

## 🔗 Quick Links

- **GitHub**: [Link to repo]
- **API Docs**: http://localhost:8000/docs (when running)
- **Issues**: [GitHub Issues]
- **Security**: security@yourdomain.com

---

**Last Updated**: June 2024
**Version**: 1.0.0
**Status**: ✅ Production Ready

---

## Navigation

[← Back to Main README](../README.md) | [Quick Start →](./QUICK_START.md)
