#!/usr/bin/env python3
"""
Utility script to create parent accounts and link them to students
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def create_parent_account():
    """Create a parent account for testing"""
    database = os.path.join(os.path.dirname(__file__), 'school.db')
    conn = sqlite3.connect(database)
    cur = conn.cursor()
    
    # Create parent account
    parent_username = "parent_demo"
    parent_password = "demo123"
    parent_name = "Demo Parent"
    parent_email = "parent@demo.com"
    parent_phone = "123-456-7890"
    
    try:
        cur.execute("""
            INSERT INTO users (username, password, role, full_name, email, phone) 
            VALUES (?, ?, 'parent', ?, ?, ?)
        """, (parent_username, parent_password, parent_name, parent_email, parent_phone))
        
        parent_id = cur.lastrowid
        print(f"✓ Created parent account: {parent_username} (ID: {parent_id})")
        
        # Get a student to link to this parent
        cur.execute("SELECT id, username, full_name FROM users WHERE role = 'student' LIMIT 1")
        student = cur.fetchone()
        
        if student:
            student_id, student_username, student_name = student
            
            # Link parent to student
            cur.execute("""
                INSERT INTO parent_student_relationships (parent_id, student_id, relationship) 
                VALUES (?, ?, 'parent')
            """, (parent_id, student_id))
            
            print(f"✓ Linked parent to student: {student_name or student_username} (ID: {student_id})")
            
            # Create some sample notifications
            cur.execute("""
                INSERT INTO parent_notifications 
                (parent_id, student_id, notification_type, title, message) 
                VALUES (?, ?, 'grade', 'New Grade Posted', 'Your child received a new grade in Mathematics: 95%')
            """, (parent_id, student_id))
            
            cur.execute("""
                INSERT INTO parent_notifications 
                (parent_id, student_id, notification_type, title, message) 
                VALUES (?, ?, 'attendance', 'Attendance Alert', 'Your child was marked absent in Physics today.')
            """, (parent_id, student_id))
            
            print("✓ Created sample notifications")
            
        else:
            print("⚠ No students found to link to parent account")
        
        conn.commit()
        print("\n🎉 Parent account setup complete!")
        print(f"Login credentials:")
        print(f"Username: {parent_username}")
        print(f"Password: {parent_password}")
        print(f"URL: http://127.0.0.1:5000/login")
        
    except sqlite3.IntegrityError as e:
        print(f"❌ Error creating parent account: {e}")
        print("Parent account may already exist")
        
        # Try to get existing parent
        cur.execute("SELECT id FROM users WHERE username = ?", (parent_username,))
        existing = cur.fetchone()
        if existing:
            print(f"✓ Found existing parent account with username: {parent_username}")
            print(f"Password: {parent_password}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_parent_account()