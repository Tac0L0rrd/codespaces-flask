"""
Advanced Analytics Module
Provides machine learning insights and advanced data visualization
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from collections import defaultdict
import math

# Optional imports for advanced analytics
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import seaborn as sns
    ANALYTICS_LIBS_AVAILABLE = True
except ImportError as e:
    print(f"Advanced analytics libraries not available: {e}")
    ANALYTICS_LIBS_AVAILABLE = False
    # Create dummy objects to prevent errors
    class DummyPandas:
        @staticmethod
        def DataFrame(*args, **kwargs):
            return None
        @staticmethod
        def read_sql_query(*args, **kwargs):
            return None
    
    class DummyNumpy:
        @staticmethod
        def array(*args, **kwargs):
            return []
        @staticmethod
        def mean(*args, **kwargs):
            return 0
        @staticmethod
        def std(*args, **kwargs):
            return 0
    
    pd = DummyPandas()
    np = DummyNumpy()

class AdvancedAnalytics:
    def __init__(self):
        self.database = os.path.join(os.path.dirname(__file__), 'school.db')
    
    def get_dataframe_from_query(self, query: str, params: tuple = ()):
        """Execute query and return pandas DataFrame"""
        if not ANALYTICS_LIBS_AVAILABLE:
            return None
        
        conn = sqlite3.connect(self.database)
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        except Exception as e:
            print(f"Query error: {e}")
            return None
        finally:
            conn.close()
    
    def predict_student_performance(self, student_id: int) -> Dict:
        """Predict future performance based on historical data"""
        # Get historical grades
        query = """
            SELECT a.grade, a.id, s.name as subject_name, 
                   julianday('now') - julianday(datetime(a.id, 'unixepoch')) as days_ago
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.user_id = ? AND a.grade IS NOT NULL AND a.grade > 0
            ORDER BY a.id
        """
        
        df = self.get_dataframe_from_query(query, (student_id,))
        
        if df.empty or len(df) < 3:
            return {'error': 'Insufficient data for prediction'}
        
        # Simple linear regression for trend analysis
        x = np.arange(len(df))
        y = df['grade'].values
        
        # Calculate trend
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        
        # Linear regression coefficients
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Predict next performance
        next_x = len(df)
        predicted_grade = slope * next_x + intercept
        predicted_grade = max(0, min(100, predicted_grade))  # Clamp between 0-100
        
        # Calculate confidence based on variance
        residuals = y - (slope * x + intercept)
        variance = np.var(residuals)
        confidence = max(0, min(100, 100 - variance))
        
        # Performance trend
        if slope > 0.5:
            trend = 'improving'
        elif slope < -0.5:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # Subject-wise analysis
        subject_performance = {}
        for subject in df['subject_name'].unique():
            subject_df = df[df['subject_name'] == subject]
            if len(subject_df) >= 2:
                subject_avg = subject_df['grade'].mean()
                subject_trend = subject_df['grade'].diff().mean()
                subject_performance[subject] = {
                    'average': round(subject_avg, 2),
                    'trend': 'improving' if subject_trend > 0 else 'declining' if subject_trend < 0 else 'stable',
                    'assignments_count': len(subject_df)
                }
        
        return {
            'predicted_grade': round(predicted_grade, 2),
            'confidence': round(confidence, 2),
            'trend': trend,
            'current_average': round(df['grade'].mean(), 2),
            'improvement_rate': round(slope, 3),
            'subject_performance': subject_performance,
            'data_points': len(df)
        }
    
    def analyze_class_performance(self, subject_id: int) -> Dict:
        """Analyze overall class performance for a subject"""
        query = """
            SELECT a.grade, a.user_id, u.username, u.full_name,
                   COUNT(*) OVER (PARTITION BY a.user_id) as assignment_count
            FROM assignments a
            JOIN users u ON a.user_id = u.id
            WHERE a.subject_id = ? AND a.grade IS NOT NULL AND a.grade > 0
        """
        
        df = self.get_dataframe_from_query(query, (subject_id,))
        
        if df.empty:
            return {'error': 'No grade data available'}
        
        # Basic statistics
        stats = {
            'mean': round(df['grade'].mean(), 2),
            'median': round(df['grade'].median(), 2),
            'std_dev': round(df['grade'].std(), 2),
            'min': round(df['grade'].min(), 2),
            'max': round(df['grade'].max(), 2),
            'total_students': df['user_id'].nunique(),
            'total_assignments': len(df)
        }
        
        # Performance distribution
        grade_ranges = {
            'A (90-100)': len(df[df['grade'] >= 90]),
            'B (80-89)': len(df[(df['grade'] >= 80) & (df['grade'] < 90)]),
            'C (70-79)': len(df[(df['grade'] >= 70) & (df['grade'] < 80)]),
            'D (60-69)': len(df[(df['grade'] >= 60) & (df['grade'] < 70)]),
            'F (0-59)': len(df[df['grade'] < 60])
        }
        
        # Student performance analysis
        student_stats = df.groupby(['user_id', 'username', 'full_name']).agg({
            'grade': ['mean', 'count', 'std']
        }).round(2)
        
        student_performance = []
        for idx, row in student_stats.iterrows():
            student_performance.append({
                'user_id': idx[0],
                'username': idx[1],
                'full_name': idx[2],
                'average_grade': row[('grade', 'mean')],
                'assignment_count': row[('grade', 'count')],
                'consistency': round(100 - row[('grade', 'std')] if not pd.isna(row[('grade', 'std')]) else 100, 2)
            })
        
        # Sort by average grade
        student_performance.sort(key=lambda x: x['average_grade'], reverse=True)
        
        # Risk assessment
        at_risk_students = [
            student for student in student_performance 
            if student['average_grade'] < 70
        ]
        
        return {
            'statistics': stats,
            'grade_distribution': grade_ranges,
            'student_performance': student_performance,
            'at_risk_students': at_risk_students,
            'performance_insights': self._generate_class_insights(stats, grade_ranges)
        }
    
    def _generate_class_insights(self, stats: Dict, distribution: Dict) -> List[str]:
        """Generate insights based on class performance"""
        insights = []
        
        if stats['mean'] >= 85:
            insights.append("Class is performing excellently with high average scores.")
        elif stats['mean'] >= 75:
            insights.append("Class performance is above average.")
        elif stats['mean'] >= 65:
            insights.append("Class performance is average - consider additional support.")
        else:
            insights.append("Class performance needs improvement - intervention recommended.")
        
        if stats['std_dev'] > 15:
            insights.append("High grade variance indicates diverse performance levels.")
        elif stats['std_dev'] < 8:
            insights.append("Low grade variance shows consistent performance across students.")
        
        failing_percentage = (distribution['F (0-59)'] / stats['total_assignments']) * 100
        if failing_percentage > 20:
            insights.append(f"{failing_percentage:.1f}% of assignments are failing - review curriculum difficulty.")
        
        if distribution['A (90-100)'] > distribution['F (0-59)'] * 2:
            insights.append("Strong performance with more A grades than failing grades.")
        
        return insights
    
    def analyze_attendance_patterns(self, student_id: int = None, subject_id: int = None) -> Dict:
        """Analyze attendance patterns and identify trends"""
        query_conditions = []
        params = []
        
        if student_id:
            query_conditions.append("att.user_id = ?")
            params.append(student_id)
        
        if subject_id:
            query_conditions.append("att.subject_id = ?")
            params.append(subject_id)
        
        where_clause = " AND ".join(query_conditions) if query_conditions else "1=1"
        
        query = f"""
            SELECT att.*, s.name as subject_name, u.username, u.full_name,
                   strftime('%w', att.date) as day_of_week,
                   strftime('%Y-%m', att.date) as month_year
            FROM attendance att
            JOIN subjects s ON att.subject_id = s.id
            JOIN users u ON att.user_id = u.id
            WHERE {where_clause}
            ORDER BY att.date DESC
        """
        
        df = self.get_dataframe_from_query(query, tuple(params))
        
        if df.empty:
            return {'error': 'No attendance data available'}
        
        # Overall attendance rate
        total_records = len(df)
        present_records = df['present'].sum()
        attendance_rate = (present_records / total_records) * 100
        
        # Day of week patterns
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        day_patterns = {}
        
        for day_num in range(7):
            day_data = df[df['day_of_week'] == str(day_num)]
            if not day_data.empty:
                day_rate = (day_data['present'].sum() / len(day_data)) * 100
                day_patterns[day_names[day_num]] = round(day_rate, 2)
        
        # Monthly trends
        monthly_trends = df.groupby('month_year').agg({
            'present': ['sum', 'count']
        })
        
        monthly_rates = {}
        for month, data in monthly_trends.iterrows():
            rate = (data[('present', 'sum')] / data[('present', 'count')]) * 100
            monthly_rates[month] = round(rate, 2)
        
        # Subject-wise attendance (if not filtered by subject)
        subject_attendance = {}
        if not subject_id:
            for subject in df['subject_name'].unique():
                subject_data = df[df['subject_name'] == subject]
                subject_rate = (subject_data['present'].sum() / len(subject_data)) * 100
                subject_attendance[subject] = round(subject_rate, 2)
        
        return {
            'overall_attendance_rate': round(attendance_rate, 2),
            'total_records': total_records,
            'present_days': int(present_records),
            'absent_days': int(total_records - present_records),
            'day_patterns': day_patterns,
            'monthly_trends': monthly_rates,
            'subject_attendance': subject_attendance,
            'insights': self._generate_attendance_insights(attendance_rate, day_patterns, monthly_rates)
        }
    
    def _generate_attendance_insights(self, overall_rate: float, day_patterns: Dict, monthly_trends: Dict) -> List[str]:
        """Generate insights from attendance analysis"""
        insights = []
        
        if overall_rate >= 95:
            insights.append("Excellent attendance record.")
        elif overall_rate >= 85:
            insights.append("Good attendance with room for improvement.")
        elif overall_rate >= 75:
            insights.append("Attendance needs improvement - consider intervention.")
        else:
            insights.append("Poor attendance - immediate intervention required.")
        
        # Day patterns
        if day_patterns:
            worst_day = min(day_patterns, key=day_patterns.get)
            best_day = max(day_patterns, key=day_patterns.get)
            
            if day_patterns[worst_day] < overall_rate - 10:
                insights.append(f"Significantly lower attendance on {worst_day}s ({day_patterns[worst_day]:.1f}%)")
            
            if day_patterns[best_day] > overall_rate + 10:
                insights.append(f"Best attendance on {best_day}s ({day_patterns[best_day]:.1f}%)")
        
        # Monthly trends
        if monthly_trends and len(monthly_trends) >= 2:
            recent_months = list(monthly_trends.keys())[-2:]
            if len(recent_months) == 2:
                trend = monthly_trends[recent_months[1]] - monthly_trends[recent_months[0]]
                if trend > 5:
                    insights.append("Attendance improving in recent months.")
                elif trend < -5:
                    insights.append("Attendance declining in recent months.")
        
        return insights
    
    def generate_performance_dashboard_data(self, user_id: int, role: str) -> Dict:
        """Generate comprehensive dashboard data for different user roles"""
        dashboard_data = {}
        
        if role == 'student':
            # Student-specific analytics
            prediction = self.predict_student_performance(user_id)
            attendance = self.analyze_attendance_patterns(student_id=user_id)
            
            dashboard_data = {
                'performance_prediction': prediction,
                'attendance_analysis': attendance,
                'type': 'student'
            }
        
        elif role == 'teacher':
            # Teacher-specific analytics - analyze all their classes
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            
            # Get teacher's subjects
            cur.execute("SELECT id, name FROM subjects WHERE teacher_id = ?", (user_id,))
            subjects = cur.fetchall()
            conn.close()
            
            class_analytics = {}
            for subject_id, subject_name in subjects:
                class_performance = self.analyze_class_performance(subject_id)
                attendance_analysis = self.analyze_attendance_patterns(subject_id=subject_id)
                
                class_analytics[subject_name] = {
                    'performance': class_performance,
                    'attendance': attendance_analysis
                }
            
            dashboard_data = {
                'class_analytics': class_analytics,
                'type': 'teacher'
            }
        
        elif role == 'admin':
            # System-wide analytics
            dashboard_data = self.generate_system_analytics()
        
        return dashboard_data
    
    def generate_system_analytics(self) -> Dict:
        """Generate system-wide analytics for administrators"""
        conn = sqlite3.connect(self.database)
        
        # Overall statistics
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM users WHERE role = 'student') as total_students,
                (SELECT COUNT(*) FROM users WHERE role = 'teacher') as total_teachers,
                (SELECT COUNT(*) FROM subjects) as total_subjects,
                (SELECT COUNT(*) FROM assignments WHERE grade IS NOT NULL) as total_graded_assignments,
                (SELECT AVG(grade) FROM assignments WHERE grade IS NOT NULL AND grade > 0) as overall_average
        """)
        
        system_stats = dict(zip(['total_students', 'total_teachers', 'total_subjects', 'total_graded_assignments', 'overall_average'], cur.fetchone()))
        
        # Performance trends by month
        query = """
            SELECT strftime('%Y-%m', datetime(a.id, 'unixepoch')) as month,
                   AVG(a.grade) as avg_grade,
                   COUNT(*) as assignment_count
            FROM assignments a
            WHERE a.grade IS NOT NULL AND a.grade > 0
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """
        
        monthly_performance = self.get_dataframe_from_query(query)
        
        # Subject performance comparison
        query = """
            SELECT s.name as subject_name,
                   AVG(a.grade) as avg_grade,
                   COUNT(a.id) as assignment_count,
                   COUNT(DISTINCT a.user_id) as student_count
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.grade IS NOT NULL AND a.grade > 0
            GROUP BY s.id, s.name
            ORDER BY avg_grade DESC
        """
        
        subject_performance = self.get_dataframe_from_query(query)
        
        conn.close()
        
        return {
            'system_statistics': system_stats,
            'monthly_trends': monthly_performance.to_dict('records') if not monthly_performance.empty else [],
            'subject_comparison': subject_performance.to_dict('records') if not subject_performance.empty else [],
            'type': 'admin'
        }

# Global analytics instance
analytics = AdvancedAnalytics()

def register_analytics_routes(app):
    """Register analytics routes with Flask app"""
    # Analytics functionality integrated into main app
    # Could add dedicated analytics API routes in the future
    pass