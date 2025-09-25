# 🎓 EduBridge - Modern School Management System

A comprehensive Flask-based school management system featuring role-based access control, real-time grade management, attendance tracking, and responsive design. Built for administrat## 👨‍💻 Developer

**Tac0L0rrd**

- GitHub: [@Tac0L0rrd](https://github.com/Tac0L0rrd)
- Portfolio: [TacoWorks](https://tacoworks.netlify.app)

## 🙏 Acknowledgments

- Flask community for excellent documentation
- Modern web design inspiration from educational platforms
- Beta testers who provided valuable feedback

---

**EduBridge** represents a modern approach to educational management, combining intuitive design with powerful functionality to enhance learning experiences for administrators, teachers, and students alike.

*⭐ If this project helped you, please consider giving it a star on GitHub!*d students to streamline educational workflows.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.3+-green?style=flat-square&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey?style=flat-square&logo=sqlite)
![Responsive](https://img.shields.io/badge/Design-Responsive-orange?style=flat-square)

## 🌟 Live Demo

**� [Try EduBridge Live](https://your-vercel-deployment.vercel.app)**

Use these demo accounts to explore the system:

## 🔑 Demo Credentials

| Role | Username | Password | Features Available |
|------|----------|----------|-------------------|
| **👑 Admin** | `admin` | `admin123` | Full system management, user creation, reports |
| **📚 Teacher** | `mr_smith` | `teacher123` | Grade entry, attendance, class management |
| **🎓 Student** | `alice_cooper` | `student123` | View grades, assignments, attendance |

*Additional admin account: `Admin` / `2009` (owner access)*

## ✨ Key Features

### 🔐 **Role-Based Access Control**

- **Administrators**: Complete system management
- **Teachers**: Class and grade management capabilities  
- **Students**: Personal academic dashboard access

### 👨‍💼 **Administrator Features**

- 👥 **User Management**: Create/manage teacher and student accounts
- 📚 **Subject Management**: Create subjects and assign teachers
- 📊 **System Analytics**: Monitor overall school performance
- 🔧 **System Settings**: Configure school-wide preferences

### 👨‍🏫 **Teacher Features**

- 📅 **Schedule Management**: Manage class schedules and periods
- ✏️ **Grade Entry**: Enter and update student grades with 4-digit precision
- 📋 **Attendance Tracking**: Mark daily attendance with history
- 📝 **Assignment Management**: Create, edit, and track assignments
- 📊 **Comprehensive Reports**: View detailed class performance analytics
- ⚙️ **Settings**: Customize notification preferences

### 🎓 **Student Features**

- 🏠 **Personal Dashboard**: Overview of grades, attendance, and schedule
- 📖 **Subject Details**: Detailed view of assignments and grades per subject
- 📈 **Progress Tracking**: Visual representation of academic performance
- 📊 **Attendance Records**: Personal attendance history and statistics

## 🛠 Technology Stack

- **Backend**: Python 3.8+ with Flask 2.3+
- **Database**: SQLite with comprehensive relational schema
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Custom responsive CSS with modern gradients and 3D effects
- **Authentication**: Secure session-based user management
- **Deployment**: Vercel-ready with serverless architecture

## 🎨 Design Highlights

- **📱 Fully Responsive**: Seamless experience across desktop, tablet, and mobile
- **🎨 Modern UI/UX**: Clean, professional interface with consistent styling
- **🌈 Dynamic Themes**: Beautiful gradient backgrounds and hover effects
- **🧭 Intuitive Navigation**: Role-based navigation with dropdown menus
- **⚡ Fast Loading**: Optimized for performance and user experience
- **♿ Accessible**: WCAG-compliant design principles

## 📊 Database Architecture

**7 Comprehensive Tables:**

- **Users**: Admin, teacher, and student profiles with role management
- **Subjects**: Course catalog with teacher assignments
- **Assignments**: Grade tracking with subject relationships  
- **Enrollments**: Student-subject relationships
- **Attendance**: Daily attendance records with date tracking
- **Schedule**: Class period and time management
- **User Settings**: Personalized notification preferences

## 🎯 Core Functionality

### 🔒 **Authentication & Security**
- Secure session-based authentication
- Role-based route protection
- SQL injection prevention
- CSRF protection ready

### 📊 **Grade Management System**
- Real-time grade entry and updates
- Support for 4-digit precision (100.0, 87.25)
- Assignment creation with subject linking
- Automated GPA calculations
- Performance analytics and trends

### 📅 **Attendance Management**
- Daily attendance marking interface
- Historical attendance tracking
- Automated attendance rate calculations
- Period-based attendance records

### 📋 **Assignment System**
- Assignment creation and management
- Grade association and tracking
- Subject-specific assignment organization
- Progress monitoring tools

### 📈 **Reporting & Analytics**
- Teacher performance reports (fixed SQL queries)
- Student progress tracking
- Attendance analytics
- Grade distribution insights

## 📱 Responsive Design Specifications

| Device Type | Screen Size | Optimizations |
|-------------|-------------|---------------|
| **Desktop** | 1200px+ | Full dashboard layout, side navigation |
| **Tablet** | 768px - 1200px | Adaptive grid, touch-friendly buttons |
| **Mobile** | 320px - 768px | Stacked layout, mobile-first navigation |

## � Technical Improvements

### Recent Updates
- ✅ Fixed teacher reports SQL queries (subjects.teacher_id vs assignments.user_id)
- ✅ Redesigned student assignment display from bullet lists to professional cards
- ✅ Standardized container dimensions (900px dashboard, 450px auth)
- ✅ Added comprehensive favicon support (SVG + ICO)
- ✅ Implemented demo data auto-initialization for deployment
- ✅ Enhanced grade input fields for 4-digit display
- ✅ Code cleanup and professional formatting

### Performance Features
- Optimized database queries
- Efficient session management
- Minified CSS and responsive images
- Fast-loading modern design elements

## 🎨 UI/UX Features

- **3D Button Effects**: Modern, interactive button styling
- **Gradient Backgrounds**: Professional color schemes
- **Card-Based Layouts**: Clean information organization
- **Hover Animations**: Smooth transitions and feedback
- **Consistent Typography**: Professional font hierarchy
- **Mobile-First Design**: Touch-friendly interface elements

## 📦 Project Structure

```text
edubridge/
├── app.py                 # Main Flask application
├── index.py              # Vercel entry point
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel deployment config
├── static/
│   ├── styles.css        # Custom CSS styling
│   ├── favicon.svg       # Modern SVG favicon
│   ├── favicon.ico       # Classic ICO favicon
│   └── manifest.json     # PWA manifest
├── templates/            # HTML template files
│   ├── login.html        # Authentication pages
│   ├── *_dashboard.html  # Role-specific dashboards
│   ├── manage_*.html     # Management interfaces
│   └── ...              # Additional templates
└── docs/                # Documentation files
```

## � Future Roadmap

- [ ] **Email Notifications**: Automated grade and assignment alerts
- [ ] **Parent Portal**: Parent access to student information
- [ ] **Advanced Analytics**: Machine learning insights
- [ ] **Mobile App**: Native iOS/Android applications
- [ ] **LMS Integration**: Moodle, Canvas, Blackboard compatibility
- [ ] **Multi-Language Support**: Internationalization features
- [ ] **API Development**: RESTful API for external integrations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License & Attribution

This project is developed by **Tac0L0rrd** and is available for educational purposes. 

**⚠️ Important:** If you use, modify, or deploy this code, proper attribution is required:
- Credit must be given to the original developer (Tac0L0rrd)
- Link back to the original repository: https://github.com/Tac0L0rrd/codespaces-flask
- Maintain this attribution notice in any derivatives

## 👨‍💻 Developer

**Tac0L0rrd**

- GitHub: [@Tac0L0rrd](https://github.com/Tac0L0rrd)
- Portfolio: [TacoWorks](https://tacoworks.netlify.app)

## � Acknowledgments

- Flask community for excellent documentation
- Modern web design inspiration from educational platforms
- Beta testers who provided valuable feedback

---

**EduBridge** represents a modern approach to educational management, combining intuitive design with powerful functionality to enhance learning experiences for administrators, teachers, and students alike.

*⭐ If this project helped you, please consider giving it a star on GitHub!*