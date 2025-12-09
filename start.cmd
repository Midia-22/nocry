@echo off
REM Ativa o ambiente virtual
call .\venv\Scripts\activate.bat

REM Executa o script Python
python .\app.py

REM Pausa apenas se quiser ver a saída antes de fechar
pause
