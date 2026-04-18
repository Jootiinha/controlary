.PHONY: help install install-all run icon build-mac build-win clean reset-db check

ifeq ($(OS),Windows_NT)
  PYTHON ?= py -3
else
  PYTHON ?= python3.13
endif

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
ifeq ($(OS),Windows_NT)
	@echo "O alvo build-mac deve ser executado no macOS (bash + PyInstaller macOS)." && exit 1
else
	bash build/build_macos.sh
endif

build-win: $(VENV_STAMP_BUILD)
ifeq ($(OS),Windows_NT)
	cmd.exe /c build\\build_windows.bat
else
	@echo "O alvo build-win deve ser executado no Windows (cmd + PyInstaller Windows)." && exit 1
endif

check:
	$(POETRY) check
	$(POETRY) run python -m compileall -q app main.py build/make_icon.py build/clean.py build/reset_db.py

reset-db:
	$(POETRY) run python build/reset_db.py

clean:
	$(POETRY) run python build/clean.py
