.PHONY: help install install-all run icon build-mac build-win clean reset-db check

PYTHON ?= python3.13
POETRY ?= poetry

VENV_STAMP      := .venv/.installed
VENV_STAMP_BUILD := .venv/.installed-build

help:
	@echo "Controle Financeiro - alvos disponíveis:"
	@echo ""
	@echo "  make install     Instala dependências de runtime via Poetry"
	@echo "  make install-all Instala runtime + grupo build (PyInstaller)"
	@echo "  make run         Roda o app localmente (instala deps se necessário)"
	@echo "  make icon        Gera os ícones placeholder em assets/ (png/ico/icns)"
	@echo "  make build-mac   Empacota o app para macOS (.app em dist/)"
	@echo "  make build-win   Empacota o app para Windows (.exe em dist/)"
	@echo "  make check       Valida pyproject.toml e compila os .py"
	@echo "  make reset-db    Apaga o banco em ~/.controle-financeiro/app.db"
	@echo "  make clean       Remove build/, dist/, caches e .pyc"
	@echo ""

$(VENV_STAMP): pyproject.toml
	$(POETRY) install --no-root
	@mkdir -p .venv
	@touch $(VENV_STAMP)

$(VENV_STAMP_BUILD): pyproject.toml
	$(POETRY) install --with build --no-root
	@mkdir -p .venv
	@touch $(VENV_STAMP) $(VENV_STAMP_BUILD)

install: $(VENV_STAMP)

install-all: $(VENV_STAMP_BUILD)

run: $(VENV_STAMP)
	$(POETRY) run python main.py

icon: $(VENV_STAMP_BUILD)
	$(POETRY) run python build/make_icon.py

build-mac: $(VENV_STAMP_BUILD)
	bash build/build_macos.sh

build-win: $(VENV_STAMP_BUILD)
	cmd.exe /c build\\build_windows.bat

check:
	$(POETRY) check
	$(POETRY) run python -m compileall -q app main.py build/make_icon.py

reset-db:
	@rm -f $$HOME/.controle-financeiro/app.db
	@echo "Banco removido. Um novo será criado no próximo 'make run'."

clean:
	rm -rf build/__pycache__ dist build/build
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
