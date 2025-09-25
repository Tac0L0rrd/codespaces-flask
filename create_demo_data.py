#!/usr/bin/env python3
"""
Demo Data Generator for EduBridge School Management System
This script populates the database with realistic demo data for showcasing
"""

import sqlite3
from datetime import datetime, timedelta
import random

def create_demo_data():
    """Create comprehensive demo data for the school management system"""

    # Connect to database
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()

    print("🚀 Creating demo data for EduBridge School Management System...")

    # Clear existing data
    print("📝 Clearing existing data...")
    tables = ['attendance', 'schedule', 'assignments', 'enrollments', 'subjects', 'users']
    for table in tables:
        try:
            cursor.execute(f'DELETE FROM {table}')
        except sqlite3.OperationalError:
            pass  # Table might not exist yet

    # Create demo users
    print("👥 Creating demo users...")

    # Admin user - Plain text password for demo
    cursor.execute('''
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
    ''', ('admin', 'admin123', 'admin'))

    # Teacher users
    teachers = [
        ('mr_smith', 'Mathematics Teacher'),
        ('ms_johnson', 'English Literature Teacher'),
        ('dr_brown', 'Science Teacher'),
        ('ms_davis', 'History Teacher'),
        ('mr_wilson', 'Physical Education Teacher')
    ]

    for username, description in teachers:
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', (username, 'teacher123', 'teacher'))

    # Student users
    students = [
        'alice_cooper', 'bob_johnson', 'charlie_brown', 'diana_prince',
        'edward_cullen', 'fiona_green', 'george_lucas', 'hannah_montana',
        'isaac_newton', 'julia_roberts', 'kevin_bacon', 'laura_croft',
        'michael_jordan', 'nancy_drew', 'oliver_twist', 'penny_lane'
    ]

    for student in students:
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', (student, 'student123', 'student'))

    # Create subjects
    print("📚 Creating subjects...")
    subjects_data = [
        ('Mathematics', 2),  # mr_smith
        ('English Literature', 3),  # ms_johnson
        ('Biology', 4),  # dr_brown
        ('Chemistry', 4),  # dr_brown
        ('World History', 5),  # ms_davis
        ('Physical Education', 6)  # mr_wilson
    ]

    for subject_name, teacher_id in subjects_data:
        cursor.execute('''
            INSERT INTO subjects (name, teacher_id)
            VALUES (?, ?)
        ''', (subject_name, teacher_id))

    # Enroll students in subjects (realistic enrollment)
    print("📋 Enrolling students in subjects...")
    for student_id in range(7, 23):  # Student IDs 7-22
        # Each student enrolled in 4-6 subjects randomly
        subject_ids = random.sample(range(1, 7), random.randint(4, 6))
        for subject_id in subject_ids:
            cursor.execute('''
                INSERT INTO enrollments (user_id, subject_id)
                VALUES (?, ?)
            ''', (student_id, subject_id))

    # Create assignments with grades for each enrolled student
    print("📝 Creating assignments and grades...")
    assignments_data = [
        (1, 'Algebra Quiz 1'), (1, 'Geometry Test'), (1, 'Calculus Project'),
        (2, 'Essay: Shakespeare'), (2, 'Poetry Analysis'), (2, 'Book Report'),
        (3, 'Cell Biology Lab'), (3, 'Genetics Quiz'), (3, 'Evolution Essay'),
        (4, 'Chemical Reactions Lab'), (4, 'Periodic Table Quiz'),
        (5, 'World War I Essay'), (5, 'Ancient Civilizations Project'),
        (6, 'Fitness Test'), (6, 'Team Sports Evaluation')
    ]

    for student_id in range(7, 23):
        # Get subjects this student is enrolled in
        cursor.execute('''
            SELECT subject_id FROM enrollments WHERE user_id = ?
        ''', (student_id,))
        enrolled_subjects = [row[0] for row in cursor.fetchall()]

        for subject_id, assignment_name in assignments_data:
            if subject_id in enrolled_subjects:
                # Generate realistic grade (bell curve distribution)
                grade = max(65, min(100, int(random.gauss(85, 10))))
                cursor.execute('''
                    INSERT INTO assignments (name, grade, subject_id, user_id)
                    VALUES (?, ?, ?, ?)
                ''', (assignment_name, grade, subject_id, student_id))

    # Create attendance records (last 30 days)
    print("📅 Creating attendance records...")
    for days_back in range(30):
        date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        for student_id in range(7, 23):
            cursor.execute('''
                SELECT subject_id FROM enrollments WHERE user_id = ?
            ''', (student_id,))
            enrolled_subjects = [row[0] for row in cursor.fetchall()]

            for subject_id in enrolled_subjects:
                # 92% attendance rate (realistic)
                present = 1 if random.random() < 0.92 else 0
                cursor.execute('''
                    INSERT INTO attendance (user_id, subject_id, date, present)
                    VALUES (?, ?, ?, ?)
                ''', (student_id, subject_id, date, present))

    # Create schedule for each enrolled student
    print("⏰ Creating class schedule...")
    schedule_assignments = [
        (1, 'Monday', 1), (1, 'Wednesday', 1), (1, 'Friday', 1),
        (2, 'Monday', 2), (2, 'Tuesday', 2), (2, 'Thursday', 2),
        (3, 'Tuesday', 3), (3, 'Thursday', 3),
        (4, 'Monday', 4), (4, 'Wednesday', 4),
        (5, 'Tuesday', 1), (5, 'Friday', 2),
        (6, 'Wednesday', 5), (6, 'Friday', 5)
    ]

    for student_id in range(7, 23):
        cursor.execute('''
            SELECT subject_id FROM enrollments WHERE user_id = ?
        ''', (student_id,))
        enrolled_subjects = [row[0] for row in cursor.fetchall()]

        for subject_id, day, period in schedule_assignments:
            if subject_id in enrolled_subjects:
                cursor.execute('''
                    INSERT INTO schedule (user_id, subject_id, day, period)
                    VALUES (?, ?, ?, ?)
                ''', (student_id, subject_id, day, period))

    # Commit changes
    conn.commit()
    conn.close()

    print("✅ Demo data creation complete!")
    print("\n🔑 Demo Login Credentials:")
    print("👨‍💼 Admin: username='admin', password='admin123'")
    print("👩‍🏫 Teacher: username='mr_smith', password='teacher123'")
    print("👨‍🎓 Student: username='alice_cooper', password='student123'")
    print("\n🌐 Start the application with: python app.py")

if __name__ == '__main__':
    create_demo_data()
