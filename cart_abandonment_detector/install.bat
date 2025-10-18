@echo off
REM Cart Abandonment Detector - Windows Installation Script
echo ============================================================
echo    Cart Abandonment Detector - Installation
echo ============================================================
echo.

echo Installing Python dependencies...
echo.

pip install google-generativeai
pip install scikit-learn
pip install numpy
pip install flask-mail


pause
