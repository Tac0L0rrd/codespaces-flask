"""
Email Service Module
Handles all email notifications for the education management system
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sqlite3
import os
from typing import List, Dict, Optional

class EmailService:
    def __init__(self, smtp_server: str = "smtp.gmail.com", 
                 smtp_port: int = 587, 
                 username: str = "", 
                 password: str = ""):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.database = os.path.join(os.path.dirname(__file__), 'school.db')
    
    def get_user_email_preferences(self, user_id: int) -> Dict:
        """Get user email notification preferences"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Check if user_settings table has email column
        cur.execute("PRAGMA table_info(user_settings)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'email' not in columns:
            # Add email column if it doesn't exist
            cur.execute("ALTER TABLE user_settings ADD COLUMN email TEXT")
            conn.commit()
        
        cur.execute("""
            SELECT us.*, u.username 
            FROM user_settings us 
            JOIN users u ON us.user_id = u.id 
            WHERE us.user_id = ?
        """, (user_id,))
        
        result = cur.fetchone()
        conn.close()
        
        if result:
            return dict(result)
        else:
            # Create default settings for user
            return self.create_default_user_settings(user_id)
    
    def create_default_user_settings(self, user_id: int) -> Dict:
        """Create default email settings for a user"""
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT OR REPLACE INTO user_settings 
            (user_id, email_notifications, assignment_reminders, attendance_reminders, email) 
            VALUES (?, 1, 1, 1, ?)
        """, (user_id, f"user{user_id}@school.edu"))
        
        conn.commit()
        conn.close()
        
        return {
            'user_id': user_id,
            'email_notifications': True,
            'assignment_reminders': True,
            'attendance_reminders': True,
            'email': f"user{user_id}@school.edu"
        }
    
    def send_email(self, to_email: str, subject: str, body: str, html_body: str = None) -> bool:
        """Send an email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send the email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    def send_grade_notification(self, student_id: int, assignment_name: str, 
                               grade: float, subject_name: str):
        """Send grade notification to student and parents"""
        preferences = self.get_user_email_preferences(student_id)
        
        if not preferences.get('email_notifications'):
            return
        
        subject = f"New Grade Posted: {assignment_name}"
        body = f"""
Dear Student,

A new grade has been posted for your assignment:

Assignment: {assignment_name}
Subject: {subject_name}
Grade: {grade}%
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Please log in to your student dashboard to view more details.

Best regards,
EduBridge Team
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">New Grade Posted</h2>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #34495e; margin-top: 0;">Assignment Details</h3>
            <p><strong>Assignment:</strong> {assignment_name}</p>
            <p><strong>Subject:</strong> {subject_name}</p>
            <p><strong>Grade:</strong> <span style="color: #27ae60; font-size: 18px; font-weight: bold;">{grade}%</span></p>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        
        <p>Please log in to your student dashboard to view more details and track your progress.</p>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
            <p style="color: #7f8c8d; font-size: 12px;">
                Best regards,<br>
                EduBridge Team
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(preferences['email'], subject, body, html_body)
    
    def send_assignment_notification(self, student_ids: List[int], assignment_name: str, 
                                   due_date: str, subject_name: str):
        """Send new assignment notification to students"""
        for student_id in student_ids:
            preferences = self.get_user_email_preferences(student_id)
            
            if not preferences.get('assignment_reminders'):
                continue
            
            subject = f"New Assignment: {assignment_name}"
            body = f"""
Dear Student,

A new assignment has been posted:

Assignment: {assignment_name}
Subject: {subject_name}
Due Date: {due_date}
Posted: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Please log in to your student dashboard to view assignment details.

Best regards,
EduBridge Team
            """
            
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">New Assignment Posted</h2>
        
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3;">
            <h3 style="color: #1976d2; margin-top: 0;">Assignment Details</h3>
            <p><strong>Assignment:</strong> {assignment_name}</p>
            <p><strong>Subject:</strong> {subject_name}</p>
            <p><strong>Due Date:</strong> <span style="color: #f44336; font-weight: bold;">{due_date}</span></p>
            <p><strong>Posted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        
        <p>Please log in to your student dashboard to view assignment details and submit your work on time.</p>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
            <p style="color: #7f8c8d; font-size: 12px;">
                Best regards,<br>
                EduBridge Team
            </p>
        </div>
    </div>
</body>
</html>
            """
            
            self.send_email(preferences['email'], subject, body, html_body)
    
    def send_attendance_reminder(self, teacher_id: int, subject_name: str):
        """Send attendance reminder to teacher"""
        preferences = self.get_user_email_preferences(teacher_id)
        
        if not preferences.get('attendance_reminders'):
            return
        
        subject = f"Attendance Reminder: {subject_name}"
        body = f"""
Dear Teacher,

This is a reminder to mark attendance for your class:

Subject: {subject_name}
Date: {datetime.now().strftime('%Y-%m-%d')}

Please log in to your teacher dashboard to mark attendance.

Best regards,
EduBridge Team
        """
        
        return self.send_email(preferences['email'], subject, body)

# Global email service instance
email_service = EmailService()

def register_email_routes(app):
    """Register email service with Flask app"""
    # Email service is used internally, no routes needed for now
    # Could add admin routes for email management in the future
    pass