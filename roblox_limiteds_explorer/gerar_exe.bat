@echo off
cd /d "%~dp0"
if not exist .venv (
    echo Criando ambiente virtual...
    py -3 -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --windowed --name RobloxLimitedsExplorer ^
  --collect-all customtkinter ^
  --hidden-import plyer.platforms.win.notification ^
  --hidden-import keyring.backends.Windows ^
  main.py
echo.
echo Pronto! O programa esta em: dist\RobloxLimitedsExplorer\RobloxLimitedsExplorer.exe
pause
