"""
Real-time Features Module
WebSocket-based real-time notifications and updates
"""

from flask import Blueprint, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import sqlite3
import os
from datetime import datetime
import json
from typing import Dict, List, Optional

# WebSocket configuration
realtime_bp = Blueprint('realtime', __name__)
socketio = SocketIO(cors_allowed_origins="*", logger=True, engineio_logger=True)

DATABASE = os.path.join(os.path.dirname(__file__), 'school.db')

# In-memory storage for active connections
active_connections: Dict[str, Dict] = {}  # session_id -> {user_id, role, rooms}
room_members: Dict[str, List[str]] = {}   # room_id -> [session_ids]

def init_realtime_tables():
    """Initialize real-time related tables"""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # Notification templates
    cur.execute('''CREATE TABLE IF NOT EXISTS notification_templates (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        title_template TEXT,
        message_template TEXT,
        type TEXT, -- 'grade', 'assignment', 'attendance', 'announcement'
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # User notifications
    cur.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        title TEXT,
        message TEXT,
        type TEXT,
        data TEXT, -- JSON data
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        read_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Real-time events log
    cur.execute('''CREATE TABLE IF NOT EXISTS realtime_events (
        id INTEGER PRIMARY KEY,
        event_type TEXT,
        user_id INTEGER,
        room_id TEXT,
        data TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Insert default notification templates
    templates = [
        ('new_grade', 'New Grade Posted', 'You received a grade of {grade}% for {assignment_name} in {subject_name}', 'grade'),
        ('assignment_due', 'Assignment Due Soon', 'Assignment "{assignment_name}" in {subject_name} is due in {days_remaining} days', 'assignment'),
        ('attendance_marked', 'Attendance Marked', 'Your attendance for {subject_name} on {date} has been marked as {status}', 'attendance'),
        ('new_assignment', 'New Assignment Posted', 'New assignment "{assignment_name}" has been posted in {subject_name}', 'assignment'),
        ('system_announcement', 'System Announcement', '{message}', 'announcement'),
        ('parent_notification', 'Student Update', 'Update for {student_name}: {message}', 'parent')
    ]
    
    for template in templates:
        cur.execute("""
            INSERT OR IGNORE INTO notification_templates (name, title_template, message_template, type)
            VALUES (?, ?, ?, ?)
        """, template)
    
    conn.commit()
    conn.close()

class NotificationService:
    @staticmethod
    def create_notification(user_id: int, template_name: str, data: Dict) -> int:
        """Create a new notification from template"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get template
        cur.execute("""
            SELECT title_template, message_template, type 
            FROM notification_templates 
            WHERE name = ? AND is_active = 1
        """, (template_name,))
        
        template = cur.fetchone()
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Format message using data
        try:
            title = template['title_template'].format(**data)
            message = template['message_template'].format(**data)
        except KeyError as e:
            raise ValueError(f"Missing template data: {e}")
        
        # Insert notification
        cur.execute("""
            INSERT INTO notifications (user_id, title, message, type, data)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, title, message, template['type'], json.dumps(data)))
        
        notification_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        return notification_id
    
    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False, limit: int = 50) -> List[Dict]:
        """Get notifications for a user"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = """
            SELECT id, title, message, type, data, is_read, created_at, read_at
            FROM notifications 
            WHERE user_id = ?
        """
        params = [user_id]
        
        if unread_only:
            query += " AND is_read = 0"
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        notifications = [dict(row) for row in cur.fetchall()]
        
        # Parse JSON data
        for notification in notifications:
            if notification['data']:
                notification['data'] = json.loads(notification['data'])
        
        conn.close()
        return notifications
    
    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE notifications 
            SET is_read = 1, read_at = datetime('now')
            WHERE id = ? AND user_id = ?
        """, (notification_id, user_id))
        
        success = cur.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """Get count of unread notifications"""
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,))
        count = cur.fetchone()[0]
        conn.close()
        
        return count

class RealtimeService:
    @staticmethod
    def emit_to_user(user_id: int, event: str, data: Dict):
        """Send real-time event to specific user"""
        user_sessions = [sid for sid, info in active_connections.items() if info['user_id'] == user_id]
        
        for session_id in user_sessions:
            socketio.emit(event, data, room=session_id)
        
        # Log event
        RealtimeService.log_event(event, user_id, f"user_{user_id}", data)
    
    @staticmethod
    def emit_to_room(room_id: str, event: str, data: Dict, exclude_user: Optional[int] = None):
        """Send real-time event to all users in a room"""
        if room_id in room_members:
            for session_id in room_members[room_id]:
                if exclude_user:
                    session_info = active_connections.get(session_id)
                    if session_info and session_info['user_id'] == exclude_user:
                        continue
                
                socketio.emit(event, data, room=session_id)
        
        # Log event
        RealtimeService.log_event(event, None, room_id, data)
    
    @staticmethod
    def emit_to_role(role: str, event: str, data: Dict):
        """Send real-time event to all users with specific role"""
        role_sessions = [sid for sid, info in active_connections.items() if info['role'] == role]
        
        for session_id in role_sessions:
            socketio.emit(event, data, room=session_id)
        
        # Log event
        RealtimeService.log_event(event, None, f"role_{role}", data)
    
    @staticmethod
    def log_event(event_type: str, user_id: Optional[int], room_id: str, data: Dict):
        """Log real-time event"""
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO realtime_events (event_type, user_id, room_id, data)
            VALUES (?, ?, ?, ?)
        """, (event_type, user_id, room_id, json.dumps(data)))
        
        conn.commit()
        conn.close()

# WebSocket Events
@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection"""
    # In a real app, you'd validate the session here
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    if not user_id:
        print("Unauthorized connection attempt")
        disconnect()
        return False
    
    session_id = request.sid
    active_connections[session_id] = {
        'user_id': user_id,
        'role': user_role,
        'rooms': [],
        'connected_at': datetime.now()
    }
    
    # Join user's personal room
    join_room(f"user_{user_id}")
    
    # Join role-based room
    join_room(f"role_{user_role}")
    
    # Send current unread notifications count
    unread_count = NotificationService.get_unread_count(user_id)
    emit('notification_count', {'count': unread_count})
    
    print(f"User {user_id} ({user_role}) connected with session {session_id}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    session_id = request.sid
    
    if session_id in active_connections:
        user_info = active_connections[session_id]
        
        # Leave all rooms
        for room in user_info['rooms']:
            leave_room(room)
            if room in room_members:
                room_members[room].remove(session_id)
                if not room_members[room]:
                    del room_members[room]
        
        # Remove from active connections
        del active_connections[session_id]
        
        print(f"User {user_info['user_id']} disconnected")

@socketio.on('join_subject')
def handle_join_subject(data):
    """Join subject-specific room"""
    subject_id = data.get('subject_id')
    if not subject_id:
        return
    
    session_id = request.sid
    room_id = f"subject_{subject_id}"
    
    join_room(room_id)
    
    if session_id in active_connections:
        active_connections[session_id]['rooms'].append(room_id)
    
    if room_id not in room_members:
        room_members[room_id] = []
    room_members[room_id].append(session_id)
    
    emit('joined_subject', {'subject_id': subject_id})

@socketio.on('leave_subject')
def handle_leave_subject(data):
    """Leave subject-specific room"""
    subject_id = data.get('subject_id')
    if not subject_id:
        return
    
    session_id = request.sid
    room_id = f"subject_{subject_id}"
    
    leave_room(room_id)
    
    if session_id in active_connections:
        if room_id in active_connections[session_id]['rooms']:
            active_connections[session_id]['rooms'].remove(room_id)
    
    if room_id in room_members and session_id in room_members[room_id]:
        room_members[room_id].remove(session_id)
        if not room_members[room_id]:
            del room_members[room_id]
    
    emit('left_subject', {'subject_id': subject_id})

@socketio.on('mark_notification_read')
def handle_mark_notification_read(data):
    """Mark notification as read"""
    notification_id = data.get('notification_id')
    user_id = session.get('user_id')
    
    if notification_id and user_id:
        success = NotificationService.mark_as_read(notification_id, user_id)
        if success:
            unread_count = NotificationService.get_unread_count(user_id)
            emit('notification_count', {'count': unread_count})
            emit('notification_read', {'notification_id': notification_id})

@socketio.on('get_notifications')
def handle_get_notifications(data):
    """Get user notifications"""
    user_id = session.get('user_id')
    unread_only = data.get('unread_only', False)
    limit = data.get('limit', 20)
    
    if user_id:
        notifications = NotificationService.get_user_notifications(user_id, unread_only, limit)
        emit('notifications_list', {'notifications': notifications})

# Helper functions for triggering real-time events

def notify_new_grade(student_id: int, assignment_name: str, grade: float, subject_name: str):
    """Trigger real-time notification for new grade"""
    data = {
        'assignment_name': assignment_name,
        'grade': grade,
        'subject_name': subject_name
    }
    
    # Create persistent notification
    notification_id = NotificationService.create_notification(student_id, 'new_grade', data)
    
    # Send real-time notification
    RealtimeService.emit_to_user(student_id, 'new_grade', {
        'notification_id': notification_id,
        'assignment_name': assignment_name,
        'grade': grade,
        'subject_name': subject_name,
        'timestamp': datetime.now().isoformat()
    })

def notify_assignment_created(subject_id: int, assignment_name: str, teacher_name: str):
    """Notify students about new assignment"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get subject name
    cur.execute("SELECT name FROM subjects WHERE id = ?", (subject_id,))
    subject = cur.fetchone()
    subject_name = subject['name'] if subject else 'Unknown Subject'
    
    # Get enrolled students
    cur.execute("""
        SELECT u.id FROM users u
        JOIN enrollments e ON u.id = e.user_id
        WHERE e.subject_id = ? AND u.role = 'student'
    """, (subject_id,))
    
    students = cur.fetchall()
    conn.close()
    
    data = {
        'assignment_name': assignment_name,
        'subject_name': subject_name,
        'teacher_name': teacher_name
    }
    
    for student in students:
        # Create notification
        notification_id = NotificationService.create_notification(student['id'], 'new_assignment', data)
        
        # Send real-time update
        RealtimeService.emit_to_user(student['id'], 'new_assignment', {
            'notification_id': notification_id,
            **data,
            'timestamp': datetime.now().isoformat()
        })
    
    # Also notify subject room
    RealtimeService.emit_to_room(f"subject_{subject_id}", 'assignment_created', {
        'assignment_name': assignment_name,
        'teacher_name': teacher_name,
        'timestamp': datetime.now().isoformat()
    })

def notify_attendance_marked(student_id: int, subject_name: str, date: str, present: bool):
    """Notify about attendance marking"""
    data = {
        'subject_name': subject_name,
        'date': date,
        'status': 'Present' if present else 'Absent'
    }
    
    notification_id = NotificationService.create_notification(student_id, 'attendance_marked', data)
    
    RealtimeService.emit_to_user(student_id, 'attendance_updated', {
        'notification_id': notification_id,
        'subject_name': subject_name,
        'date': date,
        'present': present,
        'timestamp': datetime.now().isoformat()
    })

def broadcast_system_announcement(message: str, target_role: str = None):
    """Broadcast system announcement"""
    data = {'message': message}
    
    if target_role:
        # Notify specific role
        RealtimeService.emit_to_role(target_role, 'system_announcement', {
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Create notifications for all users with that role
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE role = ?", (target_role,))
        users = cur.fetchall()
        conn.close()
        
        for user in users:
            NotificationService.create_notification(user[0], 'system_announcement', data)
    else:
        # Broadcast to all connected users
        socketio.emit('system_announcement', {
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

def get_active_users_count():
    """Get count of currently active users"""
    return len(active_connections)

def get_room_members_count(room_id: str):
    """Get count of members in a specific room"""
    return len(room_members.get(room_id, []))

# Initialize tables when module is imported
init_realtime_tables()

def init_socketio(app):
    """Initialize SocketIO with Flask app"""
    socketio.init_app(app, async_mode='threading')