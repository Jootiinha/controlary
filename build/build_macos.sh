#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

echo "==> Instalando dependências (grupo build)"
poetry install --with build --no-root

if [[ ! -f "assets/icon.icns" ]]; then
    echo "==> Gerando ícone placeholder"
    poetry run python build/make_icon.py
fi

echo "==> Rodando PyInstaller"
poetry run pyinstaller build/controle-financeiro.spec --noconfirm

echo ""
echo "Build concluído."
echo "App gerado em: dist/ControleFinanceiro.app"
echo ""
echo "Para rodar:"
echo "  open dist/ControleFinanceiro.app"
echo ""
echo "Para arrastar para /Applications:"
echo "  cp -R dist/ControleFinanceiro.app /Applications/"
