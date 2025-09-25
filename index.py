"""
EduBridge Entry Point for Vercel Deployment
This file serves as the entry point for the Vercel serverless deployment.
"""

from app import app

if __name__ == "__main__":
    app.run()
