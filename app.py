from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from datetime import datetime, date

# Import advanced feature modules with error handling
try:
    from email_service import EmailService, register_email_routes
    EMAIL_AVAILABLE = True
except ImportError as e:
    print(f"Email service not available: {e}")
    EMAIL_AVAILABLE = False

try:
    from parent_portal import register_parent_routes
    PARENT_PORTAL_AVAILABLE = True
except ImportError as e:
    print(f"Parent portal not available: {e}")
    PARENT_PORTAL_AVAILABLE = False

try:
    from advanced_analytics import register_analytics_routes
    ANALYTICS_AVAILABLE = True
except ImportError as e:
    print(f"Advanced analytics not available: {e}")
    ANALYTICS_AVAILABLE = False

try:
    from api_module import register_api
    API_AVAILABLE = True
except ImportError as e:
    print(f"API module not available: {e}")
    API_AVAILABLE = False

try:
    from realtime_module import init_socketio, socketio, notify_new_grade, notify_assignment_created
    REALTIME_AVAILABLE = True
except ImportError as e:
    print(f"Real-time features not available: {e}")
    REALTIME_AVAILABLE = False
    socketio = None

try:
    from export_module import register_export_routes
    EXPORT_AVAILABLE = True
except ImportError as e:
    print(f"Export functionality not available: {e}")
    EXPORT_AVAILABLE = False

try:
    from i18n_module import register_i18n_routes, t, get_current_language
    I18N_AVAILABLE = True
except ImportError as e:
    print(f"Multi-language support not available: {e}")
    I18N_AVAILABLE = False

try:
    from lms_integration import register_lms_routes
    LMS_AVAILABLE = True
except ImportError as e:
    print(f"LMS integration not available: {e}")
    LMS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database configuration - use in-memory for Vercel, file-based for local development
if os.environ.get('VERCEL_DEPLOYMENT'):
    DATABASE = ':memory:'  # In-memory database for Vercel
else:
    DATABASE = os.path.join(os.path.dirname(__file__), 'school.db')

# --- Helper Functions ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def is_admin():
    return session.get('role') == 'admin'

def is_student():
    return session.get('role') == 'student'

def is_teacher():
    return session.get('role') == 'teacher'

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
    
    # Get subject performance
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
    
    return render_template('system_analytics.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_subjects=total_subjects,
                         total_assignments=total_assignments,
                         avg_grade=round(avg_grade, 1),
                         attendance_rate=round(attendance_rate, 1),
                         subject_performance=subject_performance)

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
            
            # Save settings
            settings_data = [
                ('school_name', school_name),
                ('academic_year', academic_year),
                ('email_notifications', str(email_notifications)),
                ('sms_notifications', str(sms_notifications)),
                ('grading_scale', grading_scale),
                ('passing_grade', passing_grade),
                ('session_timeout', session_timeout),
                ('force_password_change', str(force_password_change))
            ]
            
            for setting_name, setting_value in settings_data:
                cur.execute('''INSERT OR REPLACE INTO system_settings 
                              (setting_name, setting_value) VALUES (?, ?)''', 
                              (setting_name, setting_value))
            
            conn.commit()
            return redirect(url_for('admin_settings'))
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return redirect(url_for('admin_settings'))
    
    # Load current settings
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT setting_name, setting_value FROM system_settings")
    settings = dict(cur.fetchall())
    
    return render_template('admin_settings.html', settings=settings)

@app.route('/system_settings', methods=['GET', 'POST'])
def system_settings():
    if not is_admin():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Extract form data
            email_notifications = 1 if request.form.get('email_notifications') else 0
            force_password_change = 1 if request.form.get('force_password_change') else 0
            
            # Save settings
            cur.execute('''INSERT OR REPLACE INTO system_settings 
                          (setting_name, setting_value) VALUES (?, ?),
                          (?, ?)''', 
                          ('email_notifications', str(email_notifications),
                           'force_password_change', str(force_password_change)))
            
            conn.commit()
            return redirect(url_for('system_settings'))
            
        except Exception as e:
            return redirect(url_for('system_settings'))
    
    # Load current settings
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT setting_name, setting_value FROM system_settings")
    settings = dict(cur.fetchall())
    
    return render_template('admin_settings.html', settings=settings)

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

# --- Student Progress and Attendance ---
@app.route('/student_progress')
def student_progress():
    if not is_student():
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Get student's subjects and grades
    cur.execute('''SELECT subjects.name as subject,
                          users.username as teacher_name,
                          AVG(assignments.grade) as avg_grade
                   FROM enrollments
                   JOIN subjects ON enrollments.subject_id = subjects.id
                   LEFT JOIN users ON subjects.teacher_id = users.id
                   LEFT JOIN assignments ON assignments.subject_id = subjects.id
                   AND assignments.user_id = ?
                   WHERE enrollments.user_id = ?
                   GROUP BY subjects.id''', (user_id, user_id))
    
    subjects = []
    total_grade = 0
    total_subjects = 0
    
    for s in cur.fetchall():
        avg_grade = s['avg_grade'] if s['avg_grade'] else 0
        total_grade += avg_grade
        total_subjects += 1
        
        subjects.append({
            'subject': s['subject'],
            'teacher': s['teacher_name'],
            'avg_grade': avg_grade
        })
    
    overall_grade = total_grade / total_subjects if total_subjects > 0 else 0
    
    return render_template('student_progress.html',
                         subjects=subjects,
                         overall_grade=overall_grade)

@app.route('/student_attendance')
def student_attendance():
    if not is_student():
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    
    # Get attendance records
    cur.execute('''SELECT subjects.name as subject_name,
                          attendance.date,
                          attendance.present
                   FROM attendance
                   JOIN subjects ON attendance.subject_id = subjects.id
                   WHERE attendance.user_id = ?
                   ORDER BY attendance.date DESC''', (user_id,))
    attendance_records = cur.fetchall()
    
    # Get attendance statistics by subject
    cur.execute('''SELECT subjects.name as subject_name,
                          COUNT(*) as total_classes,
                          SUM(present) as classes_present,
                          ROUND(AVG(CAST(present AS FLOAT)) * 100, 1) as attendance_rate
                   FROM attendance
                   JOIN subjects ON attendance.subject_id = subjects.id
                   WHERE attendance.user_id = ?
                   GROUP BY subjects.id, subjects.name''', (user_id,))
    subject_attendance = cur.fetchall()
    
    return render_template('student_attendance.html',
                         attendance_records=attendance_records,
                         subject_attendance=subject_attendance)

# --- Student Dashboard ---
@app.route('/student_dashboard')
def student_dashboard():
    if not is_student():
        return redirect(url_for('login'))
    user_id = session['user_id']
    username = session['username']
    conn = get_db()
    cur = conn.cursor()

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
            'assignments': assignments
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
                         attendance_stats=attendance_stats)

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

# --- Teacher Analytics ---
@app.route('/teacher_analytics')
def teacher_analytics():
    if not is_teacher():
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Get overall analytics
    cur.execute('''SELECT AVG(assignments.grade) as overall_avg,
                          COUNT(DISTINCT assignments.id) as total_assignments,
                          COUNT(DISTINCT enrollments.user_id) as total_students
                   FROM assignments
                   JOIN subjects ON assignments.subject_id = subjects.id
                   JOIN enrollments ON enrollments.subject_id = subjects.id
                   WHERE subjects.teacher_id = ?''', (user_id,))
    stats = cur.fetchone()
    
    overall_average = stats['overall_avg'] if stats['overall_avg'] else 0
    total_assignments = stats['total_assignments']
    total_students = stats['total_students']
    
    # Get attendance statistics
    cur.execute('''SELECT AVG(CAST(present AS FLOAT))*100 as attendance_rate
                   FROM attendance
                   WHERE subject_id IN (SELECT id FROM subjects WHERE teacher_id = ?)
                   AND date >= date('now', '-30 days')''', (user_id,))
    attendance_rate = cur.fetchone()['attendance_rate'] or 100
    
    return render_template('teacher_analytics.html',
                         overall_average=round(overall_average, 1),
                         total_assignments=total_assignments,
                         total_students=total_students,
                         attendance_rate=round(attendance_rate, 1))

# --- Teacher Dashboard ---
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if not is_teacher():
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

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

    # Get unread message count
    from parent_portal import parent_portal
    unread_messages = parent_portal.get_unread_message_count(user_id, 'teacher')

    return render_template('teacher_dashboard.html',
                           my_classes=my_classes,
                           students_count=students_count,
                           active_assignments=active_assignments,
                           attendance_rate=attendance_rate,
                           average_grade=average_grade,
                           recent_activity=recent_activity,
                           unread_messages=unread_messages)

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
        grade = request.form.get('grade')
        assignment_id = request.form.get('assignment_id')

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
        return redirect(url_for('enter_grades'))

    return render_template('enter_grades.html', 
                         subjects=subjects,
                         students_assignments=students_assignments)

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
@app.route('/teacher_reports')
def teacher_reports():
    if not is_teacher():
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''SELECT COUNT(DISTINCT enrollments.user_id) AS total_students
                   FROM enrollments
                   JOIN assignments ON enrollments.subject_id = assignments.subject_id
                   WHERE assignments.user_id=?''', (user_id,))
    total_students = cur.fetchone()['total_students'] or 0

    cur.execute("SELECT COUNT(*) AS total_assignments FROM assignments WHERE user_id=?", (user_id,))
    total_assignments = cur.fetchone()['total_assignments'] or 0

    cur.execute("SELECT AVG(grade) AS avg_grade FROM assignments WHERE user_id=?", (user_id,))
    average_grade = cur.fetchone()['avg_grade'] or 0

    cur.execute('''SELECT subjects.id, subjects.name,
                          COUNT(DISTINCT enrollments.user_id) AS student_count,
                          COUNT(assignments.id) AS assignment_count,
                          AVG(assignments.grade) AS average_grade
                   FROM subjects
                   LEFT JOIN enrollments ON subjects.id = enrollments.subject_id
                   LEFT JOIN assignments ON subjects.id = assignments.subject_id AND assignments.user_id=?
                   WHERE subjects.id IN (SELECT DISTINCT assignments.subject_id FROM assignments WHERE assignments.user_id=?)
                   GROUP BY subjects.id''', (user_id, user_id))
    class_reports = cur.fetchall()

    return render_template('teacher_reports.html',
                           total_students=total_students,
                           total_assignments=total_assignments,
                           average_grade=average_grade,
                           class_reports=class_reports)

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

# --- Announcements System ---

@app.route('/announcements')
def view_announcements():
    """View announcements based on user role"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('role')
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    
    # Get announcements based on visibility
    if user_role == 'admin':
        # Admins see all announcements
        cur.execute('''SELECT announcements.*, users.username as author_name
                      FROM announcements
                      LEFT JOIN users ON announcements.author_id = users.id
                      WHERE announcements.is_active = 1
                      ORDER BY announcements.priority DESC, announcements.created_at DESC''')
    elif user_role == 'teacher':
        # Teachers see all announcements
        cur.execute('''SELECT announcements.*, users.username as author_name
                      FROM announcements
                      LEFT JOIN users ON announcements.author_id = users.id
                      WHERE announcements.is_active = 1
                      ORDER BY announcements.priority DESC, announcements.created_at DESC''')
    elif user_role == 'student':
        # Students see announcements visible to them
        cur.execute('''SELECT announcements.*, users.username as author_name
                      FROM announcements
                      LEFT JOIN users ON announcements.author_id = users.id
                      WHERE announcements.is_active = 1
                      AND (announcements.visibility = 'all' OR announcements.visibility = 'students')
                      ORDER BY announcements.priority DESC, announcements.created_at DESC''')
    elif user_role == 'parent':
        # Parents see announcements visible to them
        cur.execute('''SELECT announcements.*, users.username as author_name
                      FROM announcements
                      LEFT JOIN users ON announcements.author_id = users.id
                      WHERE announcements.is_active = 1
                      AND (announcements.visibility = 'all' OR announcements.visibility = 'parents')
                      ORDER BY announcements.priority DESC, announcements.created_at DESC''')
    
    announcements = cur.fetchall()
    
    # Mark urgent announcements
    for announcement in announcements:
        if announcement['priority'] == 'urgent':
            announcement['urgent'] = True
        elif announcement['priority'] == 'important':
            announcement['important'] = True
    
    return render_template('announcements.html', announcements=announcements)

@app.route('/manage_announcements', methods=['GET', 'POST'])
def manage_announcements():
    """Manage announcements (teachers and admins)"""
    if not (is_teacher() or is_admin()):
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'POST':
        if 'delete' in request.form:
            # Delete announcement
            announcement_id = request.form['announcement_id']
            cur.execute('DELETE FROM announcements WHERE id = ? AND author_id = ?', 
                       (announcement_id, user_id))
            conn.commit()
            return redirect(url_for('manage_announcements'))
        else:
            # Create new announcement
            title = request.form['title']
            content = request.form['content']
            visibility = request.form['visibility']
            priority = request.form['priority']
            
            cur.execute('''INSERT INTO announcements (title, content, author_id, visibility, priority)
                          VALUES (?, ?, ?, ?, ?)''', 
                       (title, content, user_id, visibility, priority))
            conn.commit()
            return redirect(url_for('manage_announcements'))
    
    # Get user's announcements
    cur.execute('''SELECT * FROM announcements 
                   WHERE author_id = ? 
                   ORDER BY created_at DESC''', (user_id,))
    my_announcements = cur.fetchall()
    
    return render_template('manage_announcements.html', announcements=my_announcements)

@app.route('/gradebook/<int:subject_id>', methods=['GET', 'POST'])
def gradebook(subject_id):
    """Gradebook view for teachers - table layout with students and assignments"""
    if not is_teacher():
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    
    # Verify teacher owns this subject
    cur.execute('SELECT name FROM subjects WHERE id = ? AND teacher_id = ?', (subject_id, user_id))
    subject = cur.fetchone()
    if not subject:
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        # Handle grade updates
        for key, value in request.form.items():
            if key.startswith('grade_'):
                # Parse student_id and assignment_id from form key
                _, student_id, assignment_id = key.split('_')
                grade = float(value) if value.strip() else None
                
                if grade is not None:
                    # Update or insert grade
                    cur.execute('''INSERT OR REPLACE INTO assignments 
                                  (user_id, subject_id, name, grade) 
                                  VALUES (?, ?, 
                                    (SELECT name FROM assignments WHERE id = ?), 
                                    ?)''', 
                               (int(student_id), subject_id, int(assignment_id), grade))
                else:
                    # Remove grade if empty
                    cur.execute('DELETE FROM assignments WHERE user_id = ? AND subject_id = ? AND id = ?',
                               (int(student_id), subject_id, int(assignment_id)))
        conn.commit()
        return redirect(url_for('gradebook', subject_id=subject_id))
    
    # Get all students enrolled in this subject
    cur.execute('''SELECT users.id, users.username, users.full_name
                   FROM users
                   JOIN enrollments ON users.id = enrollments.user_id
                   WHERE enrollments.subject_id = ? AND users.role = 'student'
                   ORDER BY users.username''', (subject_id,))
    students = cur.fetchall()
    
    # Get all assignments for this subject
    cur.execute('''SELECT DISTINCT assignments.name, assignments.id
                   FROM assignments
                   WHERE assignments.subject_id = ?
                   ORDER BY assignments.name''', (subject_id,))
    assignments = cur.fetchall()
    
    # Create grade matrix (student_id -> assignment_id -> grade)
    grade_matrix = {}
    for student in students:
        grade_matrix[student['id']] = {}
        for assignment in assignments:
            cur.execute('''SELECT grade FROM assignments 
                          WHERE user_id = ? AND subject_id = ? AND name = ?''',
                       (student['id'], subject_id, assignment['name']))
            result = cur.fetchone()
            grade_matrix[student['id']][assignment['id']] = result['grade'] if result else None
    
    # Calculate student averages
    student_averages = {}
    for student in students:
        grades = [grade for grade in grade_matrix[student['id']].values() if grade is not None]
        student_averages[student['id']] = sum(grades) / len(grades) if grades else 0
    
    # Calculate assignment averages
    assignment_averages = {}
    for assignment in assignments:
        grades = [grade_matrix[student['id']][assignment['id']] 
                 for student in students 
                 if grade_matrix[student['id']][assignment['id']] is not None]
        assignment_averages[assignment['id']] = sum(grades) / len(grades) if grades else 0
    
    return render_template('gradebook.html', 
                         subject=subject,
                         students=students,
                         assignments=assignments,
                         grade_matrix=grade_matrix,
                         student_averages=student_averages,
                         assignment_averages=assignment_averages,
                         subject_id=subject_id)

@app.route('/student_schedule')
def student_schedule():
    """Display student's weekly schedule with rotating schedule support"""
    if not is_student():
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    
    # Get student's enrolled subjects
    cur.execute('''SELECT subjects.id, subjects.name, subjects.teacher_id, users.username as teacher_name
                   FROM subjects
                   JOIN enrollments ON subjects.id = enrollments.subject_id
                   JOIN users ON subjects.teacher_id = users.id
                   WHERE enrollments.user_id = ?''', (user_id,))
    subjects = cur.fetchall()
    
    # Get schedule data
    cur.execute('''SELECT schedule.*, subjects.name as subject_name, users.username as teacher_name
                   FROM schedule
                   JOIN subjects ON schedule.subject_id = subjects.id
                   JOIN enrollments ON subjects.id = enrollments.subject_id
                   LEFT JOIN users ON subjects.teacher_id = users.id
                   WHERE enrollments.user_id = ? AND (schedule.week_type = ? OR schedule.week_type = 'both')
                   ORDER BY 
                     CASE schedule.day
                       WHEN 'Monday' THEN 1
                       WHEN 'Tuesday' THEN 2
                       WHEN 'Wednesday' THEN 3
                       WHEN 'Thursday' THEN 4
                       WHEN 'Friday' THEN 5
                     END,
                     schedule.period''', (user_id, current_week))
    schedule_data = cur.fetchall()
    
    # Organize schedule by day and period
    schedule_grid = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = range(1, 9)  # Assuming 8 periods per day
    
    for day in days:
        schedule_grid[day] = {}
        for period in periods:
            schedule_grid[day][period] = None
    
    # Fill in the schedule
    for item in schedule_data:
        if item['day'] in schedule_grid and item['period'] in schedule_grid[item['day']]:
            schedule_grid[item['day']][item['period']] = item
    
    # Determine current week type (A or B) - simple implementation
    # In a real system, this would be configurable
    current_week = 'A'  # Default to A, could be calculated based on school calendar
    
    return render_template('student_schedule.html', 
                         schedule_grid=schedule_grid,
                         days=days,
                         periods=periods,
                         current_week=current_week,
                         subjects=subjects)

# --- Initialize Database ---
def init_db():
    # For Vercel (in-memory) or if database doesn't exist locally
    if os.environ.get('VERCEL_DEPLOYMENT') or not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()

        # Create tables...

        # Create tables
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            full_name TEXT,
            email TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY,
            name TEXT,
            teacher_id INTEGER REFERENCES users(id),
            teacher_name TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            grade REAL,
            subject_id INTEGER,
            user_id INTEGER,
            date_created TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS enrollments (
            user_id INTEGER,
            subject_id INTEGER,
            PRIMARY KEY (user_id, subject_id)
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS schedule (
            subject_id INTEGER,
            day TEXT,
            period INTEGER,
            week_type TEXT DEFAULT 'both',
            PRIMARY KEY (subject_id, day, period, week_type)
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            subject_id INTEGER,
            date TEXT,
            present INTEGER
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            notifications_enabled INTEGER DEFAULT 1,
            language TEXT DEFAULT 'en'
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS parent_teacher_messages (
            id INTEGER PRIMARY KEY,
            parent_id INTEGER,
            teacher_id INTEGER,
            subject_id INTEGER,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            date_sent TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES users(id),
            FOREIGN KEY (teacher_id) REFERENCES users(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER,
            visibility TEXT DEFAULT 'all', -- 'all', 'students', 'teachers', 'parents', or subject_id
            priority TEXT DEFAULT 'normal', -- 'normal', 'important', 'urgent'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (author_id) REFERENCES users(id)
        )''')

        # Insert demo data for Vercel and Render deployments
        if os.environ.get('VERCEL_DEPLOYMENT') or os.environ.get('RENDER'):
            # Create demo users
            demo_users = [
                ('admin', 'admin123', 'admin', 'System Administrator', 'admin@edubridge.com'),
                ('teacher1', 'teacher123', 'teacher', 'John Smith', 'john@edubridge.com'),
                ('student1', 'student123', 'student', 'Alice Johnson', 'alice@edubridge.com'),
                ('parent1', 'parent123', 'parent', 'Bob Johnson', 'bob@edubridge.com')
            ]

            for username, password, role, full_name, email in demo_users:
                try:
                    cur.execute('INSERT INTO users (username, password, role, full_name, email) VALUES (?, ?, ?, ?, ?)',
                              (username, password, role, full_name, email))
                except sqlite3.IntegrityError:
                    pass  # User already exists

            # Create demo subjects
            demo_subjects = [
                ('Mathematics', 2, 'John Smith'),
                ('English', 2, 'John Smith'),
                ('Science', 2, 'John Smith')
            ]

            for name, teacher_id, teacher_name in demo_subjects:
                try:
                    cur.execute('INSERT INTO subjects (name, teacher_id, teacher_name) VALUES (?, ?, ?)',
                              (name, teacher_id, teacher_name))
                except sqlite3.IntegrityError:
                    pass

            # Create enrollments
            cur.execute('INSERT OR IGNORE INTO enrollments (user_id, subject_id) VALUES (3, 1)')
            cur.execute('INSERT OR IGNORE INTO enrollments (user_id, subject_id) VALUES (3, 2)')
            cur.execute('INSERT OR IGNORE INTO enrollments (user_id, subject_id) VALUES (3, 3)')

        conn.commit()
        conn.close()

    # Always ensure announcements table exists (for both local and Vercel)
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author_id INTEGER,
        visibility TEXT DEFAULT 'all',
        priority TEXT DEFAULT 'normal',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (author_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

    pass

# Register advanced feature modules
if EMAIL_AVAILABLE:
    register_email_routes(app)
    print("✓ Email service module loaded")

if PARENT_PORTAL_AVAILABLE:
    register_parent_routes(app)
    print("✓ Parent portal module loaded")

if ANALYTICS_AVAILABLE:
    register_analytics_routes(app)
    print("✓ Advanced analytics module loaded")

if API_AVAILABLE:
    register_api(app)
    print("✓ API module loaded")

if EXPORT_AVAILABLE:
    register_export_routes(app)
    print("✓ Export functionality module loaded")

if I18N_AVAILABLE:
    register_i18n_routes(app)
    print("✓ Multi-language support module loaded")

if LMS_AVAILABLE:
    register_lms_routes(app)
    print("✓ LMS integration module loaded")

# Initialize real-time features
if REALTIME_AVAILABLE:
    init_socketio(app)
    print("✓ Real-time features (WebSocket) module loaded")

# Add template globals for advanced features
@app.template_global()
def feature_available(feature_name):
    """Check if a feature is available"""
    return {
        'email': EMAIL_AVAILABLE,
        'parent_portal': PARENT_PORTAL_AVAILABLE,
        'analytics': ANALYTICS_AVAILABLE,
        'api': API_AVAILABLE,
        'realtime': REALTIME_AVAILABLE,
        'export': EXPORT_AVAILABLE,
        'i18n': I18N_AVAILABLE,
        'lms': LMS_AVAILABLE
    }.get(feature_name, False)

# Initialize database on app startup for Vercel and Render
if os.environ.get('VERCEL_DEPLOYMENT') or os.environ.get('RENDER'):
    init_db()

if __name__ == '__main__':
    init_db()
    print("\n=== Education Management System Starting ===")
    print("Basic features: ✓ Authentication, ✓ Student/Teacher Management, ✓ Grades, ✓ Attendance")
    
    # Use PORT environment variable for cloud deployment (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    
    if REALTIME_AVAILABLE and socketio:
        socketio.run(app, debug=False, host='0.0.0.0', port=port)
    else:
        app.run(debug=False, host='0.0.0.0', port=port)
