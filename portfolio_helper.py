#!/usr/bin/env python3
"""
Screenshot Generator and Deployment Helper for EduBridge
This script helps create screenshots and prepare for deployment
"""

import os
import subprocess
import time

def create_screenshots():
    """Create screenshots of the application for portfolio"""
    print("📸 Screenshot Guide for EduBridge Portfolio")
    print("=" * 50)
    
    urls_to_capture = [
        ("login", "http://localhost:5000/login", "Clean login interface"),
        ("admin_dashboard", "http://localhost:5000/admin", "Admin dashboard with management options"),
        ("teacher_dashboard", "http://localhost:5000/teacher_dashboard", "Teacher dashboard with navigation"),
        ("student_dashboard", "http://localhost:5000/student_dashboard", "Student dashboard with grades"),
        ("manage_users", "http://localhost:5000/manage_users", "User management interface"),
        ("enter_grades", "http://localhost:5000/enter_grades", "Grade entry system"),
        ("attendance", "http://localhost:5000/mark_attendance", "Attendance tracking"),
        ("reports", "http://localhost:5000/teacher_reports", "Academic reports"),
    ]
    
    print("🎯 Recommended Screenshots:")
    print()
    
    for filename, url, description in urls_to_capture:
        print(f"📱 {filename}.png")
        print(f"   URL: {url}")
        print(f"   Description: {description}")
        print(f"   Login as: {'admin/admin123' if 'admin' in url else 'mr_smith/teacher123' if 'teacher' in url else 'alice_cooper/student123'}")
        print()
    
    print("💡 Screenshot Tips:")
    print("- Use browser dev tools to simulate different devices")
    print("- Capture both desktop and mobile views")
    print("- Show the application with real data")
    print("- Include hover states and interactions")
    print()

def create_deployment_config():
    """Create deployment configuration files"""
    
    # Requirements.txt
    requirements = """Flask==2.3.3
sqlite3
hashlib
datetime
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements.strip())
    
    # Procfile for Heroku
    procfile = "web: python app.py"
    
    with open('Procfile', 'w') as f:
        f.write(procfile)
    
    # Railway deployment config
    railway_config = """{
  "build": {
    "builder": "heroku/buildpacks:20"
  },
  "deploy": {
    "startCommand": "python app.py",
    "restartPolicyType": "ON_FAILURE"
  }
}"""
    
    with open('railway.json', 'w') as f:
        f.write(railway_config)
    
    # Environment setup script
    env_setup = """#!/bin/bash
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
"""
    
    with open('setup.sh', 'w') as f:
        f.write(env_setup)
    
    os.chmod('setup.sh', 0o755)
    
    print("📦 Deployment files created:")
    print("- requirements.txt (Python dependencies)")
    print("- Procfile (Heroku deployment)")
    print("- railway.json (Railway deployment)")
    print("- setup.sh (Environment setup script)")
    print()

def generate_portfolio_assets():
    """Generate additional portfolio assets"""
    
    # Technology badges for README
    tech_badges = """
<!-- Technology Stack Badges -->
![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.3.3-orange.svg)
![SQLite](https://img.shields.io/badge/sqlite-3-lightgrey.svg)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
"""
    
    # Project metrics
    project_stats = """
## 📊 Project Statistics

- **Total Lines of Code**: ~1,200
- **Files**: 25+ HTML templates, 1 CSS file, 1 Python backend
- **Database Tables**: 7 interconnected tables
- **User Roles**: 3 distinct permission levels
- **Features**: 15+ core functionalities
- **Responsive Breakpoints**: 3 device categories
- **Test Coverage**: Demo data for all features
"""
    
    # Demo instructions
    demo_instructions = """
## 🎮 Live Demo Instructions

### Quick Start (Local)
```bash
# Clone and setup
git clone https://github.com/Tac0L0rrd/codespaces-flask.git
cd codespaces-flask
pip install flask
python create_demo_data.py
python app.py
```

### Demo Accounts
| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| Admin | admin | admin123 | Full system access |
| Teacher | mr_smith | teacher123 | Class management |
| Student | alice_cooper | student123 | Personal dashboard |

### Feature Tour
1. **Login** → Try different user roles
2. **Admin Dashboard** → User & subject management
3. **Teacher Tools** → Grades, attendance, reports
4. **Student View** → Personal academic progress
5. **Responsive Design** → Resize browser window
"""
    
    with open('DEMO_GUIDE.md', 'w') as f:
        f.write("# EduBridge Demo Guide\n")
        f.write(tech_badges)
        f.write(project_stats)
        f.write(demo_instructions)
    
    print("📋 Portfolio assets created:")
    print("- DEMO_GUIDE.md (Comprehensive demo instructions)")
    print()

def deployment_options():
    """Show deployment options"""
    
    print("🌐 Deployment Options for Portfolio")
    print("=" * 40)
    
    options = [
        {
            "platform": "Railway",
            "cost": "Free tier available",
            "setup": "Connect GitHub → Auto-deploy",
            "pros": "Easy setup, good for Flask apps",
            "url": "https://railway.app"
        },
        {
            "platform": "Render",
            "cost": "Free tier available", 
            "setup": "GitHub connection → Web service",
            "pros": "Simple, reliable, good docs",
            "url": "https://render.com"
        },
        {
            "platform": "PythonAnywhere",
            "cost": "Free tier with limitations",
            "setup": "Upload files → Configure web app",
            "pros": "Python-focused, beginner-friendly", 
            "url": "https://pythonanywhere.com"
        },
        {
            "platform": "Replit",
            "cost": "Free public repls",
            "setup": "Import from GitHub → Run",
            "pros": "Instant sharing, collaborative",
            "url": "https://replit.com"
        }
    ]
    
    for i, option in enumerate(options, 1):
        print(f"{i}. **{option['platform']}**")
        print(f"   Cost: {option['cost']}")
        print(f"   Setup: {option['setup']}")
        print(f"   Pros: {option['pros']}")
        print(f"   URL: {option['url']}")
        print()
    
    print("🔧 Recommended for Portfolio: Railway or Render")
    print("   → Both offer easy GitHub integration")
    print("   → Good uptime and performance")
    print("   → Professional appearance")
    print()

if __name__ == '__main__':
    print("🎯 EduBridge Portfolio Preparation Tool")
    print("=====================================")
    
    create_screenshots()
    create_deployment_config()
    generate_portfolio_assets()
    deployment_options()
    
    print("🎉 Portfolio preparation complete!")
    print()
    print("📋 Next Steps:")
    print("1. Take screenshots using the browser")
    print("2. Choose a deployment platform")
    print("3. Push to GitHub with new files")
    print("4. Deploy and test the live version")
    print("5. Add to your portfolio with live link")