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

echo.
echo ============================================================
echo    Installation Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Add GEMINI_API_KEY to your .env file
echo    Get it from: https://makersuite.google.com/app/apikey
echo.
echo 2. Run tests:
echo    python test_detector.py
echo.
echo 3. Start the detector:
echo    python run_detector.py
echo.
echo See QUICKSTART.md for full instructions.
echo.
pause
