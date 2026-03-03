@echo off
echo Starting ValueCompass AI Stock Screener...
cd /d "d:\Trading\value"
call venv\Scripts\activate.bat
streamlit run app.py
pause
