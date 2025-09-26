"""
Export Functionality Module
PDF report generation and data export capabilities
"""

from flask import Blueprint, request, jsonify, send_file, session
import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
import json
from io import BytesIO, StringIO
import csv
from typing import Dict, List, Optional

# For PDF generation (requires: pip install reportlab)
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

export_bp = Blueprint('export', __name__, url_prefix='/export')
DATABASE = os.path.join(os.path.dirname(__file__), 'school.db')

class DataExporter:
    """Handle various data export formats"""
    
    @staticmethod
    def get_student_data(student_id: int) -> Dict:
        """Get comprehensive student data"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Student basic info
        cur.execute("""
            SELECT id, username, full_name, email, phone
            FROM users WHERE id = ? AND role = 'student'
        """, (student_id,))
        
        student = cur.fetchone()
        if not student:
            return None
        
        student_data = dict(student)
        
        # Get subjects
        cur.execute("""
            SELECT s.id, s.name as subject_name, u.full_name as teacher_name
            FROM subjects s
            JOIN enrollments e ON s.id = e.subject_id
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE e.user_id = ?
            ORDER BY s.name
        """, (student_id,))
        
        student_data['subjects'] = [dict(row) for row in cur.fetchall()]
        
        # Get grades
        cur.execute("""
            SELECT a.id, a.name as assignment_name, a.grade, s.name as subject_name,
                   u.full_name as teacher_name
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE a.user_id = ? AND a.grade IS NOT NULL
            ORDER BY s.name, a.name
        """, (student_id,))
        
        student_data['grades'] = [dict(row) for row in cur.fetchall()]
        
        # Get attendance (last 90 days)
        cur.execute("""
            SELECT att.date, att.present, s.name as subject_name
            FROM attendance att
            JOIN subjects s ON att.subject_id = s.id
            WHERE att.user_id = ? AND att.date >= date('now', '-90 days')
            ORDER BY att.date DESC, s.name
        """, (student_id,))
        
        student_data['attendance'] = [dict(row) for row in cur.fetchall()]
        
        # Calculate statistics
        if student_data['grades']:
            grades_list = [g['grade'] for g in student_data['grades']]
            student_data['grade_stats'] = {
                'average': round(sum(grades_list) / len(grades_list), 2),
                'highest': max(grades_list),
                'lowest': min(grades_list),
                'count': len(grades_list)
            }
        else:
            student_data['grade_stats'] = {'average': 0, 'highest': 0, 'lowest': 0, 'count': 0}
        
        if student_data['attendance']:
            present_count = sum(1 for a in student_data['attendance'] if a['present'])
            student_data['attendance_stats'] = {
                'rate': round((present_count / len(student_data['attendance'])) * 100, 2),
                'total_days': len(student_data['attendance']),
                'present_days': present_count,
                'absent_days': len(student_data['attendance']) - present_count
            }
        else:
            student_data['attendance_stats'] = {'rate': 0, 'total_days': 0, 'present_days': 0, 'absent_days': 0}
        
        conn.close()
        return student_data
    
    @staticmethod
    def get_class_report_data(subject_id: int) -> Dict:
        """Get comprehensive class/subject report data"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Subject info
        cur.execute("""
            SELECT s.id, s.name as subject_name, u.full_name as teacher_name, u.email as teacher_email
            FROM subjects s
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE s.id = ?
        """, (subject_id,))
        
        subject = cur.fetchone()
        if not subject:
            return None
        
        class_data = dict(subject)
        
        # Get students with their performance
        cur.execute("""
            SELECT u.id, u.username, u.full_name, u.email,
                   AVG(a.grade) as average_grade,
                   COUNT(a.id) as assignment_count,
                   MAX(a.grade) as highest_grade,
                   MIN(a.grade) as lowest_grade
            FROM users u
            JOIN enrollments e ON u.id = e.user_id
            LEFT JOIN assignments a ON u.id = a.user_id AND a.subject_id = ?
            WHERE e.subject_id = ? AND u.role = 'student'
            GROUP BY u.id, u.username, u.full_name, u.email
            ORDER BY u.full_name
        """, (subject_id, subject_id))
        
        students = []
        for row in cur.fetchall():
            student = dict(row)
            student['average_grade'] = round(student['average_grade'] or 0, 2)
            students.append(student)
        
        class_data['students'] = students
        
        # Get all assignments
        cur.execute("""
            SELECT DISTINCT a.name as assignment_name, COUNT(*) as submission_count,
                   AVG(a.grade) as average_grade, MAX(a.grade) as highest_grade, MIN(a.grade) as lowest_grade
            FROM assignments a
            WHERE a.subject_id = ? AND a.grade IS NOT NULL
            GROUP BY a.name
            ORDER BY a.name
        """, (subject_id,))
        
        assignments = []
        for row in cur.fetchall():
            assignment = dict(row)
            assignment['average_grade'] = round(assignment['average_grade'] or 0, 2)
            assignments.append(assignment)
        
        class_data['assignments'] = assignments
        
        # Get attendance summary (last 30 days)
        cur.execute("""
            SELECT att.date, 
                   COUNT(*) as total_students,
                   SUM(CASE WHEN att.present = 1 THEN 1 ELSE 0 END) as present_count,
                   SUM(CASE WHEN att.present = 0 THEN 1 ELSE 0 END) as absent_count,
                   ROUND((SUM(CASE WHEN att.present = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as attendance_rate
            FROM attendance att
            WHERE att.subject_id = ? AND att.date >= date('now', '-30 days')
            GROUP BY att.date
            ORDER BY att.date DESC
        """, (subject_id,))
        
        class_data['attendance_by_date'] = [dict(row) for row in cur.fetchall()]
        
        # Calculate overall statistics
        if students:
            all_averages = [s['average_grade'] for s in students if s['average_grade'] > 0]
            if all_averages:
                class_data['class_stats'] = {
                    'class_average': round(sum(all_averages) / len(all_averages), 2),
                    'highest_student_average': max(all_averages),
                    'lowest_student_average': min(all_averages),
                    'total_students': len(students),
                    'students_with_grades': len(all_averages)
                }
            else:
                class_data['class_stats'] = {
                    'class_average': 0, 'highest_student_average': 0, 'lowest_student_average': 0,
                    'total_students': len(students), 'students_with_grades': 0
                }
        
        conn.close()
        return class_data

class PDFReportGenerator:
    """Generate PDF reports using ReportLab"""
    
    @staticmethod
    def generate_student_report(student_data: Dict) -> BytesIO:
        """Generate comprehensive student report PDF"""
        if not PDF_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                               rightMargin=72, leftMargin=72, 
                               topMargin=72, bottomMargin=18)
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        elements.append(Paragraph(f"Student Academic Report", title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Student Information
        elements.append(Paragraph("Student Information", styles['Heading2']))
        
        student_info_data = [
            ['Name:', student_data['full_name']],
            ['Username:', student_data['username']],
            ['Email:', student_data.get('email', 'N/A')],
            ['Phone:', student_data.get('phone', 'N/A')]
        ]
        
        student_table = Table(student_info_data, colWidths=[1.5*inch, 4*inch])
        student_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(student_table)
        elements.append(Spacer(1, 20))
        
        # Academic Performance Summary
        elements.append(Paragraph("Academic Performance Summary", styles['Heading2']))
        
        performance_data = [
            ['Overall Average:', f"{student_data['grade_stats']['average']}%"],
            ['Highest Grade:', f"{student_data['grade_stats']['highest']}%"],
            ['Lowest Grade:', f"{student_data['grade_stats']['lowest']}%"],
            ['Total Assignments:', str(student_data['grade_stats']['count'])],
            ['Attendance Rate:', f"{student_data['attendance_stats']['rate']}%"]
        ]
        
        performance_table = Table(performance_data, colWidths=[2*inch, 1.5*inch])
        performance_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(performance_table)
        elements.append(Spacer(1, 20))
        
        # Subject Enrollment
        if student_data['subjects']:
            elements.append(Paragraph("Enrolled Subjects", styles['Heading2']))
            
            subject_data = [['Subject', 'Teacher']]
            for subject in student_data['subjects']:
                subject_data.append([subject['subject_name'], subject['teacher_name']])
            
            subject_table = Table(subject_data, colWidths=[3*inch, 2.5*inch])
            subject_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(subject_table)
            elements.append(Spacer(1, 20))
        
        # Recent Grades (last 10)
        if student_data['grades']:
            elements.append(Paragraph("Recent Grades", styles['Heading2']))
            
            grade_data = [['Assignment', 'Subject', 'Grade', 'Teacher']]
            recent_grades = student_data['grades'][-10:]  # Last 10 grades
            
            for grade in recent_grades:
                grade_data.append([
                    grade['assignment_name'],
                    grade['subject_name'],
                    f"{grade['grade']}%",
                    grade['teacher_name']
                ])
            
            grade_table = Table(grade_data, colWidths=[2*inch, 1.8*inch, 0.8*inch, 1.4*inch])
            grade_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Center grades
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(grade_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_class_report(class_data: Dict) -> BytesIO:
        """Generate class performance report PDF"""
        if not PDF_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        elements.append(Paragraph(f"Class Performance Report", title_style))
        elements.append(Paragraph(f"Subject: {class_data['subject_name']}", styles['Heading2']))
        elements.append(Paragraph(f"Teacher: {class_data['teacher_name']}", styles['Normal']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Class Statistics
        elements.append(Paragraph("Class Statistics", styles['Heading2']))
        
        stats = class_data.get('class_stats', {})
        stats_data = [
            ['Total Students:', str(stats.get('total_students', 0))],
            ['Students with Grades:', str(stats.get('students_with_grades', 0))],
            ['Class Average:', f"{stats.get('class_average', 0)}%"],
            ['Highest Student Average:', f"{stats.get('highest_student_average', 0)}%"],
            ['Lowest Student Average:', f"{stats.get('lowest_student_average', 0)}%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2.5*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Student Performance
        if class_data['students']:
            elements.append(Paragraph("Student Performance", styles['Heading2']))
            
            student_data = [['Student Name', 'Average Grade', 'Assignments', 'Highest', 'Lowest']]
            
            for student in class_data['students']:
                student_data.append([
                    student['full_name'],
                    f"{student['average_grade']}%" if student['average_grade'] > 0 else 'N/A',
                    str(student['assignment_count']),
                    f"{student['highest_grade']}%" if student['highest_grade'] else 'N/A',
                    f"{student['lowest_grade']}%" if student['lowest_grade'] else 'N/A'
                ])
            
            student_table = Table(student_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            student_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(student_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

# Flask Routes

@export_bp.route('/student/<int:student_id>/pdf')
def export_student_pdf(student_id):
    """Export student report as PDF"""
    # Check permissions (simplified - in real app, check if user can access this student)
    if not session.get('user_id'):
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        student_data = DataExporter.get_student_data(student_id)
        if not student_data:
            return jsonify({'error': 'Student not found'}), 404
        
        pdf_buffer = PDFReportGenerator.generate_student_report(student_data)
        
        filename = f"student_report_{student_data['username']}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/class/<int:subject_id>/pdf')
def export_class_pdf(subject_id):
    """Export class report as PDF"""
    if not session.get('user_id'):
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        class_data = DataExporter.get_class_report_data(subject_id)
        if not class_data:
            return jsonify({'error': 'Subject not found'}), 404
        
        pdf_buffer = PDFReportGenerator.generate_class_report(class_data)
        
        filename = f"class_report_{class_data['subject_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/student/<int:student_id>/csv')
def export_student_csv(student_id):
    """Export student data as CSV"""
    if not session.get('user_id'):
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        student_data = DataExporter.get_student_data(student_id)
        if not student_data:
            return jsonify({'error': 'Student not found'}), 404
        
        # Create CSV buffer
        output = StringIO()
        writer = csv.writer(output)
        
        # Write student info
        writer.writerow(['Student Information'])
        writer.writerow(['Name', student_data['full_name']])
        writer.writerow(['Username', student_data['username']])
        writer.writerow(['Email', student_data.get('email', 'N/A')])
        writer.writerow(['Phone', student_data.get('phone', 'N/A')])
        writer.writerow([])
        
        # Write grades
        writer.writerow(['Grades'])
        writer.writerow(['Assignment', 'Subject', 'Grade', 'Teacher'])
        for grade in student_data['grades']:
            writer.writerow([
                grade['assignment_name'],
                grade['subject_name'],
                grade['grade'],
                grade['teacher_name']
            ])
        
        writer.writerow([])
        
        # Write attendance summary
        writer.writerow(['Attendance Summary'])
        writer.writerow(['Total Days', student_data['attendance_stats']['total_days']])
        writer.writerow(['Present Days', student_data['attendance_stats']['present_days']])
        writer.writerow(['Absent Days', student_data['attendance_stats']['absent_days']])
        writer.writerow(['Attendance Rate', f"{student_data['attendance_stats']['rate']}%"])
        
        # Create response
        output.seek(0)
        buffer = BytesIO()
        buffer.write(output.getvalue().encode('utf-8'))
        buffer.seek(0)
        
        filename = f"student_data_{student_data['username']}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return send_file(
            buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/grades/excel')
def export_grades_excel():
    """Export all grades as Excel file"""
    if not session.get('user_id'):
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        conn = sqlite3.connect(DATABASE)
        
        # Get all grades with student and subject info
        query = """
            SELECT u.full_name as student_name, u.username, s.name as subject_name,
                   a.name as assignment_name, a.grade, ut.full_name as teacher_name
            FROM assignments a
            JOIN users u ON a.user_id = u.id
            JOIN subjects s ON a.subject_id = s.id
            LEFT JOIN users ut ON s.teacher_id = ut.id
            WHERE a.grade IS NOT NULL
            ORDER BY s.name, u.full_name, a.name
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Create Excel buffer
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='All Grades', index=False)
            
            # Add summary sheet
            summary_data = {
                'Metric': ['Total Students', 'Total Assignments', 'Average Grade', 'Highest Grade', 'Lowest Grade'],
                'Value': [
                    df['student_name'].nunique(),
                    len(df),
                    round(df['grade'].mean(), 2),
                    df['grade'].max(),
                    df['grade'].min()
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        buffer.seek(0)
        
        filename = f"all_grades_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def register_export_routes(app):
    """Register export blueprint with Flask app"""
    app.register_blueprint(export_bp)