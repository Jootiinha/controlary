# -*- mode: python ; coding: utf-8 -*-
"""Spec do PyInstaller para gerar o app em macOS e Windows.

Uso:
    poetry run pyinstaller build/controle-financeiro.spec --noconfirm
"""
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent

if sys.platform == "darwin":
    icon = str(ROOT / "assets" / "icon.icns")
elif sys.platform.startswith("win"):
    icon = str(ROOT / "assets" / "icon.ico")
else:
    icon = str(ROOT / "assets" / "icon.png")

datas = [
    (str(ROOT / "app" / "database" / "schema.sql"), "app/database"),
    (str(ROOT / "app" / "ui" / "style.qss"), "app/ui"),
    (str(ROOT / "assets"), "assets"),
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ControleFinanceiro",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="ControleFinanceiro.app",
        icon=icon,
        bundle_identifier="com.joaomonteiro.controlefinanceiro",
        info_plist={
            "CFBundleName": "Controle Financeiro",
            "CFBundleDisplayName": "Controle Financeiro",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
