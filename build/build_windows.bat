@echo off
setlocal

cd /d "%~dp0\.."

echo ==^> Instalando dependencias (grupo build)
poetry install --with build --no-root
if errorlevel 1 goto :error

if not exist "assets\icon.ico" (
    echo ==^> Gerando icone placeholder
    poetry run python build\make_icon.py
    if errorlevel 1 goto :error
)

echo ==^> Rodando PyInstaller
poetry run pyinstaller build\controle-financeiro.spec --noconfirm
if errorlevel 1 goto :error

echo.
echo Build concluido.
echo Executavel gerado em: dist\ControleFinanceiro.exe
echo.
echo Para rodar: dist\ControleFinanceiro.exe
goto :eof

:error
echo.
echo FALHA no build.
exit /b 1
