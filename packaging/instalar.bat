@echo off
REM Conveniencia de DESARROLLO: corre el dashboard desde un checkout del repo sin
REM construir el .exe (equivale a docs/dev-windows.md automatizado). NO es para el
REM cliente: el cliente usa el TapeteDashboard.exe del release.
REM Crea un entorno Python local e instala las dependencias fijadas.
setlocal
cd /d "%~dp0.."
where py >nul 2>nul && (set PY=py) || (set PY=python)
%PY% -m venv .venv || goto :err
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip || goto :err
pip install -r dashboard\requirements.txt || goto :err
> abrir_tapete.bat echo @echo off
>> abrir_tapete.bat echo cd /d "%%~dp0"
>> abrir_tapete.bat echo call .venv\Scripts\activate.bat
>> abrir_tapete.bat echo python dashboard\app.py --serial auto
echo.
echo Listo. Doble clic en abrir_tapete.bat para usar el tapete.
pause
exit /b 0
:err
echo ERROR durante la instalacion.
pause
exit /b 1
