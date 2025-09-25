"""
EduBridge - School Management System
A comprehensive Flask-based web application for managing educational institutions.
Features: User management, course enrollment, assignment tracking, attendance, and reporting.
"""

from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os
from datetime import datetime, date

# Application Configuration
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this in production
DATABASE = os.path.join(os.path.dirname(__file__), 'school.db')

# --- Helper Functions ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Grading System Functions ---
def get_grading_scale():
    """Get the current grading scale from settings"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT setting_value FROM system_settings WHERE setting_name = 'grading_scale'")
    result = cur.fetchone()
    conn.close()
    return result['setting_value'] if result else 'percentage'

def get_passing_grade():
    """Get the current passing grade from settings"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT setting_value FROM system_settings WHERE setting_name = 'passing_grade'")
    result = cur.fetchone()
    conn.close()
    return float(result['setting_value']) if result else 60.0

def percentage_to_letter(percentage):
    """Convert percentage to letter grade"""
    if percentage >= 97: return 'A+'
    elif percentage >= 93: return 'A'
    elif percentage >= 90: return 'A-'
    elif percentage >= 87: return 'B+'
    elif percentage >= 83: return 'B'
    elif percentage >= 80: return 'B-'
    elif percentage >= 77: return 'C+'
    elif percentage >= 73: return 'C'
    elif percentage >= 70: return 'C-'
    elif percentage >= 67: return 'D+'
    elif percentage >= 63: return 'D'
    elif percentage >= 60: return 'D-'
    else: return 'F'

def letter_to_percentage(letter):
    """Convert letter grade to percentage (midpoint)"""
    grade_map = {
        'A+': 98.5, 'A': 95, 'A-': 91.5,
        'B+': 88.5, 'B': 85, 'B-': 81.5,
        'C+': 78.5, 'C': 75, 'C-': 71.5,
        'D+': 68.5, 'D': 65, 'D-': 61.5,
        'F': 50
    }
    return grade_map.get(letter, 0)

def percentage_to_gpa(percentage):
    """Convert percentage to 4.0 GPA scale"""
    if percentage >= 97: return 4.0
    elif percentage >= 93: return 4.0
    elif percentage >= 90: return 3.7
    elif percentage >= 87: return 3.3
    elif percentage >= 83: return 3.0
    elif percentage >= 80: return 2.7
    elif percentage >= 77: return 2.3
    elif percentage >= 73: return 2.0
    elif percentage >= 70: return 1.7
    elif percentage >= 67: return 1.3
    elif percentage >= 65: return 1.0
    elif percentage >= 60: return 0.7
    else: return 0.0

def gpa_to_percentage(gpa):
    """Convert GPA to percentage (approximate)"""
    if gpa >= 4.0: return 95
    elif gpa >= 3.7: return 90
    elif gpa >= 3.3: return 87
    elif gpa >= 3.0: return 83
    elif gpa >= 2.7: return 80
    elif gpa >= 2.3: return 77
    elif gpa >= 2.0: return 73
    elif gpa >= 1.7: return 70
    elif gpa >= 1.3: return 67
    elif gpa >= 1.0: return 65
    elif gpa >= 0.7: return 60
    else: return 50

def format_grade(grade, target_scale=None):
    """Format grade according to the specified or current grading scale"""
    if grade is None or grade == '':
        return 'N/A'
    
    try:
        # Convert grade to float if it's not already
        if isinstance(grade, str):
            grade = float(grade)
    except (ValueError, TypeError):
        return 'N/A'
    
    # Get target scale (use current system setting if not specified)
    if target_scale is None:
        target_scale = get_grading_scale()
    
    # Assume input is always in percentage, convert to target scale
    if target_scale == 'letter':
        return percentage_to_letter(grade)
    elif target_scale == 'gpa':
        return f"{percentage_to_gpa(grade):.1f}"
    else:  # percentage
        return f"{grade:.1f}%"

def is_passing_grade(grade):
    """Check if a grade is passing based on current settings"""
    if grade is None:
        return False
    
    try:
        grade_value = float(grade)
    except (ValueError, TypeError):
        return False
    
    passing_threshold = get_passing_grade()
    return grade_value >= passing_threshold

    # Create tables if they don't exist
    cur = conn.cursor()

    # Users table
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')

    # Subjects table
    cur.execute('''CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY,
        name TEXT,
        teacher_id INTEGER REFERENCES users(id)
    )''')

    # Assignments table
    cur.execute('''CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY,
        name TEXT,
        grade REAL,
        subject_id INTEGER,
        user_id INTEGER
    )''')

    # Enrollments table
    cur.execute('''CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        subject_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (subject_id) REFERENCES subjects(id),
        UNIQUE(user_id, subject_id)
    )''')

    # Attendance table
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        subject_id INTEGER,
        date TEXT,
        present INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )''')

    # User settings table
    cur.execute('''CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        email_notifications BOOLEAN DEFAULT 0,
        assignment_reminders BOOLEAN DEFAULT 0,
        attendance_reminders BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    conn.commit()
    return conn

def is_admin():
    return session.get('role') == 'admin'

def is_student():
    return session.get('role') == 'student'

def is_teacher():
    return session.get('role') == 'teacher'

def init_demo_data():
    """Initialize demo data for Vercel deployment"""
    conn = get_db()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # Data already exists

    print("Initializing demo data for Vercel...")

    # Create admin users
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', 'admin123', 'admin'))  # Demo admin
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('Admin', '2009', 'admin'))      # Real admin

    # Teachers
    teachers = [
        ('mr_smith', 'Mathematics Teacher'),
        ('ms_johnson', 'English Literature Teacher'),
        ('dr_brown', 'Science Teacher'),
        ('ms_davis', 'History Teacher'),
        ('mr_wilson', 'Physical Education Teacher')
    ]

    for username, _ in teachers:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, 'teacher123', 'teacher'))

    # Students
    students = [
        'alice_cooper', 'bob_johnson', 'charlie_brown', 'diana_prince',
        'edward_cullen', 'fiona_green', 'george_lucas', 'hannah_montana',
        'isaac_newton', 'julia_roberts', 'kevin_bacon', 'laura_croft'
    ]

    for student in students:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (student, 'student123', 'student'))

    # Create subjects
    subjects_data = [
        ('Mathematics', 2),  # mr_smith
        ('English Literature', 3),  # ms_johnson
        ('Science', 4),  # dr_brown
        ('History', 5),  # ms_davis
        ('Physical Education', 6)  # mr_wilson
    ]

    for subject_name, teacher_id in subjects_data:
        cursor.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", (subject_name, teacher_id))

    # Enroll students in subjects (first 8 students in all subjects)
    for subject_id in range(1, 6):  # 5 subjects
        for student_id in range(7, 15):  # Students 7-14 (alice_cooper onwards)
            cursor.execute("INSERT INTO enrollments (user_id, subject_id) VALUES (?, ?)", (student_id, subject_id))

    # Create sample assignments with grades
    import random
    assignment_names = [
        'Midterm Exam', 'Final Project', 'Quiz 1', 'Homework Assignment',
        'Lab Report', 'Essay Assignment', 'Group Project', 'Presentation'
    ]

    for subject_id in range(1, 6):
        for i, assignment_name in enumerate(assignment_names[:4]):  # 4 assignments per subject
            for student_id in range(7, 15):  # Students with enrollments
                grade = random.randint(70, 98)
                cursor.execute("""
                    INSERT INTO assignments (name, subject_id, user_id, grade, date_assigned)
                    VALUES (?, ?, ?, ?, ?)
                """, (f"{assignment_name}", subject_id, student_id, grade, '2024-09-01'))

    conn.commit()
    conn.close()
    print("Demo data initialized successfully!")

# --- Home Route ---
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if is_admin():
        return redirect(url_for('admin_dashboard'))
    elif is_teacher():
        return redirect(url_for('teacher_dashboard'))
    elif is_student():
        return redirect(url_for('student_dashboard'))
    else:
        return redirect(url_for('login'))

# --- Login / Signup / Logout ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw))
        user_row = cur.fetchone()
        if user_row:
            session.clear()
            session['user_id'] = user_row['id']
            session['role'] = user_row['role']
            session['username'] = user_row['username']
            return redirect(url_for(f"{user_row['role']}_dashboard"))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        role = 'student'
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (user, pw, role))
        conn.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Admin Dashboard ---
@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/system_analytics')
def system_analytics():
    if not is_admin():
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get current grading scale
    grading_scale = get_grading_scale()
    
    # Get overall statistics
    cur.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    total_students = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM users WHERE role='teacher'")
    total_teachers = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM assignments")
    total_assignments = cur.fetchone()[0]
    
    # Get average grades
    cur.execute("SELECT AVG(grade) FROM assignments WHERE grade IS NOT NULL")
    avg_grade = cur.fetchone()[0] or 0
    
    # Get attendance rate
    cur.execute("SELECT AVG(present) FROM attendance")
    attendance_rate = (cur.fetchone()[0] or 0) * 100
    
    # Get subject performance with teacher info and student counts
    cur.execute("""
        SELECT s.name, 
               u.username as teacher_name, 
               AVG(a.grade) as avg_grade, 
               COUNT(DISTINCT a.id) as assignment_count,
               COUNT(DISTINCT e.user_id) as student_count
        FROM subjects s
        LEFT JOIN users u ON s.teacher_id = u.id
        LEFT JOIN assignments a ON s.id = a.subject_id AND a.grade IS NOT NULL
        LEFT JOIN enrollments e ON s.id = e.subject_id
        GROUP BY s.id, s.name, u.username
        ORDER BY avg_grade DESC
    """)
    subject_performance = cur.fetchall()
    
    conn.close()
    
    return render_template('system_analytics.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_subjects=total_subjects,
                         total_assignments=total_assignments,
                         avg_grade=round(avg_grade, 1),
                         formatted_avg_grade=format_grade(avg_grade, grading_scale),
                         attendance_rate=round(attendance_rate, 1),
                         subject_performance=subject_performance,
                         grading_scale=grading_scale,
                         format_grade=format_grade)

@app.route('/admin_settings', methods=['GET', 'POST'])
def admin_settings():
    if not is_admin():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Extract form data
            school_name = request.form.get('school_name', 'EduBridge Academy')
            academic_year = request.form.get('academic_year', '2024-2025')
            email_notifications = 1 if request.form.get('email_notifications') else 0
            sms_notifications = 1 if request.form.get('sms_notifications') else 0
            grading_scale = request.form.get('grading_scale', 'percentage')
            passing_grade = request.form.get('passing_grade', '60')
            session_timeout = request.form.get('session_timeout', '60')
            force_password_change = 1 if request.form.get('force_password_change') else 0
            
            # Save each setting to the database
            settings = [
                ('school_name', school_name),
                ('academic_year', academic_year),
                ('email_notifications', str(email_notifications)),
                ('sms_notifications', str(sms_notifications)),
                ('grading_scale', grading_scale),
                ('passing_grade', passing_grade),
                ('session_timeout', session_timeout),
                ('force_password_change', str(force_password_change))
            ]
            
            for setting_name, setting_value in settings:
                cur.execute('''INSERT OR REPLACE INTO system_settings (setting_name, setting_value, updated_at)
                               VALUES (?, ?, CURRENT_TIMESTAMP)''', (setting_name, setting_value))
            
            conn.commit()
            conn.close()
            
            print(f"DEBUG: Successfully saved admin settings to database - school_name: {school_name}, academic_year: {academic_year}")
            flash("✅ Settings saved successfully to database!", "success")
            return redirect(url_for('admin_settings'))
            
        except Exception as e:
            print(f"DEBUG: Error in admin_settings: {str(e)}")
            flash(f"❌ Error saving settings: {str(e)}", "error")
            return redirect(url_for('admin_settings'))
    
    # Load current settings from database for GET request
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT setting_name, setting_value FROM system_settings")
    settings_data = dict(cur.fetchall())
    conn.close()
    
    return render_template('admin_settings.html', settings=settings_data)

# --- Admin: Users / Subjects / Assignments / Schedule ---
@app.route('/manage_users', methods=['GET','POST'])
def manage_users():
    if not is_admin():
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        cur.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                   (username,password,role))
        conn.commit()

    # Get all users
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    # Get all subjects
    cur.execute("SELECT id, name FROM subjects")
    subjects = cur.fetchall()

    # Get current enrollments
    cur.execute('''SELECT enrollments.user_id, enrollments.subject_id
                   FROM enrollments''')
    enrollments = cur.fetchall()

    return render_template('manage_users.html',
                         users=users,
                         subjects=subjects,
                         enrollments=enrollments)

@app.route('/delete_user', methods=['POST'])
def delete_user():
    if not is_admin():
        return redirect(url_for('login'))

    user_id = request.form['user_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    cur.execute("DELETE FROM assignments WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM enrollments WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM schedule WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM attendance WHERE user_id=?", (user_id,))
    conn.commit()
    return redirect(url_for('manage_users'))

@app.route('/manage_subjects', methods=['GET','POST'])
def manage_subjects():
    if not is_admin():
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        subject_name = request.form['subject_name']
        teacher_id = request.form.get('teacher_id')
        cur.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", (subject_name, teacher_id))
        conn.commit()

    # Get all subjects
    cur.execute('''SELECT subjects.*, users.username as teacher_name
                   FROM subjects
                   LEFT JOIN users ON subjects.teacher_id = users.id''')
    subjects = cur.fetchall()
    cur.execute("SELECT id, username FROM users WHERE role='teacher'")
    teachers = cur.fetchall()
    return render_template('manage_subjects.html', subjects=subjects, teachers=teachers)

@app.route('/delete_subject', methods=['POST'])
def delete_subject():
    if not is_admin():
        return redirect(url_for('login'))

    subject_id = request.form['subject_id']
    conn = get_db()
    cur = conn.cursor()

    # Proceed with deletion
    cur.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
    cur.execute("DELETE FROM assignments WHERE subject_id=?", (subject_id,))
    cur.execute("DELETE FROM enrollments WHERE subject_id=?", (subject_id,))
    conn.commit()
    return redirect(url_for('manage_subjects'))

@app.route('/manage_assignments', methods=['GET','POST'])
def manage_assignments():
    if not (is_admin() or is_teacher()):
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    user_id = session['user_id']

    if is_admin():
        # Admin can see all subjects
        cur.execute("SELECT * FROM subjects")
        subjects = cur.fetchall()
    else:
        # Teachers can only see their subjects
        cur.execute("SELECT * FROM subjects WHERE teacher_id = ?", (user_id,))
        subjects = cur.fetchall()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            assignment_id = request.form['assignment_id']
            if is_admin():
                cur.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
            else:
                cur.execute('''DELETE FROM assignments
                              WHERE id = ? AND subject_id IN
                              (SELECT id FROM subjects WHERE teacher_id = ?)''',
                              (assignment_id, user_id))
            conn.commit()
        else:
            subject_id = request.form['subject_id']
            assignment_name = request.form['assignment_name']
            user_id = request.form.get('user_id')

            # Verify subject belongs to teacher
            if not is_admin():
                cur.execute("SELECT id FROM subjects WHERE id = ? AND teacher_id = ?",
                           (subject_id, user_id))
                if not cur.fetchone():
                    return redirect(url_for('manage_assignments'))

            if user_id:  # If assigning to specific student
                cur.execute("INSERT INTO assignments (name, grade, subject_id, user_id) VALUES (?,?,?,?)",
                            (assignment_name, 0, subject_id, user_id))
            else:  # If creating general assignment
                cur.execute("INSERT INTO assignments (name, subject_id, user_id) VALUES (?,?,?)",
                            (assignment_name, subject_id, session['user_id']))
            conn.commit()

    # Get assignments
    if is_admin():
        cur.execute('''SELECT assignments.*, subjects.name AS subject_name
                       FROM assignments
                       JOIN subjects ON assignments.subject_id = subjects.id''')
    else:
        cur.execute('''SELECT assignments.*, subjects.name AS subject_name
                       FROM assignments
                       JOIN subjects ON assignments.subject_id = subjects.id
                       WHERE subjects.teacher_id = ?''', (user_id,))
    assignments = cur.fetchall()

    # Get students
    if is_admin():
        cur.execute("SELECT * FROM users WHERE role='student'")
    else:
        cur.execute('''SELECT DISTINCT users.*
                       FROM users
                       JOIN enrollments ON users.id = enrollments.user_id
                       JOIN subjects ON enrollments.subject_id = subjects.id
                       WHERE subjects.teacher_id = ? AND users.role = 'student' ''', (user_id,))
    students = cur.fetchall()

    return render_template('manage_assignments.html',
                         subjects=subjects,
                         students=students,
                         assignments=assignments)

@app.route('/delete_assignment', methods=['POST'])
def delete_assignment():
    if not (is_admin() or is_teacher()):
        return redirect(url_for('login'))

    assignment_id = request.form['assignment_id']
    conn = get_db()
    cur = conn.cursor()

    # Proceed with deletion
    cur.execute("DELETE FROM assignments WHERE id=?", (assignment_id,))
    conn.commit()
    return redirect(url_for('manage_assignments'))

@app.route('/edit_grade', methods=['POST'])
def edit_grade():
    if not (is_admin() or is_teacher()):
        return redirect(url_for('login'))

    assignment_id = request.form['assignment_id']
    grade = request.form['grade']
    conn = get_db()
    cur = conn.cursor()

    # Proceed with grade update
    cur.execute("UPDATE assignments SET grade=? WHERE id=?", (grade, assignment_id))
    conn.commit()
    return redirect(url_for('manage_assignments'))

# --- Student Dashboard ---
@app.route('/student_progress')
def student_progress():
    if not is_student():
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Get current grading scale
    grading_scale = get_grading_scale()

    # Get student's subjects and grades
    cur.execute('''SELECT subjects.name as subject, subjects.id,
                          users.username as teacher_name,
                          COALESCE(AVG(assignments.grade), 0) as avg_grade
                   FROM enrollments
                   JOIN subjects ON enrollments.subject_id = subjects.id
                   LEFT JOIN users ON subjects.teacher_id = users.id
                   LEFT JOIN assignments ON assignments.subject_id = subjects.id
                   AND assignments.user_id = ?
                   WHERE enrollments.user_id = ?
                   GROUP BY subjects.id''', (user_id, user_id))
    
    subjects = []
    total_grade = 0
    for s in cur.fetchall():
        # Get assignments for this subject
        cur.execute('''SELECT * FROM assignments 
                      WHERE subject_id = ? AND user_id = ?
                      ORDER BY id DESC''', (s['id'], user_id))
        assignments = cur.fetchall()
        
        avg_grade = s['avg_grade'] if s['avg_grade'] else 0
        total_grade += avg_grade
        
        subjects.append({
            'subject': s['subject'],
            'id': s['id'],
            'teacher': s['teacher_name'],
            'avg_grade': avg_grade,
            'assignments': assignments,
            'formatted_avg_grade': format_grade(avg_grade, grading_scale),
            'is_passing': is_passing_grade(avg_grade)
        })
    
    overall_grade = total_grade / len(subjects) if subjects else 0
    
    # Calculate recent performance (last 10 assignments)
    cur.execute('''SELECT AVG(grade) as recent_avg FROM (
                      SELECT grade FROM assignments 
                      WHERE user_id = ? AND grade > 0
                      ORDER BY id DESC LIMIT 10
                   )''', (user_id,))
    recent_avg = cur.fetchone()
    avg_recent_grade = recent_avg['recent_avg'] if recent_avg['recent_avg'] else 0
    
    # Calculate improvement (compare recent vs older grades)
    cur.execute('''SELECT AVG(grade) as old_avg FROM (
                      SELECT grade FROM assignments 
                      WHERE user_id = ? AND grade > 0
                      ORDER BY id DESC LIMIT 20 OFFSET 10
                   )''', (user_id,))
    old_avg = cur.fetchone()
    old_average = old_avg['old_avg'] if old_avg['old_avg'] else avg_recent_grade
    improvement_percentage = avg_recent_grade - old_average
    
    # Count recent assignments
    cur.execute('''SELECT COUNT(*) as count FROM assignments 
                   WHERE user_id = ? AND date(id) >= date('now', '-30 days')''', (user_id,))
    recent_assignments = cur.fetchone()
    recent_assignments_count = recent_assignments['count'] if recent_assignments else 0
    
    # Get attendance statistics
    cur.execute('''SELECT COUNT(*) as total_days,
                          SUM(present) as days_present,
                          ROUND(AVG(CAST(present AS FLOAT)) * 100, 1) as attendance_rate
                   FROM attendance 
                   WHERE user_id = ?''', (user_id,))
    attendance_data = cur.fetchone()
    
    total_days = attendance_data['total_days'] if attendance_data['total_days'] else 1
    days_present = attendance_data['days_present'] if attendance_data['days_present'] else 0
    overall_attendance = attendance_data['attendance_rate'] if attendance_data['attendance_rate'] else 100
    
    # Calculate grade trend (simple comparison)
    grade_trend = improvement_percentage  # positive = improving, negative = declining
    
    return render_template('student_progress.html',
                         subjects=subjects,
                         overall_grade=overall_grade,
                         formatted_overall_grade=format_grade(overall_grade, grading_scale),
                         avg_recent_grade=avg_recent_grade,
                         formatted_recent_grade=format_grade(avg_recent_grade, grading_scale),
                         improvement_percentage=improvement_percentage,
                         recent_assignments_count=recent_assignments_count,
                         total_days=total_days,
                         days_present=days_present,
                         overall_attendance=overall_attendance,
                         grade_trend=grade_trend,
                         grading_scale=grading_scale,
                         format_grade=format_grade,
                         is_passing_grade=is_passing_grade)

@app.route('/student_attendance')
def student_attendance():
    if not is_student():
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Show 20 records per page
    offset = (page - 1) * per_page

    # Get total count of attendance records
    cur.execute('''SELECT COUNT(*) FROM attendance WHERE user_id = ?''', (user_id,))
    total_records = cur.fetchone()[0]
    
    # Get recent attendance records with pagination
    cur.execute('''SELECT subjects.name as subject_name,
                          attendance.date,
                          attendance.present,
                          subjects.id as subject_id
                   FROM attendance
                   JOIN subjects ON attendance.subject_id = subjects.id
                   WHERE attendance.user_id = ?
                   ORDER BY attendance.date DESC
                   LIMIT ? OFFSET ?''', (user_id, per_page, offset))
    attendance_records = cur.fetchall()
    
    # Get attendance statistics by subject
    cur.execute('''SELECT subjects.name as subject_name,
                          COUNT(*) as total_classes,
                          SUM(present) as classes_present,
                          ROUND(AVG(CAST(present AS FLOAT)) * 100, 1) as attendance_rate
                   FROM attendance
                   JOIN subjects ON attendance.subject_id = subjects.id
                   WHERE attendance.user_id = ?
                   GROUP BY subjects.id, subjects.name
                   ORDER BY subjects.name''', (user_id,))
    subject_attendance = cur.fetchall()
    
    # Calculate pagination info
    total_pages = (total_records + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('student_attendance.html',
                         attendance_records=attendance_records,
                         subject_attendance=subject_attendance,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         total_records=total_records)

@app.route('/student_dashboard')
def student_dashboard():
    if not is_student():
        return redirect(url_for('login'))
    user_id = session['user_id']
    username = session['username']
    conn = get_db()
    cur = conn.cursor()

    # Get current grading scale
    grading_scale = get_grading_scale()

    # Get subjects the student is enrolled in
    cur.execute('''SELECT DISTINCT
                subjects.id,
                subjects.name,
                users.username as teacher_name
                FROM subjects
                JOIN enrollments ON subjects.id = enrollments.subject_id
                LEFT JOIN users ON subjects.teacher_id = users.id
                WHERE enrollments.user_id = ?''', (user_id,))
    subjects = cur.fetchall()

    subject_grades = []
    for s in subjects:
        # Get average grade for completed assignments
        cur.execute('''SELECT AVG(grade) as avg_grade
                      FROM assignments
                      WHERE user_id = ?
                      AND subject_id = ?
                      AND grade > 0''', (user_id, s['id']))
        avg_grade = cur.fetchone()['avg_grade'] or 0

        # Get all assignments for this subject
        cur.execute('''SELECT name, grade
                      FROM assignments
                      WHERE subject_id = ?
                      AND (user_id = ? OR user_id IN
                          (SELECT id FROM users WHERE role = 'teacher'))''',
                      (s['id'], user_id))
        assignments = cur.fetchall()

        subject_grades.append({
            'subject': s['name'],
            'id': s['id'],
            'teacher': s['teacher_name'],
            'avg_grade': avg_grade,
            'formatted_avg_grade': format_grade(avg_grade, grading_scale),
            'assignments': assignments,
            'is_passing': is_passing_grade(avg_grade)
        })

    # Create schedule table if it doesn't exist
    cur.execute('''CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        subject_id INTEGER,
        day TEXT,
        period INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )''')
    conn.commit()

    # Get student's schedule
    cur.execute('''SELECT subjects.name, schedule.day, schedule.period
                   FROM schedule
                   JOIN subjects ON schedule.subject_id = subjects.id
                   WHERE schedule.user_id = ?
                   ORDER BY
                     CASE schedule.day
                       WHEN 'Monday' THEN 1
                       WHEN 'Tuesday' THEN 2
                       WHEN 'Wednesday' THEN 3
                       WHEN 'Thursday' THEN 4
                       WHEN 'Friday' THEN 5
                     END,
                     schedule.period''', (user_id,))
    schedule = cur.fetchall()

    # Get student's attendance
    cur.execute('''SELECT
                   subjects.name,
                   COUNT(CASE WHEN present = 1 THEN 1 END) as present_count,
                   COUNT(*) as total_count
                   FROM attendance
                   JOIN subjects ON attendance.subject_id = subjects.id
                   WHERE attendance.user_id = ?
                   AND date >= date('now', '-30 days')
                   GROUP BY subjects.id''', (user_id,))
    attendance = cur.fetchall()

    attendance_stats = {}
    for a in attendance:
        attendance_rate = (a['present_count'] / a['total_count'] * 100) if a['total_count'] > 0 else 100
        attendance_stats[a['name']] = round(attendance_rate, 1)

    return render_template('student_dashboard.html',
                         username=username,
                         subject_grades=subject_grades,
                         schedule=schedule,
                         attendance_stats=attendance_stats,
                         grading_scale=grading_scale,
                         format_grade=format_grade)

# --- Subject Page ---
@app.route('/subject/<int:subject_id>')
def subject(subject_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM subjects WHERE id=?", (subject_id,))
    sub = cur.fetchone()
    if not sub:
        return "Subject not found", 404
    cur.execute("SELECT name, grade FROM assignments WHERE subject_id=? AND user_id=?", (subject_id, user_id))
    assignments = cur.fetchall()
    return render_template('subject.html', subject=sub['name'], assignments=assignments)

# --- Teacher Dashboard ---
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if not is_teacher():
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Get current grading scale
    grading_scale = get_grading_scale()

    # Get all subjects assigned to the teacher
    cur.execute('''SELECT DISTINCT subjects.id, subjects.name
                   FROM subjects
                   LEFT JOIN assignments ON subjects.id = assignments.subject_id
                   WHERE assignments.user_id=? OR subjects.teacher_id=?''', (user_id, user_id))
    my_classes = cur.fetchall()

    # Stats - Get total number of students in teacher's subjects
    cur.execute('''SELECT COUNT(DISTINCT enrollments.user_id) as student_count
                   FROM enrollments
                   JOIN subjects ON enrollments.subject_id = subjects.id
                   WHERE subjects.teacher_id = ?''', (user_id,))
    students_count = cur.fetchone()['student_count'] or 0

    # Get active assignments (assignments with no grades yet)
    cur.execute('''SELECT COUNT(*) as active_assignments
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   WHERE subjects.teacher_id = ? AND (grade IS NULL OR grade = 0)''', (user_id,))
    active_assignments = cur.fetchone()['active_assignments'] or 0

    # Ensure attendance table exists
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        subject_id INTEGER,
                        date TEXT,
                        present INTEGER
                   )''')
    conn.commit()

    # Calculate attendance rate for the current week
    cur.execute('''SELECT AVG(CAST(present AS FLOAT))*100 as attendance_rate
                   FROM attendance
                   WHERE subject_id IN (SELECT id FROM subjects WHERE teacher_id = ?)
                   AND date >= date('now', '-7 days')''', (user_id,))
    row = cur.fetchone()
    attendance_rate = round(row['attendance_rate'] if row['attendance_rate'] is not None else 100, 1)

    # Calculate average grade across all assignments in teacher's subjects
    cur.execute('''SELECT AVG(CAST(assignments.grade AS FLOAT)) as avg_grade
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   WHERE subjects.teacher_id = ? AND assignments.grade > 0''', (user_id,))
    average_grade = round(cur.fetchone()['avg_grade'] or 0, 1)

    cur.execute('''SELECT assignments.name, subjects.name as subject_name
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   WHERE assignments.user_id=?
                   ORDER BY assignments.id DESC LIMIT 5''', (user_id,))
    recent_activity = [f"Assignment '{r['name']}' in {r['subject_name']}" for r in cur.fetchall()]

    return render_template('teacher_dashboard.html',
                           my_classes=my_classes,
                           students_count=students_count,
                           active_assignments=active_assignments,
                           attendance_rate=attendance_rate,
                           average_grade=average_grade,
                           formatted_average_grade=format_grade(average_grade, grading_scale),
                           recent_activity=recent_activity,
                           grading_scale=grading_scale,
                           format_grade=format_grade)

# --- Add Assignment ---
@app.route('/add_assignment', methods=['GET','POST'])
def add_assignment():
    if not is_teacher():
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Get subjects assigned to this teacher
    cur.execute('''SELECT DISTINCT subjects.id, subjects.name
                   FROM subjects
                   WHERE subjects.teacher_id = ?''', (user_id,))
    my_classes = cur.fetchall()

    if request.method == 'POST':
        subject_id = request.form['subject_id']
        assignment_name = request.form['assignment_name']
        cur.execute("INSERT INTO assignments (name, grade, subject_id, user_id) VALUES (?, ?, ?, ?)",
                    (assignment_name, 0, subject_id, user_id))
        conn.commit()
        return redirect(url_for('add_assignment'))

    return render_template('add_assignment.html', my_classes=my_classes)


# --- Enter Grades ---
@app.route('/enter_grades', methods=['GET','POST'])
def enter_grades():
    if not is_teacher():
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Get all subjects for this teacher
    cur.execute('''SELECT id, name FROM subjects WHERE teacher_id = ?''', (user_id,))
    subjects = cur.fetchall()

    # Get current grading scale
    grading_scale = get_grading_scale()

    # Get all students and their assignments for each subject
    students_assignments = []
    for subject in subjects:
        cur.execute('''SELECT
                        users.id as student_id,
                        users.username as student_name,
                        assignments.id as assignment_id,
                        assignments.name as assignment_name,
                        assignments.grade,
                        subjects.name as subject_name
                    FROM users
                    JOIN enrollments ON users.id = enrollments.user_id
                    JOIN subjects ON enrollments.subject_id = subjects.id
                    LEFT JOIN assignments ON (
                        assignments.subject_id = subjects.id
                        AND assignments.user_id = users.id
                    )
                    WHERE subjects.id = ? AND users.role = 'student'
                    ORDER BY users.username, assignments.name''', (subject['id'],))
        students_assignments.extend(cur.fetchall())

    if request.method == 'POST':
        student_id = request.form['student_id']
        subject_id = request.form['subject_id']
        assignment_name = request.form.get('assignment_name')
        grade_input = request.form.get('grade')
        assignment_id = request.form.get('assignment_id')

        # Convert grade input to percentage for storage (always store as percentage)
        if grade_input:
            try:
                if grading_scale == 'letter':
                    grade = letter_to_percentage(grade_input.upper())
                elif grading_scale == 'gpa':
                    grade = gpa_to_percentage(float(grade_input))
                else:  # percentage
                    grade = float(grade_input)
            except (ValueError, TypeError):
                flash("❌ Invalid grade format", "error")
                return redirect(url_for('enter_grades'))
        else:
            grade = None

        if assignment_id:  # Update existing assignment
            cur.execute('''UPDATE assignments
                          SET grade = ?
                          WHERE id = ? AND subject_id = ?''',
                          (grade, assignment_id, subject_id))
        else:  # Create new assignment
            cur.execute('''INSERT INTO assignments (name, grade, subject_id, user_id)
                          VALUES (?, ?, ?, ?)''',
                          (assignment_name, grade, subject_id, student_id))
        conn.commit()
        flash("✅ Grade saved successfully!", "success")
        return redirect(url_for('enter_grades'))

    return render_template('enter_grades.html',
                         subjects=subjects,
                         students_assignments=students_assignments,
                         grading_scale=grading_scale,
                         format_grade=format_grade)

# --- Mark Attendance ---
@app.route('/mark_attendance', methods=['GET','POST'])
def mark_attendance():
    if not is_teacher():
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Create attendance table if it doesn't exist
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        subject_id INTEGER,
                        date TEXT,
                        present INTEGER
                   )''')
    conn.commit()

    # Get teacher's subjects
    cur.execute('''SELECT id, name FROM subjects WHERE teacher_id = ?''', (user_id,))
    subjects = cur.fetchall()

    # Get today's date
    today = datetime.now().date().isoformat()

    # Initialize attendance data list
    attendance_data = []

    # Get selected date and subject from query parameters, defaulting to today
    selected_date = request.args.get('date', today)
    selected_subject = request.args.get('subject_id')

    if selected_subject:
        # Get all students enrolled in the selected subject and their attendance
        cur.execute('''
            SELECT
                users.id AS student_id,
                users.username,
                attendance.present,
                attendance.id AS attendance_id
            FROM users
            JOIN enrollments ON users.id = enrollments.user_id
            LEFT JOIN attendance ON (
                attendance.user_id = users.id
                AND attendance.subject_id = ?
                AND attendance.date = ?
            )
            WHERE enrollments.subject_id = ? AND users.role = 'student'
            ORDER BY users.username
        ''', (selected_subject, selected_date, selected_subject))
        attendance_data = cur.fetchall()

    if request.method == 'POST':
        subject_id = request.form['subject_id']
        date = request.form['date']

        # First delete any existing attendance records for this date and subject
        cur.execute('''DELETE FROM attendance
                      WHERE subject_id = ? AND date = ?''', (subject_id, date))

        # Insert new attendance records
        for key, value in request.form.items():
            if key.startswith('student_'):
                student_id = key.split('_')[1]
                present = 1 if value == 'present' else 0
                cur.execute('''INSERT INTO attendance (user_id, subject_id, date, present)
                              VALUES (?, ?, ?, ?)''', (student_id, subject_id, date, present))

        conn.commit()
        return redirect(url_for('mark_attendance', subject_id=subject_id, date=date))

    return render_template('mark_attendance.html',
                         subjects=subjects,
                         selected_subject=selected_subject,
                         selected_date=selected_date,
                         attendance_data=attendance_data)


# --- Teacher Reports ---


# --- Enroll Student ---
@app.route('/enroll_students', methods=['GET', 'POST'])
@app.route('/manage_students', methods=['GET', 'POST'])
def enroll_student():
    if not (is_admin() or is_teacher()):
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        student_id = request.form['student_id']
        subject_id = request.form['subject_id']

        try:
            cur.execute("INSERT INTO enrollments (user_id, subject_id) VALUES (?, ?)",
                       (student_id, subject_id))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Student is already enrolled

        if is_admin():
            return redirect(url_for('manage_users'))
        return redirect(url_for('teacher_dashboard'))

    # Get teacher's subjects
    cur.execute('''SELECT id, name FROM subjects WHERE teacher_id = ?''', (user_id,))
    subjects = cur.fetchall()

    # Get all students not enrolled in the selected subject
    selected_subject = request.args.get('subject_id')
    students = []
    if selected_subject:
        cur.execute('''SELECT id, username FROM users
                      WHERE role = 'student'
                      AND id NOT IN (
                          SELECT user_id FROM enrollments
                          WHERE subject_id = ?
                      )''', (selected_subject,))
        students = cur.fetchall()

    return render_template('manage_students.html', subjects=subjects, students=students)


# --- Teacher Settings ---
@app.route('/teacher_settings', methods=['GET','POST'])
def teacher_settings():
    if not is_teacher():
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    error = None
    success = None

    # Get current user data
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    current_user = cur.fetchone()

    # Create settings table if it doesn't exist
    cur.execute('''CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        email_notifications BOOLEAN DEFAULT 0,
        assignment_reminders BOOLEAN DEFAULT 0,
        attendance_reminders BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    conn.commit()

    # Get or create user settings
    cur.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    settings = cur.fetchone()
    if not settings:
        cur.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
        conn.commit()
        settings = {'email_notifications': 0, 'assignment_reminders': 0, 'attendance_reminders': 0}

    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Update username if changed
        if username != current_user['username']:
            cur.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
            if cur.fetchone():
                error = "Username already exists"
            else:
                cur.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
                success = "Settings updated successfully"

        # Update password if provided
        if new_password:
            if new_password != confirm_password:
                error = "Passwords do not match"
            else:
                cur.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
                success = "Settings updated successfully"

        # Update notification settings
        email_notifications = 1 if request.form.get('email_notifications') else 0
        assignment_reminders = 1 if request.form.get('assignment_reminders') else 0
        attendance_reminders = 1 if request.form.get('attendance_reminders') else 0

        cur.execute('''INSERT OR REPLACE INTO user_settings
                      (user_id, email_notifications, assignment_reminders, attendance_reminders)
                      VALUES (?, ?, ?, ?)''',
                   (user_id, email_notifications, assignment_reminders, attendance_reminders))

        conn.commit()
        if not error:
            success = "Settings updated successfully"

        # Refresh settings after update
        cur.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        settings = cur.fetchone()

    return render_template('teacher_settings.html',
                         current_user=current_user,
                         settings=settings,
                         error=error,
                         success=success)
    cur = conn.cursor()
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        if new_password:
            cur.execute("UPDATE users SET username=?, password=? WHERE id=?", (new_username, new_password, user_id))
        else:
            cur.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
        conn.commit()
        return redirect(url_for('teacher_settings'))
    cur.execute("SELECT username FROM users WHERE id=?", (user_id,))
    username = cur.fetchone()['username']
    return render_template('teacher_settings.html', username=username)

# --- Teacher Reports ---
@app.route('/teacher_analytics')
def teacher_analytics():
    if not is_teacher():
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Get current grading scale
    grading_scale = get_grading_scale()

    # Get comprehensive analytics for teacher's classes
    
    # Overall performance metrics
    cur.execute('''SELECT AVG(CAST(assignments.grade AS FLOAT)) as overall_avg,
                          COUNT(DISTINCT assignments.id) as total_assignments,
                          COUNT(DISTINCT enrollments.user_id) as total_students
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   JOIN enrollments ON enrollments.subject_id = subjects.id
                   WHERE subjects.teacher_id = ? AND assignments.grade > 0''', (user_id,))
    overview = cur.fetchone()
    
    overall_average = overview['overall_avg'] if overview['overall_avg'] else 0
    total_assignments = overview['total_assignments'] if overview['total_assignments'] else 0
    total_students = overview['total_students'] if overview['total_students'] else 0
    
    # Grade distribution (using current grading scale ranges)
    grade_distribution = {}
    if grading_scale == 'letter':
        grade_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    elif grading_scale == 'gpa':
        grade_distribution = {'4.0-3.5': 0, '3.4-2.5': 0, '2.4-1.5': 0, '1.4-1.0': 0, 'Below 1.0': 0}
    else:  # percentage
        grade_distribution = {'90-100%': 0, '80-89%': 0, '70-79%': 0, 'Below 70%': 0}
    
    cur.execute('''SELECT assignments.grade
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   WHERE subjects.teacher_id = ? AND assignments.grade > 0''', (user_id,))
    grades = cur.fetchall()
    
    for grade_row in grades:
        grade = grade_row['grade']
        if grading_scale == 'letter':
            letter_grade = percentage_to_letter(grade)
            if letter_grade.startswith('A'):
                grade_distribution['A'] += 1
            elif letter_grade.startswith('B'):
                grade_distribution['B'] += 1
            elif letter_grade.startswith('C'):
                grade_distribution['C'] += 1
            elif letter_grade.startswith('D'):
                grade_distribution['D'] += 1
            else:
                grade_distribution['F'] += 1
        elif grading_scale == 'gpa':
            gpa_grade = percentage_to_gpa(grade)
            if gpa_grade >= 3.5:
                grade_distribution['4.0-3.5'] += 1
            elif gpa_grade >= 2.5:
                grade_distribution['3.4-2.5'] += 1
            elif gpa_grade >= 1.5:
                grade_distribution['2.4-1.5'] += 1
            elif gpa_grade >= 1.0:
                grade_distribution['1.4-1.0'] += 1
            else:
                grade_distribution['Below 1.0'] += 1
        else:  # percentage
            if grade >= 90:
                grade_distribution['90-100%'] += 1
            elif grade >= 80:
                grade_distribution['80-89%'] += 1
            elif grade >= 70:
                grade_distribution['70-79%'] += 1
            else:
                grade_distribution['Below 70%'] += 1
    
    # Subject performance
    cur.execute('''SELECT subjects.name,
                          AVG(CAST(assignments.grade AS FLOAT)) as avg_grade,
                          COUNT(DISTINCT enrollments.user_id) as student_count
                   FROM subjects
                   LEFT JOIN assignments ON subjects.id = assignments.subject_id
                   LEFT JOIN enrollments ON subjects.id = enrollments.subject_id
                   WHERE subjects.teacher_id = ?
                   GROUP BY subjects.id''', (user_id,))
    subject_performance = cur.fetchall()
    
    # Attendance analytics
    cur.execute('''SELECT AVG(CAST(attendance.present AS FLOAT)) * 100 as attendance_rate,
                          COUNT(CASE WHEN attendance.present = 0 THEN 1 END) as absences
                   FROM attendance
                   JOIN subjects ON attendance.subject_id = subjects.id
                   WHERE subjects.teacher_id = ?''', (user_id,))
    attendance_data = cur.fetchone()
    attendance_rate = attendance_data['attendance_rate'] if attendance_data['attendance_rate'] else 100
    
    # Count frequently absent students (more than 3 absences)
    cur.execute('''SELECT COUNT(DISTINCT attendance.user_id) as absent_count
                   FROM attendance
                   JOIN subjects ON attendance.subject_id = subjects.id
                   WHERE subjects.teacher_id = ? 
                   GROUP BY attendance.user_id
                   HAVING COUNT(CASE WHEN attendance.present = 0 THEN 1 END) > 3''', (user_id,))
    absent_result = cur.fetchone()
    absent_students = absent_result['absent_count'] if absent_result else 0
    
    # Recent activities (last 10 graded assignments)
    cur.execute('''SELECT users.username as student_name,
                          assignments.name as assignment_name,
                          assignments.grade
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   JOIN users ON assignments.user_id = users.id
                   WHERE subjects.teacher_id = ? AND assignments.grade > 0
                   ORDER BY assignments.id DESC
                   LIMIT 10''', (user_id,))
    recent_activities = cur.fetchall()
    
    # Performance improvement trend (compare last 30 days vs previous 30 days)
    cur.execute('''SELECT AVG(CAST(grade AS FLOAT)) as recent_avg
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   WHERE subjects.teacher_id = ? AND assignments.grade > 0
                   AND assignments.id > (
                       SELECT COUNT(*) * 0.7 FROM assignments a2 
                       JOIN subjects s2 ON a2.subject_id = s2.id 
                       WHERE s2.teacher_id = ?
                   )''', (user_id, user_id))
    recent_avg = cur.fetchone()
    
    cur.execute('''SELECT AVG(CAST(grade AS FLOAT)) as older_avg
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   WHERE subjects.teacher_id = ? AND assignments.grade > 0
                   AND assignments.id <= (
                       SELECT COUNT(*) * 0.7 FROM assignments a2 
                       JOIN subjects s2 ON a2.subject_id = s2.id 
                       WHERE s2.teacher_id = ?
                   )''', (user_id, user_id))
    older_avg = cur.fetchone()
    
    recent_average = recent_avg['recent_avg'] if recent_avg['recent_avg'] else overall_average
    older_average = older_avg['older_avg'] if older_avg['older_avg'] else overall_average
    improvement_trend = recent_average - older_average
    
    return render_template('teacher_analytics.html',
                         overall_average=overall_average,
                         formatted_overall_average=format_grade(overall_average, grading_scale),
                         total_assignments=total_assignments,
                         total_students=total_students,
                         grade_distribution=grade_distribution,
                         subject_performance=subject_performance,
                         attendance_rate=attendance_rate,
                         absent_students=absent_students,
                         recent_activities=recent_activities,
                         improvement_trend=improvement_trend,
                         grading_scale=grading_scale,
                         format_grade=format_grade)

@app.route('/teacher_reports')
def teacher_reports():
    if not is_teacher():
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Get current grading scale
    grading_scale = get_grading_scale()

    # Get total students in teacher's subjects
    cur.execute('''SELECT COUNT(DISTINCT enrollments.user_id) AS total_students
                   FROM enrollments
                   JOIN subjects ON enrollments.subject_id = subjects.id
                   WHERE subjects.teacher_id=?''', (user_id,))
    total_students = cur.fetchone()['total_students'] or 0

    # Get total assignments in teacher's subjects
    cur.execute('''SELECT COUNT(*) AS total_assignments
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   WHERE subjects.teacher_id=?''', (user_id,))
    total_assignments = cur.fetchone()['total_assignments'] or 0

    # Get average grade in teacher's subjects
    cur.execute('''SELECT AVG(grade) AS avg_grade
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   WHERE subjects.teacher_id=? AND grade IS NOT NULL AND grade > 0''', (user_id,))
    average_grade = cur.fetchone()['avg_grade'] or 0

    # Get detailed reports for each subject taught by this teacher
    cur.execute('''SELECT subjects.id, subjects.name,
                          COUNT(DISTINCT enrollments.user_id) AS student_count,
                          COUNT(assignments.id) AS assignment_count,
                          AVG(CASE WHEN assignments.grade > 0 THEN assignments.grade END) AS average_grade
                   FROM subjects
                   LEFT JOIN enrollments ON subjects.id = enrollments.subject_id
                   LEFT JOIN assignments ON subjects.id = assignments.subject_id
                   WHERE subjects.teacher_id=?
                   GROUP BY subjects.id''', (user_id,))
    class_reports = cur.fetchall()

    return render_template('teacher_reports.html',
                           total_students=total_students,
                           total_assignments=total_assignments,
                           average_grade=round(average_grade, 1) if average_grade else 0,
                           formatted_average_grade=format_grade(average_grade, grading_scale),
                           class_reports=class_reports,
                           grading_scale=grading_scale,
                           format_grade=format_grade)

# --- Manage Schedule ---
@app.route('/manage_schedule', methods=['GET', 'POST'])
def manage_schedule():
    if not (is_admin() or is_teacher()):
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Create schedule table if it doesn't exist
    cur.execute('''CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        subject_id INTEGER,
        day TEXT,
        period INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )''')
    conn.commit()

    # Get teacher's subjects
    cur.execute('''SELECT id, name FROM subjects WHERE teacher_id = ?''', (user_id,))
    subjects = cur.fetchall()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            if 'schedule_id' in request.form:  # For schedule deletion
                schedule_id = request.form['schedule_id']
                cur.execute('''DELETE FROM schedule
                              WHERE id = ? AND subject_id IN
                              (SELECT id FROM subjects WHERE teacher_id = ?)''',
                              (schedule_id, user_id))
                conn.commit()
            elif 'assignment_id' in request.form:  # For assignment deletion
                assignment_id = request.form['assignment_id']
                # Only delete if the assignment belongs to one of the teacher's subjects
                cur.execute('''DELETE FROM assignments
                              WHERE id = ? AND subject_id IN
                              (SELECT id FROM subjects WHERE teacher_id = ?)''',
                              (assignment_id, user_id))
                conn.commit()
        else:
            subject_id = request.form['subject_id']
            day = request.form['day']
            period = request.form['period']

            # Check for existing schedule in that time slot
            cur.execute('''SELECT COUNT(*) as count FROM schedule
                          WHERE day = ? AND period = ? AND subject_id IN
                          (SELECT id FROM subjects WHERE teacher_id = ?)''',
                          (day, period, user_id))
            if cur.fetchone()['count'] == 0:
                cur.execute('''INSERT INTO schedule (subject_id, day, period)
                              VALUES (?, ?, ?)''', (subject_id, day, period))
                conn.commit()

    # Get current schedule
    cur.execute('''SELECT schedule.*, subjects.name as subject_name
                   FROM schedule
                   JOIN subjects ON schedule.subject_id = subjects.id
                   WHERE subjects.teacher_id = ?
                   ORDER BY
                     CASE schedule.day
                       WHEN 'Monday' THEN 1
                       WHEN 'Tuesday' THEN 2
                       WHEN 'Wednesday' THEN 3
                       WHEN 'Thursday' THEN 4
                       WHEN 'Friday' THEN 5
                     END,
                     schedule.period''', (user_id,))
    schedule = cur.fetchall()

    return render_template('manage_schedule.html',
                         subjects=subjects,
                         schedule=schedule,
                         days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                         periods=range(1, 9))

# --- Initialize Database ---
if __name__ == '__main__':
    # Initialize database and demo data for local development
    get_db()  # Creates database and tables if they don't exist
    init_demo_data()  # Initialize demo data
    app.run(debug=True)

# Initialize demo data for production deployment (like Vercel)
if not app.debug and os.environ.get('VERCEL'):
    init_demo_data()
