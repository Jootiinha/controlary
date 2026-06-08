# Makefile Command Reference

Complete reference for all Makefile commands available in this project.

---

## Quick Reference

See the root `Makefile` file for the actual command definitions.

### Most Used Commands

```bash
make help                 # Show all commands
make install-dev         # Install everything with dev tools
make backend-dev         # Start backend server
make frontend-dev        # Start frontend server
make backend-test        # Run tests
make docker-up           # Start Docker containers
make docker-down         # Stop Docker containers
```

---

## All Commands

For the complete, up-to-date list of all available commands:

```bash
make help
```

Or read the root `Makefile` file in the project root directory.

---

## Command Categories

### Setup Commands
- `make install` - Install production dependencies
- `make install-dev` - Install with development tools
- `make status` - Show project status

### Backend Commands
- `make backend-install` - Install backend only
- `make backend-dev` - Start development server
- `make backend-test` - Run tests
- `make backend-test-cov` - Tests with coverage
- `make backend-lint` - Lint code
- `make backend-format` - Format code
- `make backend-typecheck` - Type check code

### Frontend Commands
- `make frontend-install` - Install frontend
- `make frontend-dev` - Start dev server
- `make frontend-build` - Build for production
- `make frontend-lint` - Lint code

### Docker Commands
- `make docker-build` - Build images
- `make docker-up` - Start containers
- `make docker-down` - Stop containers
- `make docker-logs` - View logs
- `make docker-restart` - Restart containers

### Database Commands
- `make db-migrate` - Apply migrations
- `make db-migrate-create` - Create new migration
- `make db-reset` - Reset database

### Cleanup Commands
- `make clean` - Remove build artifacts
- `make cleanup` - Full cleanup

---

## See Also

- **[docs/guides/DEVELOPMENT.md](./DEVELOPMENT.md)** - Full development guide
- **[Root Makefile](../../Makefile)** - Actual command definitions

For detailed descriptions of each command, run:
```bash
make help
```
