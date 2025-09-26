@echo off
REM EduBridge Advanced Features Setup Script for Windows
REM This script installs all dependencies for the advanced features

echo 🎓 EduBridge - Advanced Features Setup (Windows)
echo ==============================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.8+ first.
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please install pip first.
    pause
    exit /b 1
)

echo ✓ Python and pip found

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📈 Upgrading pip...
pip install --upgrade pip

REM Install core requirements
echo 📚 Installing core Flask requirements...
pip install Flask==2.3.3

REM Install advanced features dependencies
echo 🚀 Installing advanced features dependencies...

REM Real-time features
echo   → Installing WebSocket support...
pip install flask-socketio>=5.0.0 python-socketio>=5.0.0 eventlet>=0.33.0

REM Analytics and data processing
echo   → Installing analytics libraries...
pip install pandas>=2.0.0 numpy>=1.24.0 scikit-learn>=1.3.0 matplotlib>=3.7.0 seaborn>=0.12.0

REM Export functionality
echo   → Installing export libraries...
pip install reportlab>=4.0.0 openpyxl>=3.1.0

REM API development
echo   → Installing API libraries...
pip install pyjwt>=2.8.0 requests>=2.31.0

REM Multi-language support
echo   → Installing internationalization libraries...
pip install babel>=2.12.0

REM Development tools
echo   → Installing development tools...
pip install pytest>=7.4.0 pytest-flask>=1.2.0

echo.
echo ✅ Installation completed successfully!
echo.
echo 🎉 Advanced Features Available:
echo    📧 Email Notifications
echo    👨‍👩‍👧‍👦 Parent Portal
echo    🧠 Advanced Analytics with ML
echo    🌐 RESTful API
echo    ⚡ Real-time WebSocket Features
echo    📄 PDF/Excel Export
echo    🌍 Multi-language Support
echo    🔗 LMS Integration
echo.
echo 🚀 To start the application:
echo    venv\Scripts\activate
echo    python app.py
echo.
echo 🌐 The application will be available at: http://localhost:5000
echo.
echo 💡 Pro Tip: Check the README.md for detailed feature documentation!
echo.
pause