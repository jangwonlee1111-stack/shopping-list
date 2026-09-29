@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 쇼핑 리스트 앱을 시작합니다. 브라우저가 자동으로 열립니다.
echo 종료하려면 이 창을 닫거나 Ctrl+C 를 누르세요.
python -m streamlit run app.py --browser.gatherUsageStats false
pause
