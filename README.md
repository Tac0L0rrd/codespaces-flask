# EduBridge - School Management System

A comprehensive Flask-based school management system with role-based access for administrators, teachers, and students.

## 🚀 Features

### For Administrators
- **User Management**: Create and manage student and teacher accounts
- **Subject Management**: Create subjects and assign teachers
- **System Overview**: Monitor overall school performance

### For Teachers
- **Class Management**: Manage schedules and enrolled students
- **Grade Management**: Enter and update student grades
- **Attendance Tracking**: Mark and track student attendance
- **Assignment Management**: Create and manage assignments
- **Reports**: View comprehensive class performance reports

### For Students
- **Dashboard Overview**: View grades, attendance, and schedule
- **Subject Details**: Access detailed assignment and grade information
- **Performance Tracking**: Monitor academic progress over time

## 🛠 Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom responsive CSS with gradient themes
- **Authentication**: Session-based user authentication

## 🎨 Design Features

- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Modern UI**: Clean, professional interface with consistent styling
- **Role-based Navigation**: Dynamic navigation based on user permissions
- **Interactive Elements**: Hover effects, smooth transitions, and user-friendly forms

## 📊 Database Schema

The system includes tables for:
- Users (students, teachers, admins)
- Subjects and class assignments
- Grades and assignments
- Attendance records
- Class schedules

## 🔧 Installation & Setup

```bash
# Clone the repository
git clone https://github.com/Tac0L0rrd/codespaces-flask.git

# Navigate to project directory
cd codespaces-flask

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 🎯 Key Functionality

### Authentication System
- Secure login/logout functionality
- Role-based access control (Admin, Teacher, Student)
- Session management

### Grade Management
- Real-time grade entry and updates
- Assignment creation and management
- Performance analytics and reporting

### Attendance System
- Daily attendance marking
- Attendance history tracking
- Automated attendance rate calculations

### Schedule Management
- Class schedule creation and editing
- Period-based time management
- Subject-teacher assignments

## 📱 Responsive Design

The application features a fully responsive design that adapts to:
- Desktop computers (1200px+)
- Tablets (768px - 1200px)
- Mobile devices (320px - 768px)

## 🔒 Security Features

- Session-based user management
- Role-based access control
- SQL injection prevention
- *Note: Demo version uses plain text passwords for ease of testing*

## 🔑 Demo Credentials

After running `create_demo_data.py`, use these credentials to test the system:

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Admin** | `admin` | `admin123` | Full system management |
| **Teacher** | `mr_smith` | `teacher123` | Class & grade management |
| **Student** | `alice_cooper` | `student123` | Personal dashboard & grades |

## 📈 Future Enhancements

- Email notifications for assignments and grades
- Parent portal access
- Advanced reporting and analytics
- Mobile app development
- Integration with external learning management systems

## 👨‍💻 Developer

**Tac0L0rrd**
- GitHub: [@Tac0L0rrd](https://github.com/Tac0L0rrd)

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

*EduBridge represents a modern approach to school management, combining intuitive design with powerful functionality to enhance the educational experience for all stakeholders.*