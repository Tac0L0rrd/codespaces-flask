#!/usr/bin/env python3
"""
Script to create demo accounts and sample data for public portfolio showcase.
This preserves existing accounts while adding demo accounts with sample data.
"""

import sqlite3
import os
from datetime import datetime, date, timedelta

DATABASE = 'school.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_demo_accounts():
    """Create demo accounts for public showcase."""
    conn = get_db()
    cur = conn.cursor()
    
    # Create demo accounts with clear names
    demo_users = [
        ('demo_admin', 'demo123', 'admin'),
        ('demo_teacher', 'demo123', 'teacher'), 
        ('demo_student', 'demo123', 'student'),
    ]
    
    print("Creating demo accounts...")
    
    for username, password, role in demo_users:
        try:
            cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                       (username, password, role))
            print(f"Created {role}: {username}")
        except sqlite3.IntegrityError:
            print(f"Demo {role} account '{username}' already exists")
    
    conn.commit()
    return conn, cur

def create_sample_data(conn, cur):
    """Create sample subjects, enrollments, assignments, etc. for demo accounts."""
    
    # Get demo user IDs
    cur.execute("SELECT id, role FROM users WHERE username LIKE 'demo_%'")
    demo_users = {row['role']: row['id'] for row in cur.fetchall()}
    
    if not demo_users:
        print("No demo users found!")
        return
    
    demo_teacher_id = demo_users.get('teacher')
    demo_student_id = demo_users.get('student')
    
    # Create sample subjects
    subjects = [
        ('Mathematics', demo_teacher_id),
        ('English Literature', demo_teacher_id),
        ('Science', demo_teacher_id),
    ]
    
    print("Creating sample subjects...")
    subject_ids = []
    for subject_name, teacher_id in subjects:
        try:
            cur.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", 
                       (subject_name, teacher_id))
            subject_ids.append(cur.lastrowid)
            print(f"Created subject: {subject_name}")
        except sqlite3.IntegrityError:
            # Subject might already exist, get its ID
            cur.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
            existing = cur.fetchone()
            if existing:
                subject_ids.append(existing['id'])
    
    # Enroll demo student in all subjects
    print("Enrolling demo student in subjects...")
    for subject_id in subject_ids:
        try:
            cur.execute("INSERT INTO enrollments (user_id, subject_id) VALUES (?, ?)", 
                       (demo_student_id, subject_id))
            print(f"Enrolled demo student in subject ID {subject_id}")
        except sqlite3.IntegrityError:
            print(f"Demo student already enrolled in subject ID {subject_id}")
    
    # Create sample assignments
    print("Creating sample assignments...")
    assignments = [
        ('Algebra Quiz', 85.5, subject_ids[0] if subject_ids else 1, demo_student_id),
        ('Geometry Test', 92.0, subject_ids[0] if subject_ids else 1, demo_student_id),
        ('Essay: Shakespeare', 88.0, subject_ids[1] if len(subject_ids) > 1 else 1, demo_student_id),
        ('Book Report', 90.5, subject_ids[1] if len(subject_ids) > 1 else 1, demo_student_id),
        ('Lab Report', 87.0, subject_ids[2] if len(subject_ids) > 2 else 1, demo_student_id),
        ('Science Quiz', 93.5, subject_ids[2] if len(subject_ids) > 2 else 1, demo_student_id),
    ]
    
    for name, grade, subject_id, user_id in assignments:
        try:
            cur.execute("INSERT INTO assignments (name, grade, subject_id, user_id) VALUES (?, ?, ?, ?)", 
                       (name, grade, subject_id, user_id))
            print(f"Created assignment: {name} (Grade: {grade})")
        except sqlite3.IntegrityError:
            print(f"Assignment '{name}' might already exist")
    
    # Create sample schedule for demo student
    print("Creating sample schedule...")
    schedule_items = [
        (demo_student_id, subject_ids[0] if subject_ids else 1, 'Monday', 1),
        (demo_student_id, subject_ids[1] if len(subject_ids) > 1 else 1, 'Monday', 2),
        (demo_student_id, subject_ids[2] if len(subject_ids) > 2 else 1, 'Monday', 3),
        (demo_student_id, subject_ids[0] if subject_ids else 1, 'Wednesday', 1),
        (demo_student_id, subject_ids[1] if len(subject_ids) > 1 else 1, 'Wednesday', 2),
        (demo_student_id, subject_ids[2] if len(subject_ids) > 2 else 1, 'Friday', 1),
    ]
    
    for user_id, subject_id, day, period in schedule_items:
        try:
            cur.execute("INSERT INTO schedule (user_id, subject_id, day, period) VALUES (?, ?, ?, ?)", 
                       (user_id, subject_id, day, period))
            print(f"Added schedule: Subject {subject_id} on {day} period {period}")
        except sqlite3.IntegrityError:
            print(f"Schedule item already exists: Subject {subject_id} on {day} period {period}")
    
    # Create sample attendance data
    print("Creating sample attendance data...")
    
    # Generate attendance for past 2 weeks
    today = date.today()
    for i in range(14):
        attendance_date = (today - timedelta(days=i)).isoformat()
        for subject_id in subject_ids:
            # Demo student has good attendance (90% present)
            present = 1 if (i % 10) != 0 else 0  # Absent 1 day out of 10
            try:
                cur.execute("INSERT INTO attendance (user_id, subject_id, date, present) VALUES (?, ?, ?, ?)", 
                           (demo_student_id, subject_id, attendance_date, present))
            except sqlite3.IntegrityError:
                pass  # Attendance record might already exist
    
    print("Sample attendance data created")
    
    conn.commit()
    print("All sample data created successfully!")

def main():
    """Main function to create demo accounts and sample data."""
    print("Setting up demo accounts for public portfolio showcase...")
    print("This will preserve existing accounts and add demo accounts with sample data.")
    
    # Ensure database exists
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} does not exist. Please run the main app first to initialize it.")
        return
    
    # Create demo accounts
    conn, cur = create_demo_accounts()
    
    # Create sample data
    create_sample_data(conn, cur)
    
    # Display created accounts
    print("\n" + "="*50)
    print("DEMO ACCOUNTS CREATED:")
    print("="*50)
    
    cur.execute("SELECT username, role FROM users WHERE username LIKE 'demo_%'")
    demo_users = cur.fetchall()
    
    for user in demo_users:
        print(f"Username: {user['username']} | Password: demo123 | Role: {user['role']}")
    
    print("\nExisting accounts remain untouched:")
    cur.execute("SELECT username, role FROM users WHERE username NOT LIKE 'demo_%'")
    existing_users = cur.fetchall()
    
    for user in existing_users:
        print(f"Username: {user['username']} | Role: {user['role']}")
    
    conn.close()
    print("\nDemo setup complete! You can now showcase all three account types.")

if __name__ == "__main__":
    main()