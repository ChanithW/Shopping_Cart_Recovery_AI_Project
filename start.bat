@echo off
echo E-Commerce Platform Setup and Launch Script
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if MySQL is running
echo Checking MySQL connection...
mysql -u root -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Cannot connect to MySQL
    echo Please ensure:
    echo 1. MySQL Server is installed and running
    echo 2. Root user has access (or update credentials in app.py)
    echo 3. Run the database.sql script to create the database
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Create necessary directories
echo Creating required directories...
if not exist "static\images\products" mkdir static\images\products

REM Check if database exists
echo Checking database setup...
mysql -u root -e "USE ecommerce;" >nul 2>&1
if errorlevel 1 (
    echo Creating database...
    mysql -u root < database.sql
    if errorlevel 1 (
        echo ERROR: Failed to create database
        echo Please run: mysql -u root -p < database.sql
        pause
        exit /b 1
    )
    echo Database created successfully!
)

echo.
echo Setup complete! Starting the application...
echo.
echo The application will be available at: http://127.0.0.1:5000
echo.
echo Default admin login:
echo Email: admin@ecommerce.com
echo Password: admin123
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask application
python app.py

pause