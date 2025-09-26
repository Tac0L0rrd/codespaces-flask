"""
Parent Portal Module
Provides parent access to their children's academic information
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class ParentPortal:
    def __init__(self):
        self.database = os.path.join(os.path.dirname(__file__), 'school.db')
        self.init_parent_tables()
    
    def init_parent_tables(self):
        """Initialize parent-related tables"""
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        
        # Parent-student relationships table
        cur.execute('''CREATE TABLE IF NOT EXISTS parent_student_relationships (
            id INTEGER PRIMARY KEY,
            parent_id INTEGER,
            student_id INTEGER,
            relationship TEXT DEFAULT 'parent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES users(id),
            FOREIGN KEY (student_id) REFERENCES users(id),
            UNIQUE(parent_id, student_id)
        )''')
        
        # Parent notifications table
        cur.execute('''CREATE TABLE IF NOT EXISTS parent_notifications (
            id INTEGER PRIMARY KEY,
            parent_id INTEGER,
            student_id INTEGER,
            notification_type TEXT,
            title TEXT,
            message TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES users(id),
            FOREIGN KEY (student_id) REFERENCES users(id)
        )''')
        
        # Update users table to include parent role if needed
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cur.fetchone():
            # Add parent contact info columns if they don't exist
            cur.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cur.fetchall()]
            
            if 'email' not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
            if 'phone' not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            if 'full_name' not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
        
        # Parent-teacher messages table
        cur.execute('''CREATE TABLE IF NOT EXISTS parent_teacher_messages (
            id INTEGER PRIMARY KEY,
            parent_id INTEGER,
            teacher_id INTEGER,
            student_id INTEGER,
            subject_id INTEGER,
            message TEXT,
            sender_role TEXT DEFAULT 'parent',
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES users(id),
            FOREIGN KEY (teacher_id) REFERENCES users(id),
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )''')
        
        # Add is_read column if it doesn't exist
        try:
            cur.execute("ALTER TABLE parent_teacher_messages ADD COLUMN is_read BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        conn.commit()
        conn.close()
    
    def create_parent_account(self, username: str, password: str, full_name: str, 
                            email: str, phone: str = None) -> int:
        """Create a new parent account"""
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO users (username, password, role, full_name, email, phone) 
                VALUES (?, ?, 'parent', ?, ?, ?)
            """, (username, password, full_name, email, phone))
            
            parent_id = cur.lastrowid
            conn.commit()
            return parent_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def link_parent_to_student(self, parent_id: int, student_id: int, 
                              relationship: str = 'parent') -> bool:
        """Link a parent to a student"""
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO parent_student_relationships (parent_id, student_id, relationship) 
                VALUES (?, ?, ?)
            """, (parent_id, student_id, relationship))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_parent_children(self, parent_id: int) -> List[Dict]:
        """Get all children linked to a parent"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT u.*, psr.relationship 
            FROM users u
            JOIN parent_student_relationships psr ON u.id = psr.student_id
            WHERE psr.parent_id = ? AND u.role = 'student'
            ORDER BY u.full_name, u.username
        """, (parent_id,))
        
        children = [dict(row) for row in cur.fetchall()]
        conn.close()
        return children
    
    def get_student_grades(self, student_id: int, subject_id: int = None) -> List[Dict]:
        """Get grades for a specific student"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = """
            SELECT a.*, s.name as subject_name, u.full_name as teacher_name, u.username as teacher_username
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE a.user_id = ?
        """
        params = [student_id]
        
        if subject_id:
            query += " AND a.subject_id = ?"
            params.append(subject_id)
        
        query += " ORDER BY a.id DESC"
        
        cur.execute(query, params)
        grades = [dict(row) for row in cur.fetchall()]
        conn.close()
        return grades
    
    def get_student_attendance(self, student_id: int, days: int = 30) -> List[Dict]:
        """Get attendance records for a student"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cur.execute("""
            SELECT att.*, s.name as subject_name
            FROM attendance att
            JOIN subjects s ON att.subject_id = s.id
            WHERE att.user_id = ? AND att.date >= ?
            ORDER BY att.date DESC
        """, (student_id, start_date))
        
        attendance = [dict(row) for row in cur.fetchall()]
        conn.close()
        return attendance
    
    def get_student_subjects(self, student_id: int) -> List[Dict]:
        """Get all subjects a student is enrolled in"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.*, 
                   COALESCE(u.full_name, u.username, 'Not assigned') as teacher_name, 
                   u.username as teacher_username, 
                   u.id as teacher_id
            FROM subjects s
            JOIN enrollments e ON s.id = e.subject_id
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE e.user_id = ?
            ORDER BY s.name
        """, (student_id,))
        
        subjects = [dict(row) for row in cur.fetchall()]
        conn.close()
        return subjects
    
    def get_student_progress_summary(self, student_id: int) -> Dict:
        """Get a comprehensive progress summary for a student"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Overall grade average
        cur.execute("""
            SELECT AVG(grade) as overall_average, COUNT(*) as total_assignments
            FROM assignments 
            WHERE user_id = ? AND grade IS NOT NULL AND grade > 0
        """, (student_id,))
        
        overall_stats = dict(cur.fetchone())
        
        # Subject-wise averages
        cur.execute("""
            SELECT s.name as subject_name, AVG(a.grade) as subject_average, 
                   COUNT(a.id) as assignment_count
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.user_id = ? AND a.grade IS NOT NULL AND a.grade > 0
            GROUP BY s.id, s.name
            ORDER BY s.name
        """, (student_id,))
        
        subject_averages = [dict(row) for row in cur.fetchall()]
        
        # Recent attendance rate
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cur.execute("""
            SELECT 
                COUNT(*) as total_days,
                SUM(present) as present_days,
                CAST(SUM(present) AS FLOAT) / COUNT(*) * 100 as attendance_rate
            FROM attendance 
            WHERE user_id = ? AND date >= ?
        """, (student_id, thirty_days_ago))
        
        attendance_stats = dict(cur.fetchone())
        
        conn.close()
        
        return {
            'overall_stats': overall_stats,
            'subject_averages': subject_averages,
            'attendance_stats': attendance_stats
        }
    
    def create_parent_notification(self, parent_id: int, student_id: int, 
                                 notification_type: str, title: str, message: str):
        """Create a notification for a parent"""
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO parent_notifications 
            (parent_id, student_id, notification_type, title, message) 
            VALUES (?, ?, ?, ?, ?)
        """, (parent_id, student_id, notification_type, title, message))
        
        conn.commit()
        conn.close()
    
    def get_parent_notifications(self, parent_id: int, unread_only: bool = False) -> List[Dict]:
        """Get notifications for a parent"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = """
            SELECT pn.*, u.full_name as student_name, u.username as student_username
            FROM parent_notifications pn
            JOIN users u ON pn.student_id = u.id
            WHERE pn.parent_id = ?
        """
        
        if unread_only:
            query += " AND pn.is_read = 0"
        
        query += " ORDER BY pn.created_at DESC"
        
        cur.execute(query, (parent_id,))
        notifications = [dict(row) for row in cur.fetchall()]
        conn.close()
        return notifications
    
    def mark_notification_read(self, notification_id: int, parent_id: int):
        """Mark a notification as read"""
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE parent_notifications 
            SET is_read = 1 
            WHERE id = ? AND parent_id = ?
        """, (notification_id, parent_id))
        
        conn.commit()
        conn.close()
        
    def get_children_info(self, parent_id: int) -> List[Dict]:
        """Get comprehensive information about parent's children"""
        children = self.get_parent_children(parent_id)
        
        for child in children:
            child['progress'] = self.get_student_progress_summary(child['id'])
            child['subjects'] = self.get_student_subjects(child['id'])
            child['recent_grades'] = self.get_student_grades(child['id'])[:5]  # Last 5 grades
            child['teachers'] = self.get_student_teachers(child['id'])
            
        return children
        
    def get_student_teachers(self, student_id: int) -> List[Dict]:
        """Get teachers for a student's subjects"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT u.id as teacher_id, u.username as teacher_name, u.full_name as teacher_full_name, 
                   s.id as subject_id, s.name as subject_name
            FROM enrollments e
            JOIN subjects s ON e.subject_id = s.id
            JOIN users u ON s.teacher_id = u.id
            WHERE e.user_id = ? AND u.role = 'teacher'
        """, (student_id,))
        
        teachers = [dict(row) for row in cur.fetchall()]
        conn.close()
        return teachers
        
    def verify_parent_child_relationship(self, parent_id: int, student_id: int) -> bool:
        """Verify that a parent has access to a specific student"""
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 1 FROM parent_student_relationships 
            WHERE parent_id = ? AND student_id = ?
        """, (parent_id, student_id))
        
        result = cur.fetchone() is not None
        conn.close()
        return result
        
    def get_student_progress_for_parent(self, student_id: int) -> Dict:
        """Get detailed progress information for a specific student"""
        return {
            'student_info': self.get_student_info(student_id),
            'grades': self.get_student_grades(student_id),
            'attendance': self.get_student_attendance(student_id),
            'subjects': self.get_student_subjects(student_id),
            'progress_summary': self.get_student_progress_summary(student_id)
        }
        
    def get_student_info(self, student_id: int) -> Dict:
        """Get basic student information"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users WHERE id = ? AND role = 'student'", (student_id,))
        result = cur.fetchone()
        student = dict(result) if result else None
        conn.close()
        return student
    
    def send_message_to_teacher(self, parent_id: int, teacher_id: int, student_id: int, 
                              subject_id: int, message: str) -> bool:
        """Send a message from parent to teacher"""
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            
            # Create messages table if it doesn't exist
            cur.execute('''CREATE TABLE IF NOT EXISTS parent_teacher_messages (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER,
                teacher_id INTEGER,
                student_id INTEGER,
                subject_id INTEGER,
                message TEXT,
                sender_role TEXT DEFAULT 'parent',
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES users(id),
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )''')
            
            # Insert the message
            cur.execute("""
                INSERT INTO parent_teacher_messages 
                (parent_id, teacher_id, student_id, subject_id, message, sender_role) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (parent_id, teacher_id, student_id, subject_id, message, 'parent'))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
        finally:
            conn.close()
    
    def get_teacher_messages(self, teacher_id: int) -> List[Dict]:
        """Get all messages for a teacher"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT ptm.*, 
                   p.username as parent_name, 
                   p.full_name as parent_full_name,
                   s.username as student_name,
                   s.full_name as student_full_name,
                   subj.name as subject_name,
                   ptm.created_at
            FROM parent_teacher_messages ptm
            JOIN users p ON ptm.parent_id = p.id
            JOIN users s ON ptm.student_id = s.id
            LEFT JOIN subjects subj ON ptm.subject_id = subj.id
            WHERE ptm.teacher_id = ?
            ORDER BY ptm.created_at DESC
        """, (teacher_id,))
        
        messages = [dict(row) for row in cur.fetchall()]
        conn.close()
        return messages
    
    def send_message_to_parent(self, teacher_id: int, parent_id: int, student_id: int, 
                              subject_id: int, message: str) -> bool:
        """Send a message from teacher to parent"""
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            
            # Check if parent_teacher_messages table exists, create if not
            cur.execute('''CREATE TABLE IF NOT EXISTS parent_teacher_messages (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER,
                teacher_id INTEGER,
                student_id INTEGER,
                subject_id INTEGER,
                message TEXT,
                sender_role TEXT DEFAULT 'parent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES users(id),
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )''')
            
            cur.execute('''INSERT INTO parent_teacher_messages 
                          (parent_id, teacher_id, student_id, subject_id, message, sender_role) 
                          VALUES (?, ?, ?, ?, ?, ?)''', 
                          (parent_id, teacher_id, student_id, subject_id, message, 'teacher'))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error sending teacher message: {e}")
            return False
    
    def get_parent_messages(self, parent_id: int) -> List[Dict]:
        """Get all messages for a parent"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT ptm.*, 
                   t.username as teacher_name, 
                   t.full_name as teacher_full_name,
                   s.username as student_name,
                   s.full_name as student_full_name,
                   subj.name as subject_name,
                   ptm.created_at
            FROM parent_teacher_messages ptm
            JOIN users t ON ptm.teacher_id = t.id
            JOIN users s ON ptm.student_id = s.id
            LEFT JOIN subjects subj ON ptm.subject_id = subj.id
            WHERE ptm.parent_id = ?
            ORDER BY ptm.created_at DESC
        """, (parent_id,))
        
        messages = [dict(row) for row in cur.fetchall()]
        conn.close()
        return messages
    
    def delete_message(self, message_id: int, user_id: int, user_role: str) -> bool:
        """Delete a message (only if user is sender or recipient)"""
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            
            # Check if user can delete this message
            if user_role == 'teacher':
                cur.execute("SELECT teacher_id FROM parent_teacher_messages WHERE id = ?", (message_id,))
            else:  # parent
                cur.execute("SELECT parent_id FROM parent_teacher_messages WHERE id = ?", (message_id,))
            
            result = cur.fetchone()
            if not result or result[0] != user_id:
                conn.close()
                return False
            
            # Delete the message
            cur.execute("DELETE FROM parent_teacher_messages WHERE id = ?", (message_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting message: {e}")
            return False
    
    def get_unread_message_count(self, user_id: int, user_role: str) -> int:
        """Get count of unread messages for a user"""
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        
        if user_role == 'teacher':
            cur.execute("""
                SELECT COUNT(*) FROM parent_teacher_messages 
                WHERE teacher_id = ? AND sender_role = 'parent' AND is_read = 0
            """, (user_id,))
        else:  # parent
            cur.execute("""
                SELECT COUNT(*) FROM parent_teacher_messages 
                WHERE parent_id = ? AND sender_role = 'teacher' AND is_read = 0
            """, (user_id,))
        
        count = cur.fetchone()[0]
        conn.close()
        return count
    
    def mark_messages_as_read(self, user_id: int, user_role: str) -> bool:
        """Mark all messages as read for a user"""
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            
            if user_role == 'teacher':
                cur.execute("""
                    UPDATE parent_teacher_messages 
                    SET is_read = 1 
                    WHERE teacher_id = ? AND sender_role = 'parent' AND is_read = 0
                """, (user_id,))
            else:  # parent
                cur.execute("""
                    UPDATE parent_teacher_messages 
                    SET is_read = 1 
                    WHERE parent_id = ? AND sender_role = 'teacher' AND is_read = 0
                """, (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return False

# Global parent portal instance
parent_portal = ParentPortal()

def register_parent_routes(app):
    """Register parent portal routes with Flask app"""
    
    @app.route('/parent_dashboard')
    def parent_dashboard():
        from flask import session, redirect, url_for, render_template
        if 'user_id' not in session or session.get('role') != 'parent':
            return redirect(url_for('login'))
        
        # Get parent's children and their information
        portal = ParentPortal()
        children_data = portal.get_children_info(session['user_id'])
        notifications = portal.get_parent_notifications(session['user_id'])
        
        # Get unread message count
        unread_messages = portal.get_unread_message_count(session['user_id'], 'parent')
        
        return render_template('parent_dashboard.html', 
                             children=children_data,
                             notifications=notifications,
                             unread_messages=unread_messages)
    
    @app.route('/parent_child_progress/<int:student_id>')
    def parent_child_progress(student_id):
        from flask import session, redirect, url_for, render_template
        if 'user_id' not in session or session.get('role') != 'parent':
            return redirect(url_for('login'))
        
        # Verify this parent has access to this student
        portal = ParentPortal()
        if not portal.verify_parent_child_relationship(session['user_id'], student_id):
            return redirect(url_for('parent_dashboard'))
        
        # Get student's progress data
        progress_data = portal.get_student_progress_for_parent(student_id)
        
        return render_template('parent_child_progress.html', 
                             student_data=progress_data)
    
    @app.route('/parent_message_teacher', methods=['GET', 'POST'])
    def parent_message_teacher():
        from flask import session, redirect, url_for, render_template, request, flash
        if 'user_id' not in session or session.get('role') != 'parent':
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            student_id = request.form.get('student_id')
            teacher_id = request.form.get('teacher_id')
            subject_id = request.form.get('subject_id')
            message = request.form.get('message')
            
            # Create message record (you'd need to implement the messaging system)
            portal = ParentPortal()
            success = portal.send_message_to_teacher(
                session['user_id'], teacher_id, student_id, subject_id, message
            )
            
            if success:
                flash('Message sent successfully!', 'success')
            else:
                flash('Failed to send message. Please try again.', 'error')
            
            return redirect(url_for('parent_dashboard'))
        
        # Get children and their teachers for the form
        portal = ParentPortal()
        children_data = portal.get_children_info(session['user_id'])
        
        # Get unread message count
        unread_messages = portal.get_unread_message_count(session['user_id'], 'parent')
        
        return render_template('parent_message_teacher.html', children=children_data, unread_messages=unread_messages)
    
    @app.route('/teacher_messages', methods=['GET', 'POST'])
    def teacher_messages():
        from flask import session, redirect, url_for, render_template, request, flash
        if 'user_id' not in session or session.get('role') != 'teacher':
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            parent_id = request.form.get('parent_id')
            student_id = request.form.get('student_id')
            subject_id = request.form.get('subject_id')
            message = request.form.get('message')
            
            portal = ParentPortal()
            success = portal.send_message_to_parent(
                session['user_id'], parent_id, student_id, subject_id, message
            )
            
            if success:
                flash('Message sent successfully!', 'success')
            else:
                flash('Failed to send message. Please try again.', 'error')
            
            return redirect(url_for('teacher_messages'))
        
        # Get all messages for this teacher
        portal = ParentPortal()
        messages = portal.get_teacher_messages(session['user_id'])
        
        # Mark messages as read when viewed
        portal.mark_messages_as_read(session['user_id'], 'teacher')
        
        # Get teacher's students and their parents for the reply form
        conn = sqlite3.connect(portal.database)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT 
                s.id as student_id, s.username as student_name, s.full_name as student_full_name,
                p.id as parent_id, p.username as parent_name, p.full_name as parent_full_name,
                subj.id as subject_id, subj.name as subject_name
            FROM enrollments e
            JOIN subjects subj ON e.subject_id = subj.id
            JOIN users s ON e.user_id = s.id
            JOIN parent_student_relationships psr ON s.id = psr.student_id
            JOIN users p ON psr.parent_id = p.id
            WHERE subj.teacher_id = ?
        """, (session['user_id'],))
        
        teacher_students = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        # Get unread message count
        unread_messages = portal.get_unread_message_count(session['user_id'], 'teacher')
        
        return render_template('teacher_messages.html', 
                             messages=messages, 
                             teacher_students=teacher_students,
                             unread_messages=unread_messages)
    
    @app.route('/parent_messages')
    def parent_messages():
        from flask import session, redirect, url_for, render_template
        if 'user_id' not in session or session.get('role') != 'parent':
            return redirect(url_for('login'))
        
        # Get all messages for this parent
        portal = ParentPortal()
        messages = portal.get_parent_messages(session['user_id'])
        
        # Mark messages as read when viewed
        portal.mark_messages_as_read(session['user_id'], 'parent')
        
        # Get children data for the compose form
        children_data = portal.get_children_info(session['user_id'])
        
        return render_template('parent_messages.html', messages=messages, children=children_data)
    
    @app.route('/delete_message/<int:message_id>', methods=['POST'])
    def delete_message(message_id):
        from flask import session, redirect, url_for, flash, request
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        portal = ParentPortal()
        success = portal.delete_message(message_id, session['user_id'], session.get('role'))
        
        if success:
            flash('Message deleted successfully!', 'success')
        else:
            flash('Failed to delete message. You can only delete your own messages.', 'error')
        
        # Redirect back to the appropriate messages page
        if session.get('role') == 'teacher':
            return redirect(url_for('teacher_messages'))
        else:
            return redirect(url_for('parent_messages'))