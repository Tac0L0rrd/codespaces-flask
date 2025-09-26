# 🌐 EduBridge API Documentation

## Overview

EduBridge provides a comprehensive RESTful API for external integrations and mobile application development. The API supports student management, grade tracking, attendance monitoring, and advanced analytics features.

**Base URL**: `http://your-domain.com/api/v1`

## Authentication

All API endpoints require authentication using API keys. You can create API keys through the admin dashboard.

### Request Headers

```http
Authorization: Bearer YOUR_KEY_ID:YOUR_SECRET
Content-Type: application/json
```

### Example Authentication

```bash
curl -H "Authorization: Bearer abc123:def456789" \
     -H "Content-Type: application/json" \
     "http://localhost:5000/api/v1/students"
```

## API Endpoints

### Health Check

**GET** `/health`

Check API health status.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

### Students

#### Get All Students

**GET** `/students`

Retrieve all students in the system.

**Response:**
```json
{
  "students": [
    {
      "id": 1,
      "username": "student1",
      "full_name": "John Smith",
      "email": "john.smith@example.com",
      "phone": "555-0123"
    }
  ],
  "count": 1
}
```

#### Get Student Details

**GET** `/students/{student_id}`

Retrieve detailed information for a specific student.

**Response:**
```json
{
  "student": {
    "id": 1,
    "username": "student1",
    "full_name": "John Smith",
    "email": "john.smith@example.com",
    "phone": "555-0123"
  },
  "subjects": [
    {
      "id": 1,
      "name": "Mathematics",
      "teacher_name": "Mrs. Johnson"
    }
  ],
  "recent_grades": [
    {
      "id": 1,
      "name": "Algebra Quiz",
      "grade": 85.5,
      "subject_name": "Mathematics"
    }
  ]
}
```

#### Get Student Grades

**GET** `/students/{student_id}/grades`

Retrieve grades for a specific student with optional filtering.

**Query Parameters:**
- `subject_id` (optional): Filter by subject ID
- `limit` (optional): Number of records to return (default: 50)

**Response:**
```json
{
  "grades": [
    {
      "id": 1,
      "name": "Algebra Quiz",
      "grade": 85.5,
      "subject_name": "Mathematics",
      "subject_id": 1,
      "teacher_name": "Mrs. Johnson"
    }
  ],
  "statistics": {
    "average": 85.5,
    "highest": 95.0,
    "lowest": 76.0,
    "count": 5
  }
}
```

#### Get Student Attendance

**GET** `/students/{student_id}/attendance`

Retrieve attendance records for a specific student.

**Query Parameters:**
- `days` (optional): Number of days to look back (default: 30)
- `subject_id` (optional): Filter by subject ID

**Response:**
```json
{
  "attendance_records": [
    {
      "date": "2024-01-15",
      "present": true,
      "subject_name": "Mathematics",
      "subject_id": 1
    }
  ],
  "statistics": {
    "attendance_rate": 95.0,
    "total_days": 20,
    "present_days": 19,
    "absent_days": 1
  }
}
```

### Subjects

#### Get All Subjects

**GET** `/subjects`

Retrieve all subjects in the system.

**Response:**
```json
{
  "subjects": [
    {
      "id": 1,
      "name": "Mathematics",
      "teacher_name": "Mrs. Johnson",
      "teacher_username": "teacher1",
      "student_count": 25
    }
  ],
  "count": 1
}
```

#### Get Subject Students

**GET** `/subjects/{subject_id}/students`

Retrieve students enrolled in a specific subject.

**Response:**
```json
{
  "students": [
    {
      "id": 1,
      "username": "student1",
      "full_name": "John Smith",
      "email": "john.smith@example.com",
      "average_grade": 85.5,
      "assignment_count": 5
    }
  ],
  "count": 1
}
```

### Assignments

#### Create Assignment

**POST** `/assignments`

Create a new assignment.

**Request Body:**
```json
{
  "name": "Chapter 5 Quiz",
  "subject_id": 1,
  "student_id": 1,
  "grade": 88.5
}
```

**Response:**
```json
{
  "message": "Assignment created successfully",
  "assignment_id": 123
}
```

#### Update Assignment

**PUT** `/assignments/{assignment_id}`

Update an existing assignment.

**Request Body:**
```json
{
  "name": "Updated Assignment Name",
  "grade": 92.0
}
```

**Response:**
```json
{
  "message": "Assignment updated successfully"
}
```

### Analytics

#### Get Student Analytics

**GET** `/analytics/student/{student_id}`

Get analytics data for a specific student.

**Response:**
```json
{
  "student_id": 1,
  "performance_prediction": {
    "predicted_grade": 87.2,
    "confidence": 0.85,
    "trend": "improving"
  },
  "attendance_analysis": {
    "current_rate": 95.0,
    "predicted_rate": 93.5,
    "risk_level": "low"
  }
}
```

### API Key Management

#### Create API Key

**POST** `/api-keys`

Create a new API key (admin only).

**Request Body:**
```json
{
  "name": "Mobile App Integration",
  "permissions": "read,write",
  "expires_days": 365
}
```

**Response:**
```json
{
  "message": "API key created successfully",
  "key_id": "abc123",
  "secret": "def456789",
  "expires_at": "2025-01-15T10:30:00Z",
  "usage_note": "Store the secret securely. Use format: Authorization: Bearer key_id:secret"
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

**Error Response Format:**
```json
{
  "error": "Error description"
}
```

## Rate Limiting

API requests are automatically logged and monitored. Each API key has usage tracking for monitoring and potential rate limiting in the future.

## SDKs and Integration Examples

### Python SDK Example

```python
import requests

class EduBridgeAPI:
    def __init__(self, base_url, key_id, secret):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {key_id}:{secret}',
            'Content-Type': 'application/json'
        }
    
    def get_students(self):
        response = requests.get(f'{self.base_url}/students', headers=self.headers)
        return response.json()
    
    def get_student_grades(self, student_id, subject_id=None):
        url = f'{self.base_url}/students/{student_id}/grades'
        params = {}
        if subject_id:
            params['subject_id'] = subject_id
        
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()

# Usage
api = EduBridgeAPI('http://localhost:5000/api/v1', 'your_key_id', 'your_secret')
students = api.get_students()
print(students)
```

### JavaScript SDK Example

```javascript
class EduBridgeAPI {
    constructor(baseUrl, keyId, secret) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${keyId}:${secret}`,
            'Content-Type': 'application/json'
        };
    }
    
    async getStudents() {
        const response = await fetch(`${this.baseUrl}/students`, {
            headers: this.headers
        });
        return response.json();
    }
    
    async getStudentGrades(studentId, subjectId = null) {
        let url = `${this.baseUrl}/students/${studentId}/grades`;
        if (subjectId) {
            url += `?subject_id=${subjectId}`;
        }
        
        const response = await fetch(url, {
            headers: this.headers
        });
        return response.json();
    }
}

// Usage
const api = new EduBridgeAPI('http://localhost:5000/api/v1', 'your_key_id', 'your_secret');
api.getStudents().then(students => console.log(students));
```

### Mobile App Integration

For mobile app development, the API is designed to support:

- **Flutter/React Native**: Full REST API compatibility
- **Native iOS/Android**: Standard HTTP client integration
- **Real-time Updates**: WebSocket support for live notifications
- **Offline Sync**: Comprehensive data endpoints for offline storage

## Webhooks (Future Feature)

Coming soon: Webhook support for real-time notifications to external systems when grades, attendance, or other data changes.

## Support

For API support and integration assistance:

- **Documentation Issues**: Create an issue on GitHub
- **Integration Help**: Contact the development team
- **Feature Requests**: Submit through the GitHub issues page

---

**Note**: This API is part of the EduBridge Education Management System. Ensure you have proper authorization and follow your institution's data privacy policies when integrating external systems.
