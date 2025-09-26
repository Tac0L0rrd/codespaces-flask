"""
RESTful API Module
Provides external API access to the education management system
"""

from flask import Blueprint, jsonify, request, g
from functools import wraps
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# API Configuration
API_SECRET_KEY = 'your-api-secret-key-here'
DATABASE = os.path.join(os.path.dirname(__file__), 'school.db')

def init_api_tables():
    """Initialize API-related tables"""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # API keys table
    cur.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY,
        key_id TEXT UNIQUE,
        key_hash TEXT,
        user_id INTEGER,
        name TEXT,
        permissions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        last_used TIMESTAMP,
        usage_count INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # API usage logs
    cur.execute('''CREATE TABLE IF NOT EXISTS api_logs (
        id INTEGER PRIMARY KEY,
        api_key_id TEXT,
        endpoint TEXT,
        method TEXT,
        ip_address TEXT,
        user_agent TEXT,
        response_code INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (api_key_id) REFERENCES api_keys(key_id)
    )''')
    
    conn.commit()
    conn.close()

def generate_api_key() -> tuple:
    """Generate a new API key pair (key_id, secret)"""
    key_id = secrets.token_urlsafe(16)
    secret = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(secret.encode()).hexdigest()
    return key_id, secret, key_hash

def verify_api_key(key_id: str, secret: str) -> dict:
    """Verify API key and return key info"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    
    cur.execute("""
        SELECT * FROM api_keys 
        WHERE key_id = ? AND key_hash = ? AND is_active = 1
        AND (expires_at IS NULL OR expires_at > datetime('now'))
    """, (key_id, secret_hash))
    
    api_key = cur.fetchone()
    
    if api_key:
        # Update usage stats
        cur.execute("""
            UPDATE api_keys 
            SET last_used = datetime('now'), usage_count = usage_count + 1
            WHERE key_id = ?
        """, (key_id,))
        conn.commit()
    
    conn.close()
    return dict(api_key) if api_key else None

def log_api_request(api_key_id: str, endpoint: str, method: str, 
                   ip_address: str, user_agent: str, response_code: int):
    """Log API request"""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO api_logs (api_key_id, endpoint, method, ip_address, user_agent, response_code)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (api_key_id, endpoint, method, ip_address, user_agent, response_code))
    
    conn.commit()
    conn.close()

def require_api_key(f):
    """Decorator to require valid API key for endpoint access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid API key format'}), 401
        
        try:
            # Parse API key from header: "Bearer key_id:secret"
            token = auth_header.split(' ')[1]
            key_id, secret = token.split(':', 1)
        except (IndexError, ValueError):
            return jsonify({'error': 'Invalid API key format'}), 401
        
        api_key_info = verify_api_key(key_id, secret)
        
        if not api_key_info:
            return jsonify({'error': 'Invalid or expired API key'}), 401
        
        # Check permissions if specified
        endpoint_permission = f.__name__
        permissions = api_key_info.get('permissions', '').split(',') if api_key_info.get('permissions') else ['all']
        
        if 'all' not in permissions and endpoint_permission not in permissions:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Log the request
        log_api_request(
            api_key_info['key_id'],
            request.endpoint,
            request.method,
            request.remote_addr,
            request.headers.get('User-Agent', ''),
            200  # Will be updated if error occurs
        )
        
        g.api_key_info = api_key_info
        return f(*args, **kwargs)
    
    return decorated_function

# API Endpoints

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/students', methods=['GET'])
@require_api_key
def get_students():
    """Get all students"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, username, full_name, email, phone
        FROM users 
        WHERE role = 'student'
        ORDER BY full_name, username
    """)
    
    students = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    return jsonify({
        'students': students,
        'count': len(students)
    })

@api_bp.route('/students/<int:student_id>', methods=['GET'])
@require_api_key
def get_student(student_id):
    """Get specific student details"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, username, full_name, email, phone
        FROM users 
        WHERE id = ? AND role = 'student'
    """, (student_id,))
    
    student = cur.fetchone()
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Get student's subjects
    cur.execute("""
        SELECT s.id, s.name, u.full_name as teacher_name
        FROM subjects s
        JOIN enrollments e ON s.id = e.subject_id
        LEFT JOIN users u ON s.teacher_id = u.id
        WHERE e.user_id = ?
    """, (student_id,))
    
    subjects = [dict(row) for row in cur.fetchall()]
    
    # Get recent grades
    cur.execute("""
        SELECT a.name, a.grade, s.name as subject_name, a.id
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.user_id = ? AND a.grade IS NOT NULL
        ORDER BY a.id DESC
        LIMIT 10
    """, (student_id,))
    
    grades = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return jsonify({
        'student': dict(student),
        'subjects': subjects,
        'recent_grades': grades
    })

@api_bp.route('/students/<int:student_id>/grades', methods=['GET'])
@require_api_key
def get_student_grades(student_id):
    """Get student's grades with optional filtering"""
    subject_id = request.args.get('subject_id', type=int)
    limit = request.args.get('limit', default=50, type=int)
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = """
        SELECT a.id, a.name, a.grade, s.name as subject_name, s.id as subject_id,
               u.full_name as teacher_name
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        LEFT JOIN users u ON s.teacher_id = u.id
        WHERE a.user_id = ? AND a.grade IS NOT NULL
    """
    params = [student_id]
    
    if subject_id:
        query += " AND s.id = ?"
        params.append(subject_id)
    
    query += " ORDER BY a.id DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    grades = [dict(row) for row in cur.fetchall()]
    
    # Calculate statistics
    if grades:
        grade_values = [g['grade'] for g in grades]
        stats = {
            'average': round(sum(grade_values) / len(grade_values), 2),
            'highest': max(grade_values),
            'lowest': min(grade_values),
            'count': len(grades)
        }
    else:
        stats = {'average': 0, 'highest': 0, 'lowest': 0, 'count': 0}
    
    conn.close()
    
    return jsonify({
        'grades': grades,
        'statistics': stats
    })

@api_bp.route('/students/<int:student_id>/attendance', methods=['GET'])
@require_api_key
def get_student_attendance(student_id):
    """Get student's attendance records"""
    days = request.args.get('days', default=30, type=int)
    subject_id = request.args.get('subject_id', type=int)
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = """
        SELECT att.date, att.present, s.name as subject_name, s.id as subject_id
        FROM attendance att
        JOIN subjects s ON att.subject_id = s.id
        WHERE att.user_id = ?
        AND att.date >= date('now', '-{} days')
    """.format(days)
    
    params = [student_id]
    
    if subject_id:
        query += " AND s.id = ?"
        params.append(subject_id)
    
    query += " ORDER BY att.date DESC"
    
    cur.execute(query, params)
    attendance_records = [dict(row) for row in cur.fetchall()]
    
    # Calculate attendance rate
    if attendance_records:
        present_count = sum(1 for record in attendance_records if record['present'])
        attendance_rate = (present_count / len(attendance_records)) * 100
    else:
        attendance_rate = 0
    
    conn.close()
    
    return jsonify({
        'attendance_records': attendance_records,
        'statistics': {
            'attendance_rate': round(attendance_rate, 2),
            'total_days': len(attendance_records),
            'present_days': sum(1 for record in attendance_records if record['present']),
            'absent_days': sum(1 for record in attendance_records if not record['present'])
        }
    })

@api_bp.route('/subjects', methods=['GET'])
@require_api_key
def get_subjects():
    """Get all subjects"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT s.id, s.name, u.full_name as teacher_name, u.username as teacher_username,
               COUNT(e.user_id) as student_count
        FROM subjects s
        LEFT JOIN users u ON s.teacher_id = u.id
        LEFT JOIN enrollments e ON s.id = e.subject_id
        GROUP BY s.id, s.name, u.full_name, u.username
        ORDER BY s.name
    """)
    
    subjects = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    return jsonify({
        'subjects': subjects,
        'count': len(subjects)
    })

@api_bp.route('/subjects/<int:subject_id>/students', methods=['GET'])
@require_api_key
def get_subject_students(subject_id):
    """Get students enrolled in a specific subject"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT u.id, u.username, u.full_name, u.email,
               AVG(a.grade) as average_grade,
               COUNT(a.id) as assignment_count
        FROM users u
        JOIN enrollments e ON u.id = e.user_id
        LEFT JOIN assignments a ON u.id = a.user_id AND a.subject_id = ?
        WHERE e.subject_id = ? AND u.role = 'student'
        GROUP BY u.id, u.username, u.full_name, u.email
        ORDER BY u.full_name, u.username
    """, (subject_id, subject_id))
    
    students = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    return jsonify({
        'students': students,
        'count': len(students)
    })

@api_bp.route('/assignments', methods=['POST'])
@require_api_key
def create_assignment():
    """Create a new assignment"""
    data = request.get_json()
    
    required_fields = ['name', 'subject_id', 'student_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO assignments (name, subject_id, user_id, grade)
            VALUES (?, ?, ?, ?)
        """, (data['name'], data['subject_id'], data['student_id'], data.get('grade')))
        
        assignment_id = cur.lastrowid
        conn.commit()
        
        return jsonify({
            'message': 'Assignment created successfully',
            'assignment_id': assignment_id
        }), 201
    
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@api_bp.route('/assignments/<int:assignment_id>', methods=['PUT'])
@require_api_key
def update_assignment(assignment_id):
    """Update an assignment"""
    data = request.get_json()
    
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # Build update query dynamically
    update_fields = []
    values = []
    
    for field in ['name', 'grade']:
        if field in data:
            update_fields.append(f"{field} = ?")
            values.append(data[field])
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    values.append(assignment_id)
    
    try:
        cur.execute(f"""
            UPDATE assignments 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, values)
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Assignment not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Assignment updated successfully'})
    
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@api_bp.route('/analytics/student/<int:student_id>', methods=['GET'])
@require_api_key
def get_student_analytics(student_id):
    """Get analytics data for a specific student"""
    try:
        from advanced_analytics import analytics
        
        prediction = analytics.predict_student_performance(student_id)
        attendance_analysis = analytics.analyze_attendance_patterns(student_id=student_id)
        
        return jsonify({
            'student_id': student_id,
            'performance_prediction': prediction,
            'attendance_analysis': attendance_analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api-keys', methods=['POST'])
@require_api_key
def create_api_key():
    """Create a new API key (admin only)"""
    # Check if current API key has admin permissions
    if g.api_key_info.get('permissions') != 'all' and 'admin' not in g.api_key_info.get('permissions', ''):
        return jsonify({'error': 'Admin permissions required'}), 403
    
    data = request.get_json()
    name = data.get('name', 'Unnamed API Key')
    permissions = data.get('permissions', 'read')
    expires_days = data.get('expires_days', 365)
    
    key_id, secret, key_hash = generate_api_key()
    expires_at = datetime.now() + timedelta(days=expires_days)
    
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO api_keys (key_id, key_hash, user_id, name, permissions, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key_id, key_hash, g.api_key_info['user_id'], name, permissions, expires_at))
        
        conn.commit()
        
        return jsonify({
            'message': 'API key created successfully',
            'key_id': key_id,
            'secret': secret,
            'expires_at': expires_at.isoformat(),
            'usage_note': 'Store the secret securely. Use format: Authorization: Bearer key_id:secret'
        }), 201
    
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Error handlers
@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@api_bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Initialize API tables when module is imported
init_api_tables()

def register_api(app):
    """Register API blueprint with Flask app"""
    app.register_blueprint(api_bp)