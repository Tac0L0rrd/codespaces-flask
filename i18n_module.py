"""
Multi-Language Support Module
Internationalization (i18n) features for the education management system
"""

from flask import Blueprint, request, session, jsonify, redirect, url_for
import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Optional, List

i18n_bp = Blueprint('i18n', __name__, url_prefix='/i18n')
DATABASE = os.path.join(os.path.dirname(__file__), 'school.db')

# Default translations
DEFAULT_TRANSLATIONS = {
    'en': {
        # Navigation
        'dashboard': 'Dashboard',
        'students': 'Students',
        'teachers': 'Teachers',
        'subjects': 'Subjects',
        'assignments': 'Assignments',
        'attendance': 'Attendance',
        'grades': 'Grades',
        'reports': 'Reports',
        'settings': 'Settings',
        'logout': 'Logout',
        'login': 'Login',
        'signup': 'Sign Up',
        
        # Common actions
        'add': 'Add',
        'edit': 'Edit',
        'delete': 'Delete',
        'save': 'Save',
        'cancel': 'Cancel',
        'submit': 'Submit',
        'search': 'Search',
        'filter': 'Filter',
        'export': 'Export',
        'import': 'Import',
        'print': 'Print',
        'close': 'Close',
        'back': 'Back',
        'next': 'Next',
        'previous': 'Previous',
        
        # Forms
        'name': 'Name',
        'email': 'Email',
        'phone': 'Phone',
        'username': 'Username',
        'password': 'Password',
        'confirm_password': 'Confirm Password',
        'full_name': 'Full Name',
        'subject_name': 'Subject Name',
        'assignment_name': 'Assignment Name',
        'grade': 'Grade',
        'date': 'Date',
        'description': 'Description',
        
        # Messages
        'success': 'Success',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Information',
        'required_field': 'This field is required',
        'invalid_email': 'Please enter a valid email address',
        'password_mismatch': 'Passwords do not match',
        'login_required': 'Please log in to continue',
        'access_denied': 'Access denied',
        'not_found': 'Not found',
        'server_error': 'Server error occurred',
        
        # Academic terms
        'present': 'Present',
        'absent': 'Absent',
        'late': 'Late',
        'excused': 'Excused',
        'semester': 'Semester',
        'academic_year': 'Academic Year',
        'term': 'Term',
        'course': 'Course',
        'class': 'Class',
        'section': 'Section',
        
        # Reports and analytics
        'performance': 'Performance',
        'analytics': 'Analytics',
        'statistics': 'Statistics',
        'average': 'Average',
        'highest': 'Highest',
        'lowest': 'Lowest',
        'total': 'Total',
        'percentage': 'Percentage',
        'trend': 'Trend',
        'improvement': 'Improvement',
        'decline': 'Decline',
        
        # Time periods
        'today': 'Today',
        'yesterday': 'Yesterday',
        'this_week': 'This Week',
        'last_week': 'Last Week',
        'this_month': 'This Month',
        'last_month': 'Last Month',
        'this_year': 'This Year',
        'last_year': 'Last Year',
        
        # Notifications
        'new_grade': 'New Grade',
        'assignment_due': 'Assignment Due',
        'attendance_marked': 'Attendance Marked',
        'new_assignment': 'New Assignment',
        'system_announcement': 'System Announcement',
        'parent_notification': 'Parent Notification',
    },
    
    'es': {
        # Navigation
        'dashboard': 'Panel de Control',
        'students': 'Estudiantes',
        'teachers': 'Profesores',
        'subjects': 'Materias',
        'assignments': 'Tareas',
        'attendance': 'Asistencia',
        'grades': 'Calificaciones',
        'reports': 'Reportes',
        'settings': 'Configuración',
        'logout': 'Cerrar Sesión',
        'login': 'Iniciar Sesión',
        'signup': 'Registrarse',
        
        # Common actions
        'add': 'Agregar',
        'edit': 'Editar',
        'delete': 'Eliminar',
        'save': 'Guardar',
        'cancel': 'Cancelar',
        'submit': 'Enviar',
        'search': 'Buscar',
        'filter': 'Filtrar',
        'export': 'Exportar',
        'import': 'Importar',
        'print': 'Imprimir',
        'close': 'Cerrar',
        'back': 'Atrás',
        'next': 'Siguiente',
        'previous': 'Anterior',
        
        # Forms
        'name': 'Nombre',
        'email': 'Correo Electrónico',
        'phone': 'Teléfono',
        'username': 'Usuario',
        'password': 'Contraseña',
        'confirm_password': 'Confirmar Contraseña',
        'full_name': 'Nombre Completo',
        'subject_name': 'Nombre de Materia',
        'assignment_name': 'Nombre de Tarea',
        'grade': 'Calificación',
        'date': 'Fecha',
        'description': 'Descripción',
        
        # Messages
        'success': 'Éxito',
        'error': 'Error',
        'warning': 'Advertencia',
        'info': 'Información',
        'required_field': 'Este campo es obligatorio',
        'invalid_email': 'Por favor ingrese un correo electrónico válido',
        'password_mismatch': 'Las contraseñas no coinciden',
        'login_required': 'Por favor inicie sesión para continuar',
        'access_denied': 'Acceso denegado',
        'not_found': 'No encontrado',
        'server_error': 'Ocurrió un error en el servidor',
        
        # Academic terms
        'present': 'Presente',
        'absent': 'Ausente',
        'late': 'Tardío',
        'excused': 'Justificado',
        'semester': 'Semestre',
        'academic_year': 'Año Académico',
        'term': 'Período',
        'course': 'Curso',
        'class': 'Clase',
        'section': 'Sección',
        
        # Reports and analytics
        'performance': 'Rendimiento',
        'analytics': 'Analíticas',
        'statistics': 'Estadísticas',
        'average': 'Promedio',
        'highest': 'Más Alto',
        'lowest': 'Más Bajo',
        'total': 'Total',
        'percentage': 'Porcentaje',
        'trend': 'Tendencia',
        'improvement': 'Mejora',
        'decline': 'Declive',
        
        # Time periods
        'today': 'Hoy',
        'yesterday': 'Ayer',
        'this_week': 'Esta Semana',
        'last_week': 'Semana Pasada',
        'this_month': 'Este Mes',
        'last_month': 'Mes Pasado',
        'this_year': 'Este Año',
        'last_year': 'Año Pasado',
        
        # Notifications
        'new_grade': 'Nueva Calificación',
        'assignment_due': 'Tarea Vence',
        'attendance_marked': 'Asistencia Marcada',
        'new_assignment': 'Nueva Tarea',
        'system_announcement': 'Anuncio del Sistema',
        'parent_notification': 'Notificación para Padres',
    },
    
    'fr': {
        # Navigation
        'dashboard': 'Tableau de Bord',
        'students': 'Étudiants',
        'teachers': 'Enseignants',
        'subjects': 'Matières',
        'assignments': 'Devoirs',
        'attendance': 'Présence',
        'grades': 'Notes',
        'reports': 'Rapports',
        'settings': 'Paramètres',
        'logout': 'Se Déconnecter',
        'login': 'Se Connecter',
        'signup': 'S\'inscrire',
        
        # Common actions
        'add': 'Ajouter',
        'edit': 'Modifier',
        'delete': 'Supprimer',
        'save': 'Enregistrer',
        'cancel': 'Annuler',
        'submit': 'Soumettre',
        'search': 'Rechercher',
        'filter': 'Filtrer',
        'export': 'Exporter',
        'import': 'Importer',
        'print': 'Imprimer',
        'close': 'Fermer',
        'back': 'Retour',
        'next': 'Suivant',
        'previous': 'Précédent',
        
        # Forms
        'name': 'Nom',
        'email': 'Email',
        'phone': 'Téléphone',
        'username': 'Nom d\'utilisateur',
        'password': 'Mot de Passe',
        'confirm_password': 'Confirmer Mot de Passe',
        'full_name': 'Nom Complet',
        'subject_name': 'Nom de Matière',
        'assignment_name': 'Nom du Devoir',
        'grade': 'Note',
        'date': 'Date',
        'description': 'Description',
        
        # Messages
        'success': 'Succès',
        'error': 'Erreur',
        'warning': 'Avertissement',
        'info': 'Information',
        'required_field': 'Ce champ est requis',
        'invalid_email': 'Veuillez saisir une adresse email valide',
        'password_mismatch': 'Les mots de passe ne correspondent pas',
        'login_required': 'Veuillez vous connecter pour continuer',
        'access_denied': 'Accès refusé',
        'not_found': 'Non trouvé',
        'server_error': 'Erreur serveur survenue',
        
        # Academic terms
        'present': 'Présent',
        'absent': 'Absent',
        'late': 'En Retard',
        'excused': 'Excusé',
        'semester': 'Semestre',
        'academic_year': 'Année Académique',
        'term': 'Trimestre',
        'course': 'Cours',
        'class': 'Classe',
        'section': 'Section',
        
        # Reports and analytics
        'performance': 'Performance',
        'analytics': 'Analytiques',
        'statistics': 'Statistiques',
        'average': 'Moyenne',
        'highest': 'Plus Élevé',
        'lowest': 'Plus Bas',
        'total': 'Total',
        'percentage': 'Pourcentage',
        'trend': 'Tendance',
        'improvement': 'Amélioration',
        'decline': 'Déclin',
        
        # Time periods
        'today': 'Aujourd\'hui',
        'yesterday': 'Hier',
        'this_week': 'Cette Semaine',
        'last_week': 'Semaine Dernière',
        'this_month': 'Ce Mois',
        'last_month': 'Mois Dernier',
        'this_year': 'Cette Année',
        'last_year': 'Année Dernière',
        
        # Notifications
        'new_grade': 'Nouvelle Note',
        'assignment_due': 'Devoir À Rendre',
        'attendance_marked': 'Présence Marquée',
        'new_assignment': 'Nouveau Devoir',
        'system_announcement': 'Annonce Système',
        'parent_notification': 'Notification Parent',
    },
    
    'de': {
        # Navigation
        'dashboard': 'Dashboard',
        'students': 'Schüler',
        'teachers': 'Lehrer',
        'subjects': 'Fächer',
        'assignments': 'Aufgaben',
        'attendance': 'Anwesenheit',
        'grades': 'Noten',
        'reports': 'Berichte',
        'settings': 'Einstellungen',
        'logout': 'Abmelden',
        'login': 'Anmelden',
        'signup': 'Registrieren',
        
        # Common actions
        'add': 'Hinzufügen',
        'edit': 'Bearbeiten',
        'delete': 'Löschen',
        'save': 'Speichern',
        'cancel': 'Abbrechen',
        'submit': 'Absenden',
        'search': 'Suchen',
        'filter': 'Filter',
        'export': 'Exportieren',
        'import': 'Importieren',
        'print': 'Drucken',
        'close': 'Schließen',
        'back': 'Zurück',
        'next': 'Weiter',
        'previous': 'Vorherige',
        
        # Forms
        'name': 'Name',
        'email': 'E-Mail',
        'phone': 'Telefon',
        'username': 'Benutzername',
        'password': 'Passwort',
        'confirm_password': 'Passwort Bestätigen',
        'full_name': 'Vollständiger Name',
        'subject_name': 'Fachname',
        'assignment_name': 'Aufgabenname',
        'grade': 'Note',
        'date': 'Datum',
        'description': 'Beschreibung',
        
        # Academic terms
        'present': 'Anwesend',
        'absent': 'Abwesend',
        'late': 'Verspätet',
        'excused': 'Entschuldigt',
        'semester': 'Semester',
        'academic_year': 'Schuljahr',
        'term': 'Semester',
        'course': 'Kurs',
        'class': 'Klasse',
        'section': 'Sektion',
    }
}

def init_i18n_tables():
    """Initialize internationalization tables"""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # Language settings table
    cur.execute('''CREATE TABLE IF NOT EXISTS language_settings (
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE,
        language_code TEXT DEFAULT 'en',
        date_format TEXT DEFAULT 'MM/dd/yyyy',
        time_format TEXT DEFAULT '12h',
        timezone TEXT DEFAULT 'UTC',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Custom translations table
    cur.execute('''CREATE TABLE IF NOT EXISTS translations (
        id INTEGER PRIMARY KEY,
        language_code TEXT,
        translation_key TEXT,
        translation_value TEXT,
        context TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(language_code, translation_key)
    )''')
    
    # Supported languages table
    cur.execute('''CREATE TABLE IF NOT EXISTS supported_languages (
        id INTEGER PRIMARY KEY,
        code TEXT UNIQUE,
        name TEXT,
        native_name TEXT,
        is_active BOOLEAN DEFAULT 1,
        sort_order INTEGER DEFAULT 0
    )''')
    
    # Insert default supported languages
    languages = [
        ('en', 'English', 'English', 1, 1),
        ('es', 'Spanish', 'Español', 1, 2),
        ('fr', 'French', 'Français', 1, 3),
        ('de', 'German', 'Deutsch', 1, 4),
        ('zh', 'Chinese', '中文', 1, 5),
        ('ja', 'Japanese', '日本語', 1, 6),
        ('ar', 'Arabic', 'العربية', 0, 7),  # Disabled by default
        ('ru', 'Russian', 'Русский', 0, 8)   # Disabled by default
    ]
    
    for lang in languages:
        cur.execute("""
            INSERT OR IGNORE INTO supported_languages (code, name, native_name, is_active, sort_order)
            VALUES (?, ?, ?, ?, ?)
        """, lang)
    
    # Insert default translations
    for lang_code, translations in DEFAULT_TRANSLATIONS.items():
        for key, value in translations.items():
            cur.execute("""
                INSERT OR IGNORE INTO translations (language_code, translation_key, translation_value)
                VALUES (?, ?, ?)
            """, (lang_code, key, value))
    
    conn.commit()
    conn.close()

class TranslationService:
    """Handle translation and localization"""
    
    @staticmethod
    def get_user_language(user_id: int) -> str:
        """Get user's preferred language"""
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        cur.execute("SELECT language_code FROM language_settings WHERE user_id = ?", (user_id,))
        result = cur.fetchone()
        conn.close()
        
        return result[0] if result else 'en'
    
    @staticmethod
    def set_user_language(user_id: int, language_code: str) -> bool:
        """Set user's preferred language"""
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT OR REPLACE INTO language_settings (user_id, language_code, updated_at)
                VALUES (?, ?, datetime('now'))
            """, (user_id, language_code))
            
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_translations(language_code: str = 'en') -> Dict[str, str]:
        """Get all translations for a language"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT translation_key, translation_value
            FROM translations
            WHERE language_code = ? AND is_active = 1
        """, (language_code,))
        
        translations = {row['translation_key']: row['translation_value'] for row in cur.fetchall()}
        conn.close()
        
        # Fall back to default translations if database is empty
        if not translations and language_code in DEFAULT_TRANSLATIONS:
            translations = DEFAULT_TRANSLATIONS[language_code]
        elif not translations:
            translations = DEFAULT_TRANSLATIONS['en']
        
        return translations
    
    @staticmethod
    def translate(key: str, language_code: str = 'en', default: str = None) -> str:
        """Translate a single key"""
        translations = TranslationService.get_translations(language_code)
        return translations.get(key, default or key)
    
    @staticmethod
    def get_supported_languages() -> List[Dict]:
        """Get list of supported languages"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT code, name, native_name, is_active
            FROM supported_languages
            WHERE is_active = 1
            ORDER BY sort_order, name
        """)
        
        languages = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        return languages
    
    @staticmethod
    def add_custom_translation(language_code: str, key: str, value: str, context: str = None) -> bool:
        """Add or update a custom translation"""
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT OR REPLACE INTO translations 
                (language_code, translation_key, translation_value, context, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (language_code, key, value, context))
            
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

def get_current_language() -> str:
    """Get current user's language or session language"""
    # Check session first
    if 'language' in session:
        return session['language']
    
    # Check user settings if logged in
    user_id = session.get('user_id')
    if user_id:
        return TranslationService.get_user_language(user_id)
    
    # Check browser Accept-Language header
    if request and hasattr(request, 'accept_languages'):
        browser_langs = request.accept_languages
        supported = [lang['code'] for lang in TranslationService.get_supported_languages()]
        
        for lang in browser_langs:
            lang_code = lang[0].split('-')[0]  # Get primary language code
            if lang_code in supported:
                return lang_code
    
    return 'en'  # Default fallback

def t(key: str, **kwargs) -> str:
    """Translation function (similar to gettext)"""
    language = get_current_language()
    translation = TranslationService.translate(key, language)
    
    # Simple string formatting if kwargs provided
    if kwargs:
        try:
            translation = translation.format(**kwargs)
        except (KeyError, ValueError):
            pass  # Ignore formatting errors
    
    return translation

# Flask routes
@i18n_bp.route('/set_language', methods=['POST'])
def set_language():
    """Set user's language preference"""
    data = request.get_json()
    language_code = data.get('language_code')
    
    if not language_code:
        return jsonify({'error': 'Language code required'}), 400
    
    # Check if language is supported
    supported = [lang['code'] for lang in TranslationService.get_supported_languages()]
    if language_code not in supported:
        return jsonify({'error': 'Language not supported'}), 400
    
    # Set in session
    session['language'] = language_code
    
    # If user is logged in, save to database
    user_id = session.get('user_id')
    if user_id:
        success = TranslationService.set_user_language(user_id, language_code)
        if not success:
            return jsonify({'error': 'Failed to save language preference'}), 500
    
    return jsonify({'message': 'Language updated successfully', 'language': language_code})

@i18n_bp.route('/translations')
def get_translations_api():
    """Get translations for current language"""
    language = request.args.get('lang', get_current_language())
    translations = TranslationService.get_translations(language)
    
    return jsonify({
        'language': language,
        'translations': translations
    })

@i18n_bp.route('/supported_languages')
def get_supported_languages_api():
    """Get list of supported languages"""
    languages = TranslationService.get_supported_languages()
    current_language = get_current_language()
    
    return jsonify({
        'languages': languages,
        'current': current_language
    })

@i18n_bp.route('/add_translation', methods=['POST'])
def add_translation():
    """Add custom translation (admin only)"""
    # Check if user is admin
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    language_code = data.get('language_code')
    key = data.get('key')
    value = data.get('value')
    context = data.get('context')
    
    if not all([language_code, key, value]):
        return jsonify({'error': 'Language code, key, and value required'}), 400
    
    success = TranslationService.add_custom_translation(language_code, key, value, context)
    
    if success:
        return jsonify({'message': 'Translation added successfully'})
    else:
        return jsonify({'error': 'Failed to add translation'}), 500

# Jinja2 template filters
def register_i18n_filters(app):
    """Register internationalization filters for Jinja2"""
    
    @app.template_filter('translate')
    def translate_filter(key, **kwargs):
        """Template filter for translations"""
        return t(key, **kwargs)
    
    @app.template_global()
    def get_language():
        """Get current language in templates"""
        return get_current_language()
    
    @app.template_global()
    def get_translations():
        """Get all translations for current language"""
        return TranslationService.get_translations(get_current_language())

def format_date_localized(date_obj, user_id: int = None) -> str:
    """Format date according to user's locale preferences"""
    if not user_id:
        user_id = session.get('user_id')
    
    # Get user's date format preference
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    cur.execute("SELECT date_format FROM language_settings WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    
    date_format = result[0] if result else 'MM/dd/yyyy'
    
    # Convert format string
    format_map = {
        'MM/dd/yyyy': '%m/%d/%Y',
        'dd/MM/yyyy': '%d/%m/%Y',
        'yyyy-MM-dd': '%Y-%m-%d',
        'dd.MM.yyyy': '%d.%m.%Y'
    }
    
    python_format = format_map.get(date_format, '%m/%d/%Y')
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
        except ValueError:
            return date_obj
    
    return date_obj.strftime(python_format)

# Initialize tables when module is imported
init_i18n_tables()

def register_i18n_routes(app):
    """Register i18n blueprint with Flask app"""
    app.register_blueprint(i18n_bp)
    register_i18n_filters(app)