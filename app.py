from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = os.path.join(os.path.dirname(__file__), 'school.db')

# --- Helper Functions ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    
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
    
    # Create demo users
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', 'admin123', 'admin'))
    
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

    return render_template('teacher_dashboard.html',
                           my_classes=my_classes,
                           students_count=students_count,
                           active_assignments=active_assignments,
                           attendance_rate=attendance_rate,
                           average_grade=average_grade,
                           recent_activity=recent_activity)

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

# --- Initialize Database ---
def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
        cur.execute('''CREATE TABLE subjects (id INTEGER PRIMARY KEY, name TEXT, teacher_id INTEGER REFERENCES users(id))''')
        cur.execute('''CREATE TABLE assignments (id INTEGER PRIMARY KEY, name TEXT, grade REAL, subject_id INTEGER, user_id INTEGER)''')
        cur.execute('''CREATE TABLE enrollments (user_id INTEGER, subject_id INTEGER)''')
        cur.execute('''CREATE TABLE schedule (user_id INTEGER, subject_id INTEGER, day TEXT, period INTEGER)''')
        cur.execute('''CREATE TABLE attendance (id INTEGER PRIMARY KEY, user_id INTEGER, subject_id INTEGER, date TEXT, present INTEGER)''')
        conn.commit()
        conn.close()

    pass

if __name__ == '__main__':
    init_db()
    init_demo_data()  # Initialize demo data for Vercel
    app.run(debug=True)

# Initialize demo data for production deployment (like Vercel)
if not app.debug and os.environ.get('VERCEL'):
    init_demo_data()
