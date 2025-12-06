"""
Helper functions for the Municipal Complaint Management System
"""
from datetime import datetime, timedelta
from bson import ObjectId
import random
import string

def generate_complaint_id():
    """Generate a unique complaint ID"""
    prefix = 'COM'
    timestamp = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{timestamp}-{random_str}"

def calculate_sla_deadline(priority, created_at):
    """Calculate SLA deadline based on priority"""
    from config import Config
    days = Config.SLA_DAYS.get(priority, 5)
    return created_at + timedelta(days=days)

def get_status_badge_color(status):
    """Get color for status badge"""
    colors = {
        'Pending': '#f59e0b',
        'Acknowledged': '#3b82f6',
        'In Progress': '#6366f1',
        'Under Review': '#8b5cf6',
        'Resolved': '#10b981',
        'Closed': '#64748b',
        'Rejected': '#ef4444'
    }
    return colors.get(status, '#64748b')

def get_priority_color(priority):
    """Get color for priority badge"""
    from config import Config
    return Config.PRIORITY_LEVELS.get(priority, {}).get('color', '#64748b')

def format_datetime(dt, format_str='%B %d, %Y at %I:%M %p'):
    """Format datetime object"""
    if dt is None:
        return 'N/A'
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return 'N/A'
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    return str(dt)

def calculate_time_ago(dt):
    """Calculate human-readable time ago"""
    if dt is None:
        return 'N/A'
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return 'N/A'
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def is_sla_breached(deadline):
    """Check if SLA deadline has been breached"""
    if deadline is None:
        return False
    return datetime.utcnow() > deadline

def get_complaint_age(created_at):
    """Get complaint age in days"""
    if created_at is None:
        return 0
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            return 0
    diff = datetime.utcnow() - created_at
    return diff.days

def paginate(items, page, per_page):
    """Paginate a list of items"""
    total = len(items)
    pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], page, pages, total

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename[:255]

def get_file_size_mb(file_size):
    """Convert file size to MB"""
    return round(file_size / (1024 * 1024), 2)

