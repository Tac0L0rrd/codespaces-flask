#!/bin/bash

# EduBridge Advanced Features Setup Script
# This script installs all dependencies for the advanced features

echo "🎓 EduBridge - Advanced Features Setup"
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo "✓ Python and pip found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Install core requirements
echo "📚 Installing core Flask requirements..."
pip install Flask==2.3.3

# Install advanced features dependencies
echo "🚀 Installing advanced features dependencies..."

# Real-time features
echo "  → Installing WebSocket support..."
pip install flask-socketio>=5.0.0 python-socketio>=5.0.0 eventlet>=0.33.0

# Analytics and data processing
echo "  → Installing analytics libraries..."
pip install pandas>=2.0.0 numpy>=1.24.0 scikit-learn>=1.3.0 matplotlib>=3.7.0 seaborn>=0.12.0

# Export functionality
echo "  → Installing export libraries..."
pip install reportlab>=4.0.0 openpyxl>=3.1.0

# API development
echo "  → Installing API libraries..."
pip install pyjwt>=2.8.0 requests>=2.31.0

# Multi-language support
echo "  → Installing internationalization libraries..."
pip install babel>=2.12.0

# Development tools
echo "  → Installing development tools..."
pip install pytest>=7.4.0 pytest-flask>=1.2.0

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🎉 Advanced Features Available:"
echo "   📧 Email Notifications"
echo "   👨‍👩‍👧‍👦 Parent Portal"  
echo "   🧠 Advanced Analytics with ML"
echo "   🌐 RESTful API"
echo "   ⚡ Real-time WebSocket Features"
echo "   📄 PDF/Excel Export"
echo "   🌍 Multi-language Support"
echo "   🔗 LMS Integration"
echo ""
echo "🚀 To start the application:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🌐 The application will be available at: http://localhost:5000"
echo ""
echo "💡 Pro Tip: Check the README.md for detailed feature documentation!"