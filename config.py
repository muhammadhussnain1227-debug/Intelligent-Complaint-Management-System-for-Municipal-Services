"""
Configuration file for the Municipal Complaint Management System
Professional Edition
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-secret-key-in-production-2025'
    
    # MongoDB Configuration
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/'
    # Separate databases for users and complaints
    USERS_DATABASE_NAME = os.environ.get('USERS_DATABASE_NAME') or 'municipal_users'
    COMPLAINTS_DATABASE_NAME = os.environ.get('COMPLAINTS_DATABASE_NAME') or 'municipal_complaints'
    # Legacy support - if DATABASE_NAME is set, use it for complaints
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or COMPLAINTS_DATABASE_NAME
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload Configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'mp4', 'mov', 'avi'}
    
    # Email Configuration (Optional - Set via environment variables)
    ENABLE_EMAIL_NOTIFICATIONS = os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() == 'true'
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    
    # Application Settings
    COMPLAINT_CATEGORIES = [
        'Garbage Collection',
        'Road Damage',
        'Water Leakage',
        'Drainage Problems',
        'Streetlight Malfunction',
        'Potholes',
        'Tree Maintenance',
        'Public Toilets',
        'Parks & Recreation',
        'Noise Complaints',
        'Parking Issues',
        'Other'
    ]
    
    # Priority Levels
    PRIORITY_LEVELS = {
        'Low': {'color': '#10b981', 'days': 7},
        'Normal': {'color': '#3b82f6', 'days': 5},
        'High': {'color': '#f59e0b', 'days': 3},
        'Urgent': {'color': '#ef4444', 'days': 1}
    }
    
    # Status Options
    STATUS_OPTIONS = [
        'Pending',
        'Acknowledged',
        'In Progress',
        'Under Review',
        'Resolved',
        'Closed',
        'Rejected'
    ]
    
    # Departments with staff assignment
    DEPARTMENTS = {
        'Garbage Collection': {
            'name': 'Sanitation Department',
            'code': 'SAN',
            'email': 'sanitation@municipal.gov'
        },
        'Road Damage': {
            'name': 'Public Works Department',
            'code': 'PWD',
            'email': 'publicworks@municipal.gov'
        },
        'Potholes': {
            'name': 'Public Works Department',
            'code': 'PWD',
            'email': 'publicworks@municipal.gov'
        },
        'Water Leakage': {
            'name': 'Water Department',
            'code': 'WTR',
            'email': 'water@municipal.gov'
        },
        'Drainage Problems': {
            'name': 'Public Works Department',
            'code': 'PWD',
            'email': 'publicworks@municipal.gov'
        },
        'Streetlight Malfunction': {
            'name': 'Electrical Department',
            'code': 'ELC',
            'email': 'electrical@municipal.gov'
        },
        'Tree Maintenance': {
            'name': 'Parks & Recreation Department',
            'code': 'PRK',
            'email': 'parks@municipal.gov'
        },
        'Parks & Recreation': {
            'name': 'Parks & Recreation Department',
            'code': 'PRK',
            'email': 'parks@municipal.gov'
        },
        'Public Toilets': {
            'name': 'Public Facilities Department',
            'code': 'PFD',
            'email': 'facilities@municipal.gov'
        },
        'Noise Complaints': {
            'name': 'Public Safety Department',
            'code': 'PSD',
            'email': 'safety@municipal.gov'
        },
        'Parking Issues': {
            'name': 'Traffic & Parking Department',
            'code': 'TPD',
            'email': 'traffic@municipal.gov'
        },
        'Other': {
            'name': 'General Services Department',
            'code': 'GSD',
            'email': 'general@municipal.gov'
        }
    }
    
    # SLA Configuration (Service Level Agreement)
    SLA_DAYS = {
        'Low': 7,
        'Normal': 5,
        'High': 3,
        'Urgent': 1
    }
    
    # Notification Settings
    ENABLE_EMAIL_NOTIFICATIONS = os.environ.get('ENABLE_EMAIL', 'False').lower() == 'true'
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    
    # Pagination
    ITEMS_PER_PAGE = 10
    ADMIN_ITEMS_PER_PAGE = 20
    
    # File Paths
    REPORTS_FOLDER = 'static/reports'
    EXPORTS_FOLDER = 'static/exports'
    
    # Application Info
    APP_NAME = 'Municipal Complaint Management System'
    APP_VERSION = '2.0.0'
    ORGANIZATION_NAME = 'Municipal Corporation'

