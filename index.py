"""
EduBridge Entry Point for Vercel Deployment
This file serves as the entry point for the Vercel serverless deployment.
"""

import os

# Set environment variable to indicate Vercel deployment
os.environ['VERCEL_DEPLOYMENT'] = '1'

from app import app

# For Vercel, we need to return the app directly
app = app
