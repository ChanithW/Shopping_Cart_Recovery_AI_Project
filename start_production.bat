@echo off
echo ================================================================
echo   E-Commerce Platform - Production Server
echo ================================================================
echo.

REM Navigate to the correct directory
cd /d "C:\AI_Agent_LLM&NLP\Ecom_platform\ecom"

REM Activate virtual environment
call venv\Scripts\activate

echo Starting production server...
echo.
echo ================================================================
echo   Your E-Commerce Website is now running in PRODUCTION MODE
echo ================================================================
echo.
echo   🌐 Website URL: http://localhost:8080
echo   🌐 Network URL: http://0.0.0.0:8080
echo.
echo   📊 Server: Waitress (Production WSGI Server)
echo   🔒 Debug Mode: DISABLED
echo   ⚡ Performance: Optimized for production
echo.
echo   🔑 Admin Login:
echo   📧 Email: admin@ecommerce.com
echo   🔐 Password: admin123
echo.
echo   Press Ctrl+C to stop the server
echo ================================================================
echo.

REM Start the production server using Waitress
waitress-serve --host=0.0.0.0 --port=8080 --threads=4 wsgi:application

pause