#!/bin/bash
# Environment setup for EduBridge deployment

echo "🚀 Setting up EduBridge for deployment..."

# Install dependencies
pip install -r requirements.txt

# Create demo data
python create_demo_data.py

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

echo "✅ Setup complete! Run 'python app.py' to start the server."
