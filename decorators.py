"""
Decorators for route protection and validation
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify

def login_required(f):
    """Decorator for routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator for routes that require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        # Import here to avoid circular imports
        from app import users_db
        if users_db is None:
            flash('Database connection error', 'danger')
            return redirect(url_for('index'))
        
        from bson import ObjectId
        try:
            user = users_db.users.find_one({'_id': ObjectId(session['user_id'])})
            if not user or user.get('role') != 'admin':
                if request.is_json:
                    return jsonify({'error': 'Admin access required'}), 403
                flash('Admin access required', 'danger')
                return redirect(url_for('index'))
        except Exception as e:
            print(f"Admin check error: {e}")
            flash('Error verifying admin access', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    """Decorator for routes that require staff (admin or department staff) access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        # Import here to avoid circular imports
        from app import users_db
        if users_db is None:
            flash('Database connection error', 'danger')
            return redirect(url_for('index'))
        
        from bson import ObjectId
        try:
            user = users_db.users.find_one({'_id': ObjectId(session['user_id'])})
            if not user or user.get('role') not in ['admin', 'staff']:
                if request.is_json:
                    return jsonify({'error': 'Staff access required'}), 403
                flash('Staff access required', 'danger')
                return redirect(url_for('index'))
        except Exception as e:
            print(f"Staff check error: {e}")
            flash('Error verifying staff access', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

