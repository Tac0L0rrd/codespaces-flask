"""
LMS Integration Module
Compatibility with external Learning Management Systems (Moodle, Canvas, Blackboard)
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
import sqlite3
import os
import requests
from datetime import datetime, timedelta
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Union
import hashlib
import hmac
import base64
from urllib.parse import urlencode, parse_qs
import jwt

lms_bp = Blueprint('lms', __name__, url_prefix='/lms')
DATABASE = os.path.join(os.path.dirname(__file__), 'school.db')

def init_lms_tables():
    """Initialize LMS integration tables"""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # LMS configurations
    cur.execute('''CREATE TABLE IF NOT EXISTS lms_configurations (
        id INTEGER PRIMARY KEY,
        lms_type TEXT, -- 'moodle', 'canvas', 'blackboard'
        name TEXT,
        base_url TEXT,
        api_key TEXT,
        api_secret TEXT,
        additional_config TEXT, -- JSON for extra settings
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # LMS user mappings
    cur.execute('''CREATE TABLE IF NOT EXISTS lms_user_mappings (
        id INTEGER PRIMARY KEY,
        local_user_id INTEGER,
        lms_config_id INTEGER,
        external_user_id TEXT,
        external_username TEXT,
        sync_enabled BOOLEAN DEFAULT 1,
        last_sync TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (local_user_id) REFERENCES users(id),
        FOREIGN KEY (lms_config_id) REFERENCES lms_configurations(id),
        UNIQUE(local_user_id, lms_config_id)
    )''')
    
    # LMS course mappings
    cur.execute('''CREATE TABLE IF NOT EXISTS lms_course_mappings (
        id INTEGER PRIMARY KEY,
        local_subject_id INTEGER,
        lms_config_id INTEGER,
        external_course_id TEXT,
        external_course_code TEXT,
        sync_enabled BOOLEAN DEFAULT 1,
        last_sync TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (local_subject_id) REFERENCES subjects(id),
        FOREIGN KEY (lms_config_id) REFERENCES lms_configurations(id),
        UNIQUE(local_subject_id, lms_config_id)
    )''')
    
    # LMS sync logs
    cur.execute('''CREATE TABLE IF NOT EXISTS lms_sync_logs (
        id INTEGER PRIMARY KEY,
        lms_config_id INTEGER,
        sync_type TEXT, -- 'users', 'courses', 'grades', 'assignments'
        status TEXT, -- 'success', 'error', 'partial'
        records_processed INTEGER DEFAULT 0,
        records_succeeded INTEGER DEFAULT 0,
        records_failed INTEGER DEFAULT 0,
        error_details TEXT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (lms_config_id) REFERENCES lms_configurations(id)
    )''')
    
    # LTI integrations
    cur.execute('''CREATE TABLE IF NOT EXISTS lti_integrations (
        id INTEGER PRIMARY KEY,
        consumer_key TEXT UNIQUE,
        shared_secret TEXT,
        name TEXT,
        description TEXT,
        launch_url TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

class MoodleIntegration:
    """Integration with Moodle LMS"""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.api_url = f"{self.base_url}/webservice/rest/server.php"
    
    def make_request(self, function: str, params: Dict = None) -> Dict:
        """Make API request to Moodle"""
        data = {
            'wstoken': self.api_token,
            'wsfunction': function,
            'moodlewsrestformat': 'json'
        }
        
        if params:
            data.update(params)
        
        try:
            response = requests.post(self.api_url, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Moodle API error: {str(e)}")
    
    def get_users(self, criteria: Dict = None) -> List[Dict]:
        """Get users from Moodle"""
        params = {}
        if criteria:
            params['criteria'] = [{'key': k, 'value': v} for k, v in criteria.items()]
        
        result = self.make_request('core_user_get_users', params)
        return result.get('users', [])
    
    def get_courses(self) -> List[Dict]:
        """Get courses from Moodle"""
        result = self.make_request('core_course_get_courses')
        return result if isinstance(result, list) else []
    
    def get_course_enrollments(self, course_id: int) -> List[Dict]:
        """Get enrollments for a specific course"""
        params = {'courseid': course_id}
        result = self.make_request('core_enrol_get_enrolled_users', params)
        return result if isinstance(result, list) else []
    
    def create_user(self, user_data: Dict) -> Dict:
        """Create user in Moodle"""
        params = {'users': [user_data]}
        return self.make_request('core_user_create_users', params)
    
    def update_grades(self, course_id: int, item_id: int, grades: List[Dict]) -> Dict:
        """Update grades in Moodle"""
        params = {
            'source': 'mod/assign',
            'courseid': course_id,
            'component': 'mod_assign',
            'itemid': item_id,
            'grades': grades
        }
        return self.make_request('core_grades_update_grades', params)

class CanvasIntegration:
    """Integration with Canvas LMS"""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def make_request(self, endpoint: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Union[Dict, List]:
        """Make API request to Canvas"""
        url = f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Canvas API error: {str(e)}")
    
    def get_courses(self) -> List[Dict]:
        """Get courses from Canvas"""
        return self.make_request('courses')
    
    def get_course_users(self, course_id: int) -> List[Dict]:
        """Get users enrolled in a course"""
        return self.make_request(f'courses/{course_id}/users')
    
    def get_assignments(self, course_id: int) -> List[Dict]:
        """Get assignments for a course"""
        return self.make_request(f'courses/{course_id}/assignments')
    
    def create_assignment(self, course_id: int, assignment_data: Dict) -> Dict:
        """Create assignment in Canvas"""
        return self.make_request(f'courses/{course_id}/assignments', 'POST', data={'assignment': assignment_data})
    
    def update_grade(self, course_id: int, assignment_id: int, user_id: int, grade_data: Dict) -> Dict:
        """Update grade for assignment"""
        endpoint = f'courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}'
        return self.make_request(endpoint, 'PUT', data={'submission': grade_data})
    
    def get_gradebook(self, course_id: int) -> Dict:
        """Get gradebook data"""
        return self.make_request(f'courses/{course_id}/gradebook_history')

class BlackboardIntegration:
    """Integration with Blackboard LMS"""
    
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires = None
    
    def authenticate(self) -> str:
        """Authenticate and get access token"""
        auth_url = f"{self.base_url}/learn/api/public/v1/oauth2/token"
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(auth_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
            
            return self.access_token
        except requests.RequestException as e:
            raise Exception(f"Blackboard authentication error: {str(e)}")
    
    def make_request(self, endpoint: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Union[Dict, List]:
        """Make API request to Blackboard"""
        if not self.access_token or datetime.now() >= self.token_expires:
            self.authenticate()
        
        url = f"{self.base_url}/learn/api/public/v1/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Blackboard API error: {str(e)}")
    
    def get_courses(self) -> List[Dict]:
        """Get courses from Blackboard"""
        result = self.make_request('courses')
        return result.get('results', [])
    
    def get_course_memberships(self, course_id: str) -> List[Dict]:
        """Get course memberships"""
        result = self.make_request(f'courses/{course_id}/users')
        return result.get('results', [])
    
    def get_gradebook_columns(self, course_id: str) -> List[Dict]:
        """Get gradebook columns"""
        result = self.make_request(f'courses/{course_id}/gradebook/columns')
        return result.get('results', [])
    
    def update_grade(self, course_id: str, column_id: str, user_id: str, grade_data: Dict) -> Dict:
        """Update grade"""
        endpoint = f'courses/{course_id}/gradebook/columns/{column_id}/users/{user_id}'
        return self.make_request(endpoint, 'PATCH', data=grade_data)

class LTIProvider:
    """LTI (Learning Tools Interoperability) Provider"""
    
    @staticmethod
    def validate_lti_request(request_data: Dict, shared_secret: str) -> bool:
        """Validate LTI launch request"""
        # Get OAuth signature
        oauth_signature = request_data.pop('oauth_signature', None)
        if not oauth_signature:
            return False
        
        # Build base string
        params = '&'.join([f"{k}={v}" for k, v in sorted(request_data.items())])
        base_string = f"POST&{request.url}&{params}"
        
        # Calculate signature
        key = f"{shared_secret}&"
        signature = hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
        expected_signature = base64.b64encode(signature).decode()
        
        return hmac.compare_digest(oauth_signature, expected_signature)
    
    @staticmethod
    def extract_user_info(lti_data: Dict) -> Dict:
        """Extract user information from LTI launch"""
        return {
            'user_id': lti_data.get('user_id'),
            'username': lti_data.get('ext_user_username', lti_data.get('lis_person_sourcedid')),
            'full_name': lti_data.get('lis_person_name_full'),
            'email': lti_data.get('lis_person_contact_email_primary'),
            'role': lti_data.get('roles', '').lower()
        }

class LMSSyncService:
    """Service for synchronizing data with external LMS"""
    
    @staticmethod
    def get_lms_integration(lms_config_id: int) -> Optional[Union[MoodleIntegration, CanvasIntegration, BlackboardIntegration]]:
        """Get LMS integration instance"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM lms_configurations WHERE id = ? AND is_active = 1", (lms_config_id,))
        config = cur.fetchone()
        conn.close()
        
        if not config:
            return None
        
        additional_config = json.loads(config['additional_config'] or '{}')
        
        if config['lms_type'] == 'moodle':
            return MoodleIntegration(config['base_url'], config['api_key'])
        elif config['lms_type'] == 'canvas':
            return CanvasIntegration(config['base_url'], config['api_key'])
        elif config['lms_type'] == 'blackboard':
            return BlackboardIntegration(config['base_url'], config['api_key'], config['api_secret'])
        
        return None
    
    @staticmethod
    def sync_users(lms_config_id: int) -> Dict:
        """Sync users from external LMS"""
        lms = LMSSyncService.get_lms_integration(lms_config_id)
        if not lms:
            return {'error': 'LMS configuration not found'}
        
        # Start sync log
        sync_log_id = LMSSyncService.start_sync_log(lms_config_id, 'users')
        
        try:
            if isinstance(lms, MoodleIntegration):
                external_users = lms.get_users()
            elif isinstance(lms, CanvasIntegration):
                # Get users from all courses
                courses = lms.get_courses()
                external_users = []
                for course in courses:
                    external_users.extend(lms.get_course_users(course['id']))
            elif isinstance(lms, BlackboardIntegration):
                # Get users from all courses
                courses = lms.get_courses()
                external_users = []
                for course in courses:
                    external_users.extend(lms.get_course_memberships(course['id']))
            
            # Process users
            processed = succeeded = failed = 0
            errors = []
            
            for ext_user in external_users:
                processed += 1
                try:
                    # Map external user to local user
                    local_user_data = LMSSyncService.map_external_user(ext_user, lms_config_id)
                    
                    if local_user_data:
                        # Create or update local user
                        success = LMSSyncService.create_or_update_user(local_user_data, lms_config_id, ext_user)
                        if success:
                            succeeded += 1
                        else:
                            failed += 1
                            errors.append(f"Failed to sync user {ext_user.get('id', 'unknown')}")
                    else:
                        failed += 1
                        errors.append(f"Could not map external user {ext_user.get('id', 'unknown')}")
                
                except Exception as e:
                    failed += 1
                    errors.append(f"Error processing user {ext_user.get('id', 'unknown')}: {str(e)}")
            
            # Complete sync log
            LMSSyncService.complete_sync_log(
                sync_log_id, 'success' if failed == 0 else 'partial',
                processed, succeeded, failed, '; '.join(errors[:10])  # Limit error details
            )
            
            return {
                'status': 'success' if failed == 0 else 'partial',
                'processed': processed,
                'succeeded': succeeded,
                'failed': failed,
                'errors': errors[:5]  # Return first 5 errors
            }
        
        except Exception as e:
            LMSSyncService.complete_sync_log(sync_log_id, 'error', 0, 0, 0, str(e))
            return {'error': str(e)}
    
    @staticmethod
    def sync_courses(lms_config_id: int) -> Dict:
        """Sync courses from external LMS"""
        lms = LMSSyncService.get_lms_integration(lms_config_id)
        if not lms:
            return {'error': 'LMS configuration not found'}
        
        sync_log_id = LMSSyncService.start_sync_log(lms_config_id, 'courses')
        
        try:
            if isinstance(lms, MoodleIntegration):
                external_courses = lms.get_courses()
            elif isinstance(lms, CanvasIntegration):
                external_courses = lms.get_courses()
            elif isinstance(lms, BlackboardIntegration):
                external_courses = lms.get_courses()
            
            processed = succeeded = failed = 0
            errors = []
            
            for ext_course in external_courses:
                processed += 1
                try:
                    # Map and sync course
                    success = LMSSyncService.sync_course_data(ext_course, lms_config_id)
                    if success:
                        succeeded += 1
                    else:
                        failed += 1
                        errors.append(f"Failed to sync course {ext_course.get('id', 'unknown')}")
                
                except Exception as e:
                    failed += 1
                    errors.append(f"Error processing course {ext_course.get('id', 'unknown')}: {str(e)}")
            
            LMSSyncService.complete_sync_log(
                sync_log_id, 'success' if failed == 0 else 'partial',
                processed, succeeded, failed, '; '.join(errors[:10])
            )
            
            return {
                'status': 'success' if failed == 0 else 'partial',
                'processed': processed,
                'succeeded': succeeded,
                'failed': failed,
                'errors': errors[:5]
            }
        
        except Exception as e:
            LMSSyncService.complete_sync_log(sync_log_id, 'error', 0, 0, 0, str(e))
            return {'error': str(e)}
    
    @staticmethod
    def start_sync_log(lms_config_id: int, sync_type: str) -> int:
        """Start sync log entry"""
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO lms_sync_logs (lms_config_id, sync_type, status)
            VALUES (?, ?, 'running')
        """, (lms_config_id, sync_type))
        
        sync_log_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        return sync_log_id
    
    @staticmethod
    def complete_sync_log(sync_log_id: int, status: str, processed: int, succeeded: int, failed: int, errors: str):
        """Complete sync log entry"""
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE lms_sync_logs 
            SET status = ?, records_processed = ?, records_succeeded = ?, 
                records_failed = ?, error_details = ?, completed_at = datetime('now')
            WHERE id = ?
        """, (status, processed, succeeded, failed, errors, sync_log_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def map_external_user(ext_user: Dict, lms_config_id: int) -> Optional[Dict]:
        """Map external user data to local user format"""
        # This would be customized based on LMS type and institution needs
        if 'email' in ext_user or 'username' in ext_user:
            return {
                'username': ext_user.get('username', ext_user.get('email', '').split('@')[0]),
                'full_name': ext_user.get('fullname', ext_user.get('name', '')),
                'email': ext_user.get('email', ''),
                'role': LMSSyncService.map_external_role(ext_user.get('role', 'student'))
            }
        return None
    
    @staticmethod
    def map_external_role(external_role: str) -> str:
        """Map external role to local role"""
        role_mappings = {
            'teacher': 'teacher',
            'instructor': 'teacher',
            'student': 'student',
            'learner': 'student',
            'admin': 'admin',
            'administrator': 'admin'
        }
        return role_mappings.get(external_role.lower(), 'student')
    
    @staticmethod
    def create_or_update_user(user_data: Dict, lms_config_id: int, ext_user: Dict) -> bool:
        """Create or update local user and mapping"""
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        try:
            # Check if user exists
            cur.execute("SELECT id FROM users WHERE username = ?", (user_data['username'],))
            existing_user = cur.fetchone()
            
            if existing_user:
                user_id = existing_user[0]
                # Update user
                cur.execute("""
                    UPDATE users SET full_name = ?, email = ?, role = ?
                    WHERE id = ?
                """, (user_data['full_name'], user_data['email'], user_data['role'], user_id))
            else:
                # Create user
                cur.execute("""
                    INSERT INTO users (username, full_name, email, role, password_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_data['username'], user_data['full_name'], user_data['email'], 
                      user_data['role'], 'external_lms_user'))
                user_id = cur.lastrowid
            
            # Create or update mapping
            cur.execute("""
                INSERT OR REPLACE INTO lms_user_mappings 
                (local_user_id, lms_config_id, external_user_id, external_username, last_sync)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (user_id, lms_config_id, str(ext_user.get('id', '')), ext_user.get('username', '')))
            
            conn.commit()
            return True
        
        except sqlite3.Error:
            return False
        finally:
            conn.close()
    
    @staticmethod
    def sync_course_data(ext_course: Dict, lms_config_id: int) -> bool:
        """Sync course data"""
        # Similar implementation for courses
        # This would be expanded based on requirements
        return True

# Flask Routes
@lms_bp.route('/configurations', methods=['GET'])
def get_lms_configurations():
    """Get all LMS configurations"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT id, lms_type, name, base_url, is_active, created_at FROM lms_configurations ORDER BY name")
    configs = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    return jsonify({'configurations': configs})

@lms_bp.route('/sync/<int:config_id>/users', methods=['POST'])
def sync_users_endpoint(config_id):
    """Trigger user sync"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    result = LMSSyncService.sync_users(config_id)
    return jsonify(result)

@lms_bp.route('/sync/<int:config_id>/courses', methods=['POST'])
def sync_courses_endpoint(config_id):
    """Trigger course sync"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    result = LMSSyncService.sync_courses(config_id)
    return jsonify(result)

@lms_bp.route('/lti/launch', methods=['POST'])
def lti_launch():
    """Handle LTI launch request"""
    # Get consumer key
    consumer_key = request.form.get('oauth_consumer_key')
    
    if not consumer_key:
        return "Missing consumer key", 400
    
    # Get LTI integration
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM lti_integrations WHERE consumer_key = ? AND is_active = 1", (consumer_key,))
    lti_config = cur.fetchone()
    conn.close()
    
    if not lti_config:
        return "Invalid consumer key", 400
    
    # Validate LTI request
    if not LTIProvider.validate_lti_request(dict(request.form), lti_config['shared_secret']):
        return "Invalid LTI signature", 400
    
    # Extract user info
    user_info = LTIProvider.extract_user_info(dict(request.form))
    
    # Create session or authenticate user
    session['lti_user'] = user_info
    session['lti_launch'] = True
    
    # Redirect to appropriate dashboard
    role = user_info.get('role', 'student')
    if 'instructor' in role or 'teacher' in role:
        return redirect(url_for('teacher_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

# Initialize tables when module is imported
init_lms_tables()

def register_lms_routes(app):
    """Register LMS blueprint with Flask app"""
    app.register_blueprint(lms_bp)