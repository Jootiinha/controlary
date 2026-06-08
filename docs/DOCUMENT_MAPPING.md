# Documentation Mapping

This document shows where all documentation files are located after reorganization.

---

## Root Level Documents

| File | Location | Purpose |
|------|----------|---------|
| `README.md` | Root | Project overview & features |
| `.env.example` | Root | Environment template |
| `Makefile` | Root | Development commands |
| `pyproject.toml` | `backend/` | Python dependencies |
| `package.json` | `frontend/` | Node dependencies |

---

## Complete Documentation Structure

### In `docs/`

#### Main Index & Navigation
```
docs/
├── README.md                    # Main documentation index (START HERE)
├── QUICK_START.md              # 5-minute setup guide
└── DOCUMENT_MAPPING.md         # This file
```

#### Guides (How-to & Workflows)
```
docs/guides/
├── DEVELOPMENT.md              # Development workflow
├── MAKEFILE.md                 # Command reference
├── MAKEFILE_SETUP.md           # Setup guide
└── (POETRY.md & DATABASE.md coming soon)
```

#### Security Documentation
```
docs/security/
├── SECURITY.md                 # Best practices
├── SECURITY_IMPLEMENTATION.md  # Technical details
├── SECURITY_MAINTENANCE.md     # Operations & scanning
└── SECURITY_INDEX.md           # Security features navigation
```

#### Deployment & Production
```
docs/deployment/
├── DEPLOYMENT.md               # Full deployment guide
└── (DOCKER.md & PRODUCTION_CHECKLIST.md coming soon)
```

#### Development & Implementation Details
```
docs/development/
├── IMPLEMENTATION_NOTES.md     # Architecture decisions
├── IMPLEMENTATION_STATUS.md    # Project status
├── PHASE_2_SUMMARY.md         # Phase 2 completion
├── PHASE_8_COMPLETION.md      # Phase 8 (Security) completion
├── EXECUTION_SUMMARY.md       # Execution details
└── FILES_CREATED.md           # Files created in implementation
```

#### Architecture (Coming Soon)
```
docs/architecture/
├── ARCHITECTURE.md             # System architecture
├── DATABASE_SCHEMA.md          # Database design
└── API_DESIGN.md              # API design patterns
```

#### API Documentation (Coming Soon)
```
docs/api/
├── API_REFERENCE.md            # Endpoint reference
├── AUTHENTICATION.md           # Auth flows
└── ERROR_CODES.md             # Error handling
```

---

## New Documentation Structure

### docs/ (Newly Created)

```
docs/
├── README.md                          # Main docs index
├── QUICK_START.md                     # 5-minute setup
├── DOCUMENT_MAPPING.md               # This file
├── guides/
│   ├── DEVELOPMENT.md                # Development workflow
│   ├── MAKEFILE.md                   # Command reference
│   ├── POETRY.md                     # Package management
│   └── DATABASE.md                   # Database guide
├── security/                         # (Links to root files)
│   ├── SECURITY.md
│   ├── SECURITY_IMPLEMENTATION.md
│   ├── SECURITY_MAINTENANCE.md
│   └── SECURITY_INDEX.md
├── deployment/                       # (Links to root files)
│   ├── DEPLOYMENT.md
│   ├── DOCKER.md
│   └── PRODUCTION_CHECKLIST.md
├── architecture/
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   └── API_DESIGN.md
├── api/
│   ├── API_REFERENCE.md
│   ├── AUTHENTICATION.md
│   └── ERROR_CODES.md
└── development/
    ├── PHASES.md
    ├── TECH_STACK.md
    └── TROUBLESHOOTING.md
```

---

## How to Navigate

### For Quick Setup
1. **Start**: docs/QUICK_START.md
2. **Then**: docs/guides/DEVELOPMENT.md
3. **Commands**: docs/guides/MAKEFILE.md

### For Development
1. **Workflow**: docs/guides/DEVELOPMENT.md
2. **Database**: docs/guides/DATABASE.md
3. **Troubleshooting**: docs/development/TROUBLESHOOTING.md

### For Security
1. **Practices**: docs/security/SECURITY.md
2. **Implementation**: docs/security/SECURITY_IMPLEMENTATION.md
3. **Maintenance**: docs/security/SECURITY_MAINTENANCE.md
4. **Index**: docs/security/SECURITY_INDEX.md

### For Deployment
1. **Guide**: docs/deployment/DEPLOYMENT.md
2. **Docker**: docs/deployment/DOCKER.md
3. **Checklist**: docs/deployment/PRODUCTION_CHECKLIST.md

### For Architecture
1. **Overview**: docs/architecture/ARCHITECTURE.md
2. **Database**: docs/architecture/DATABASE_SCHEMA.md
3. **API**: docs/architecture/API_DESIGN.md

---

## File Organization Strategy

### Current State
- Main docs in project **root**
- Well-organized but not centralized

### New Structure
- All docs in **docs/** folder
- Organized by topic
- Clear navigation
- Symlinks/references where needed

### Benefits
✅ Cleaner project root (only config files + README)
✅ Organized by topic (guides, security, deployment, etc.)
✅ Easy to find information
✅ Better for documentation sites (MkDocs, Sphinx, etc.)
✅ Easier to maintain

---

## Migration Checklist

- [x] Created `docs/` folder structure
- [x] Created `docs/README.md` (main index)
- [x] Created `docs/QUICK_START.md` (5-minute setup)
- [x] Created `docs/guides/DEVELOPMENT.md` (updated from root)
- [x] Created `docs/guides/MAKEFILE.md` (command reference)
- [ ] Move/copy `DEVELOPMENT.md` from root to `docs/guides/`
- [ ] Move/copy `IMPLEMENTATION_NOTES.md` → `docs/development/ARCHITECTURE.md`
- [ ] Move/copy `DEPLOYMENT.md` → `docs/deployment/`
- [ ] Create symlinks or update root README with links
- [ ] Update main README.md to point to docs/

---

## How to Use This Mapping

1. **To find something**: Use this mapping table
2. **To add documentation**: Put in appropriate `docs/` subfolder
3. **To navigate**: Use `docs/README.md` as entry point
4. **From command line**: `docs/guides/MAKEFILE.md` for commands

---

## Future Improvements

- [ ] Generate documentation site with MkDocs
- [ ] Create PDF versions of guides
- [ ] Add video tutorials
- [ ] Create API documentation from OpenAPI spec
- [ ] Add troubleshooting flowcharts

---

**Last Updated**: June 2024
**Version**: 1.0.0

See also: [docs/README.md](./README.md) for full documentation index.
