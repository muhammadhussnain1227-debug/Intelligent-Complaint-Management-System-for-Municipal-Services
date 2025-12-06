"""
Municipal Complaint Management System
Professional Edition v2.0
Main Flask Application with Advanced Features
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import bcrypt
from pymongo import MongoClient
from bson import ObjectId
import json
from config import Config
from utils.helpers import *
from utils.decorators import login_required, admin_required, staff_required

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Make config available to templates
@app.context_processor
def inject_config():
    return dict(config=app.config)

# MongoDB Connection - Separate databases for users and complaints
try:
    client = MongoClient(app.config['MONGODB_URI'], serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    
    # Separate databases
    users_db = client[app.config['USERS_DATABASE_NAME']]
    complaints_db = client[app.config['COMPLAINTS_DATABASE_NAME']]
    
    # Legacy support - maintain 'db' variable for complaints
    db = complaints_db
    
    print("✓ Connected to MongoDB successfully")
    print(f"  - Users Database: {app.config['USERS_DATABASE_NAME']}")
    print(f"  - Complaints Database: {app.config['COMPLAINTS_DATABASE_NAME']}")
except Exception as e:
    print(f"✗ MongoDB connection error: {e}")
    print("\n" + "="*60)
    print("MongoDB Setup Instructions:")
    print("="*60)
    print("\nOption 1: Start Local MongoDB")
    print("  - Windows: Start 'MongoDB' service from Services")
    print("  - Or run: net start MongoDB")
    print("  - Download: https://www.mongodb.com/try/download/community")
    print("\nOption 2: Use MongoDB Atlas (Cloud - Free)")
    print("  - Sign up: https://www.mongodb.com/cloud/atlas")
    print("  - Create free cluster")
    print("  - Get connection string")
    print("  - Update MONGODB_URI in config.py")
    print("\n" + "="*60)
    users_db = None
    complaints_db = None
    db = None

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# Create reports and exports folders if they don't exist
reports_folder = os.path.join('static', 'reports')
exports_folder = os.path.join('static', 'exports')
os.makedirs(reports_folder, exist_ok=True)
os.makedirs(exports_folder, exist_ok=True)

# Database Initialization Function
def initialize_database():
    """Initialize MongoDB databases and collections"""
    if complaints_db is None or users_db is None:
        print("⚠️  Cannot initialize databases - connection not available")
        return
    
    try:
        # Initialize activity_logs collection (create if doesn't exist)
        if 'activity_logs' not in complaints_db.list_collection_names():
            complaints_db.activity_logs.insert_one({
                'initialized': datetime.utcnow(),
                'type': 'initialization'
            })
            # Remove the initialization document
            complaints_db.activity_logs.delete_one({'type': 'initialization'})
            print("✓ Activity logs collection initialized")
        
        # Initialize category collections (create if don't exist)
        for category in app.config['COMPLAINT_CATEGORIES']:
            collection_name = get_category_collection_name(category)
            collection = get_category_collection(category)
            if collection is not None:
                # Check if collection exists by trying to count
                try:
                    collection.count_documents({})
                    print(f"✓ Collection '{collection_name}' ready")
                except:
                    # Collection doesn't exist, create it by inserting a temp doc
                    temp_doc = {
                        'initialized': datetime.utcnow(),
                        'type': 'initialization',
                        'category': category
                    }
                    collection.insert_one(temp_doc)
                    collection.delete_one({'type': 'initialization'})
                    print(f"✓ Collection '{collection_name}' created")
        
        # Print database structure
        print("\n" + "="*60)
        print("DATABASE STRUCTURE")
        print("="*60)
        print(f"\n📊 Complaints Database: {app.config['COMPLAINTS_DATABASE_NAME']}")
        collections_list = complaints_db.list_collection_names()
        if collections_list:
            print(f"   Collections ({len(collections_list)}):")
            for coll_name in sorted(collections_list):
                count = complaints_db[coll_name].count_documents({})
                print(f"   - {coll_name}: {count} documents")
        else:
            print("   ⚠️  No collections found (collections will be created when first complaint is saved)")
        
        print(f"\n👥 Users Database: {app.config['USERS_DATABASE_NAME']}")
        users_collections = users_db.list_collection_names()
        if users_collections:
            print(f"   Collections ({len(users_collections)}):")
            for coll_name in sorted(users_collections):
                count = users_db[coll_name].count_documents({})
                print(f"   - {coll_name}: {count} documents")
        else:
            print("   ⚠️  No collections found")
        
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"⚠️  Error initializing databases: {e}")
        import traceback
        traceback.print_exc()

# JSON Encoder for ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_encoder = JSONEncoder

# Jinja2 Filters
@app.template_filter('datetime')
def datetime_filter(value, format='%B %d, %Y at %I:%M %p'):
    return format_datetime(value, format)

@app.template_filter('time_ago')
def time_ago_filter(value):
    return calculate_time_ago(value)

@app.template_filter('status_color')
def status_color_filter(value):
    return get_status_badge_color(value)

@app.template_filter('priority_color')
def priority_color_filter(value):
    return get_priority_color(value)

# Helper Functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_category_collection_name(category):
    """Convert category name to a valid MongoDB collection name"""
    # Replace spaces and special characters with underscores, lowercase
    collection_name = category.lower().replace(' ', '_').replace('&', 'and')
    collection_name = ''.join(c for c in collection_name if c.isalnum() or c == '_')
    return f"complaints_{collection_name}"

def get_category_collection(category):
    """Get the MongoDB collection for a specific category"""
    if complaints_db is None:
        return None
    collection_name = get_category_collection_name(category)
    return complaints_db[collection_name]

def get_complaint_from_all_collections(complaint_id):
    """Search for a complaint across all category collections by ID"""
    if complaints_db is None:
        print("ERROR: complaints_db is None in get_complaint_from_all_collections")
        return None, None
    
    if not complaint_id:
        print("ERROR: complaint_id is empty")
        return None, None
    
    print(f"DEBUG: Searching for complaint with ID: {complaint_id}")
    
    # Try to find in all category collections
    for category in app.config['COMPLAINT_CATEGORIES']:
        try:
            collection = get_category_collection(category)
            if collection is None:
                continue
            
            # Try by _id first (as ObjectId)
            try:
                complaint = collection.find_one({'_id': ObjectId(complaint_id)})
                if complaint:
                    print(f"DEBUG: Found complaint in collection '{collection.name}' by _id")
                    return complaint, collection
            except Exception as e:
                # If ObjectId conversion fails, continue to try other methods
                pass
            
            # Also try by complaint_id field (string match)
            try:
                complaint = collection.find_one({'complaint_id': complaint_id})
                if complaint:
                    print(f"DEBUG: Found complaint in collection '{collection.name}' by complaint_id field")
                    return complaint, collection
            except Exception as e:
                pass
            
            # Try as string _id if complaint_id was passed as string
            try:
                complaint = collection.find_one({'_id': complaint_id})
                if complaint:
                    print(f"DEBUG: Found complaint in collection '{collection.name}' by _id (string)")
                    return complaint, collection
            except:
                pass
                
        except Exception as e:
            print(f"Error searching collection {category}: {e}")
            continue
    
    print(f"DEBUG: Complaint not found in any collection for ID: {complaint_id}")
    return None, None

def query_all_category_collections(query, sort=None, skip=0, limit=None):
    """Query across all category collections and combine results"""
    if complaints_db is None:
        return []
    
    all_results = []
    for category in app.config['COMPLAINT_CATEGORIES']:
        try:
            collection = get_category_collection(category)
            if collection is None:
                continue
            cursor = collection.find(query)
            if sort:
                cursor = cursor.sort(sort[0], sort[1] if len(sort) > 1 else 1)
            results = list(cursor)
            all_results.extend(results)
        except Exception as e:
            print(f"Error querying collection {category}: {e}")
            continue
    
    # Sort all results if sort is provided
    if sort and all_results:
        reverse = sort[1] == -1 if len(sort) > 1 else False
        sort_key = sort[0]
        all_results.sort(key=lambda x: x.get(sort_key, datetime.min), reverse=reverse)
    
    # Apply skip and limit
    if skip > 0:
        all_results = all_results[skip:]
    if limit:
        all_results = all_results[:limit]
    
    return all_results

def count_all_category_collections(query):
    """Count documents matching query across all category collections"""
    if complaints_db is None:
        return 0
    
    total = 0
    for category in app.config['COMPLAINT_CATEGORIES']:
        try:
            collection = get_category_collection(category)
            if collection is None:
                continue
            total += collection.count_documents(query)
        except Exception as e:
            print(f"Error counting collection {category}: {e}")
            continue
    
    return total

def log_activity(complaint_id, action, user_id, details=None):
    """Log activity for audit trail"""
    if complaints_db is None:
        return
    
    try:
        activity = {
            'complaint_id': ObjectId(complaint_id) if isinstance(complaint_id, str) else complaint_id,
            'action': action,
            'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id,
            'details': details or {},
            'timestamp': datetime.utcnow(),
            'ip_address': request.remote_addr if request else 'N/A'
        }
        complaints_db.activity_logs.insert_one(activity)
    except Exception as e:
        print(f"Error logging activity: {e}")

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    # Get statistics for homepage
    stats = {}
    if db is not None:
        try:
            stats = {
                'total_complaints': count_all_category_collections({}),
                'resolved': count_all_category_collections({'status': 'Resolved'}),
                'total_users': users_db.users.count_documents({'role': 'citizen'})
            }
        except:
            stats = {'total_complaints': 0, 'resolved': 0, 'total_users': 0}
    
    return render_template('index.html', stats=stats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([name, email, phone, password, confirm_password]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
            return render_template('register.html')
        
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        if users_db is None:
            flash('Database connection error. Please try again later.', 'danger')
            return render_template('register.html')
        
        existing_user = users_db.users.find_one({'email': email})
        if existing_user:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('login'))
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        try:
            user = {
                'name': name,
                'email': email,
                'phone': phone,
                'password': password_hash,
                'role': 'citizen',
                'created_at': datetime.utcnow(),
                'last_login': None,
                'is_active': True,
                'profile': {
                    'address': '',
                    'city': '',
                    'pincode': ''
                }
            }
            
            # Insert user into users database
            result = users_db.users.insert_one(user)
            
            # Verify insertion was successful
            if not result.inserted_id:
                flash('Registration failed. Please try again.', 'danger')
                print("ERROR: User insertion failed - no inserted_id returned")
                return render_template('register.html')
            
            # Verify user was actually saved
            saved_user = users_db.users.find_one({'_id': result.inserted_id})
            if not saved_user:
                flash('Registration failed. Please try again.', 'danger')
                print(f"ERROR: User with ID {result.inserted_id} not found after insertion")
                return render_template('register.html')
            
            print(f"✓ User registered successfully: {email} (ID: {result.inserted_id})")
            
            # Set session variables
            session['user_id'] = str(result.inserted_id)
            session['user_name'] = name
            session['user_role'] = 'citizen'
            session['user_email'] = email
            
            flash('Registration successful! Welcome to the Municipal Complaint System.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"ERROR during user registration: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            flash(f'Registration failed: {str(e)}. Please try again.', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'danger')
            return render_template('login.html')
        
        if users_db is None:
            flash('Database connection error. Please try again later.', 'danger')
            return render_template('login.html')
        
        # Find user
        user = users_db.users.find_one({'email': email})
        
        if not user:
            print(f"LOGIN ERROR: User not found for email: {email}")
            flash('Invalid email or password', 'danger')
            return render_template('login.html')
        
        # Debug: Check user details
        print(f"LOGIN: User found - Email: {user.get('email')}, Role: {user.get('role')}, Active: {user.get('is_active')}")
        
        # Check password
        try:
            password_match = bcrypt.checkpw(password.encode('utf-8'), user['password'])
            print(f"LOGIN: Password match: {password_match}")
        except Exception as e:
            print(f"LOGIN ERROR: Password check failed - {str(e)}")
            flash('Invalid email or password', 'danger')
            return render_template('login.html')
        
        if password_match:
            if not user.get('is_active', True):
                flash('Your account has been deactivated. Please contact admin.', 'danger')
                return render_template('login.html')
            
            # Update last login
            users_db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'last_login': datetime.utcnow()}}
            )
            
            user_role = user.get('role', 'citizen')
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['name']
            session['user_role'] = user_role
            session['user_email'] = user['email']
            
            print(f"LOGIN SUCCESS: User {user.get('email')} logged in with role: {user_role}")
            print(f"LOGIN: Session set - user_id: {session.get('user_id')}, role: {session.get('user_role')}")
            
            flash(f'Welcome back, {user["name"]}!', 'success')
            
            # Redirect based on role
            if user_role == 'admin':
                print("LOGIN: Redirecting to admin_dashboard")
                return redirect(url_for('admin_dashboard'))
            elif user_role == 'staff':
                print("LOGIN: Redirecting to staff_dashboard")
                return redirect(url_for('staff_dashboard'))
            else:
                print("LOGIN: Redirecting to dashboard (citizen)")
                return redirect(url_for('dashboard'))
        else:
            print(f"LOGIN ERROR: Password mismatch for user: {email}")
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

# ==================== CITIZEN ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Citizen dashboard - view their complaints"""
    if complaints_db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    
    # Build query
    query = {'user_id': ObjectId(user_id)}
    if status_filter:
        query['status'] = status_filter
    if category_filter:
        query['category'] = category_filter
    
    # Get complaints (across all category collections or specific category)
    if category_filter:
        # Query specific category collection
        category_collection = get_category_collection(category_filter)
        if category_collection is not None:
            total = category_collection.count_documents(query)
            complaints = list(category_collection.find(query)
                             .sort('created_at', -1)
                             .skip((page - 1) * app.config['ITEMS_PER_PAGE'])
                             .limit(app.config['ITEMS_PER_PAGE']))
        else:
            total = 0
            complaints = []
    else:
        # Query all category collections
        total = count_all_category_collections(query)
        skip = (page - 1) * app.config['ITEMS_PER_PAGE']
        complaints = query_all_category_collections(query, sort=('created_at', -1), skip=skip, limit=app.config['ITEMS_PER_PAGE'])
    
    # Convert ObjectIds
    for complaint in complaints:
        complaint['_id'] = str(complaint['_id'])
        complaint['user_id'] = str(complaint['user_id'])
        complaint['age'] = get_complaint_age(complaint.get('created_at'))
    
    # Calculate pagination
    total_pages = (total + app.config['ITEMS_PER_PAGE'] - 1) // app.config['ITEMS_PER_PAGE']
    
    # Get statistics (across all category collections)
    stats = {
        'total': count_all_category_collections({'user_id': ObjectId(user_id)}),
        'pending': count_all_category_collections({'user_id': ObjectId(user_id), 'status': 'Pending'}),
        'in_progress': count_all_category_collections({'user_id': ObjectId(user_id), 'status': 'In Progress'}),
        'resolved': count_all_category_collections({'user_id': ObjectId(user_id), 'status': 'Resolved'})
    }
    
    return render_template('dashboard.html', 
                         complaints=complaints,
                         stats=stats,
                         page=page,
                         total_pages=total_pages,
                         status_filter=status_filter,
                         category_filter=category_filter,
                         categories=app.config['COMPLAINT_CATEGORIES'],
                         statuses=app.config['STATUS_OPTIONS'])

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    if complaints_db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    user = users_db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('logout'))
    
    user['_id'] = str(user['_id'])
    
    # Get user statistics (across all category collections)
    user_stats = {
        'total_complaints': count_all_category_collections({'user_id': ObjectId(session['user_id'])}),
        'resolved': count_all_category_collections({'user_id': ObjectId(session['user_id']), 'status': 'Resolved'}),
        'pending': count_all_category_collections({'user_id': ObjectId(session['user_id']), 'status': 'Pending'})
    }
    
    return render_template('profile.html', user=user, stats=user_stats)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    pincode = request.form.get('pincode', '').strip()
    
    update_data = {
        'name': name,
        'phone': phone,
        'profile.address': address,
        'profile.city': city,
        'profile.pincode': pincode,
        'updated_at': datetime.utcnow()
    }
    
    # Use dot notation properly for nested fields
    users_db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {
            'name': name,
            'phone': phone,
            'profile': {
                'address': address,
                'city': city,
                'pincode': pincode
            },
            'updated_at': datetime.utcnow()
        }}
    )
    
    session['user_name'] = name
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/submit_complaint', methods=['GET', 'POST'])
@login_required
def submit_complaint():
    """Submit a new complaint"""
    print("\n" + "="*70)
    print("DEBUG: ===== COMPLAINT SUBMISSION STARTED =====")
    print("="*70)
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request URL: {request.url}")
    print(f"DEBUG: Request endpoint: {request.endpoint}")
    
    if request.method == 'POST':
        print("DEBUG: POST request received - processing complaint submission")
        print(f"DEBUG: User ID from session: {session.get('user_id')}")
        print(f"DEBUG: User role: {session.get('user_role')}")
        
        if complaints_db is None or users_db is None:
            print("ERROR: Database connections are None!")
            print(f"  - complaints_db: {complaints_db}")
            print(f"  - users_db: {users_db}")
            flash('Database connection error', 'danger')
            return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
        
        print("DEBUG: Database connections OK")
        
        # Get form data with detailed logging
        print("\nDEBUG: --- Extracting Form Data ---")
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Normal').strip()
        is_urgent = request.form.get('is_urgent', '').lower() in ['true', 'on', '1']
        
        print(f"DEBUG: Category: '{category}'")
        print(f"DEBUG: Location: '{location}'")
        print(f"DEBUG: Description length: {len(description)} characters")
        print(f"DEBUG: Description preview: '{description[:100]}...' if len(description) > 100 else description")
        print(f"DEBUG: Priority: '{priority}'")
        print(f"DEBUG: Is urgent: {is_urgent}")
        print(f"DEBUG: All form keys: {list(request.form.keys())}")
        print(f"DEBUG: Files in request: {list(request.files.keys())}")
        
        # Validate required fields
        print("\nDEBUG: --- Validating Form Data ---")
        if not all([category, location, description]):
            print("ERROR: Missing required fields!")
            print(f"  - Category present: {bool(category)}")
            print(f"  - Location present: {bool(location)}")
            print(f"  - Description present: {bool(description)}")
            flash('Category, location, and description are required', 'danger')
            return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
        print("DEBUG: All required fields present")
        
        if len(description) < 10:
            print(f"ERROR: Description too short: {len(description)} characters")
            flash('Description must be at least 10 characters long', 'danger')
            return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
        print(f"DEBUG: Description length OK: {len(description)} characters")
        
        # Validate category
        print(f"DEBUG: Validating category '{category}' against: {app.config['COMPLAINT_CATEGORIES']}")
        if category not in app.config['COMPLAINT_CATEGORIES']:
            print(f"ERROR: Invalid category '{category}'")
            flash('Invalid category selected', 'danger')
            return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
        print(f"DEBUG: Category validation passed")
        
        # Validate priority
        if priority not in app.config['PRIORITY_LEVELS']:
            print(f"DEBUG: Invalid priority '{priority}', defaulting to 'Normal'")
            priority = 'Normal'
        print(f"DEBUG: Final priority: '{priority}'")
        
        # Handle file upload
        print("\nDEBUG: --- Processing File Upload ---")
        photo_path = None
        if 'photo' in request.files:
            print("DEBUG: Photo field found in request.files")
            file = request.files['photo']
            print(f"DEBUG: File object: {file}")
            print(f"DEBUG: Filename: {file.filename}")
            if file and file.filename and allowed_file(file.filename):
                print(f"DEBUG: File is valid, processing...")
                filename = secure_filename(file.filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"DEBUG: Saving file to: {filepath}")
                file.save(filepath)
                photo_path = f"uploads/{filename}"
                print(f"DEBUG: File saved successfully: {photo_path}")
            else:
                print(f"DEBUG: File upload skipped or invalid")
        else:
            print("DEBUG: No photo field in request")
        
        # Assign department based on category
        print("\nDEBUG: --- Preparing Complaint Document ---")
        department_info = app.config['DEPARTMENTS'].get(category, app.config['DEPARTMENTS'].get('Other', {'name': 'General Department', 'code': 'GEN'}))
        print(f"DEBUG: Department assigned: {department_info.get('name')} ({department_info.get('code')})")
        
        # Generate complaint ID
        complaint_id = generate_complaint_id()
        print(f"DEBUG: Generated complaint ID: {complaint_id}")
        
        # Set final priority (urgent overrides)
        final_priority = 'Urgent' if is_urgent else priority
        print(f"DEBUG: Final priority: {final_priority} (urgent={is_urgent}, original={priority})")
        
        # Calculate SLA deadline
        created_at = datetime.utcnow()
        sla_deadline = calculate_sla_deadline(final_priority, created_at)
        print(f"DEBUG: Created at: {created_at}")
        print(f"DEBUG: SLA deadline: {sla_deadline}")
        
        # Create complaint document
        print("\nDEBUG: Creating complaint document structure...")
        complaint_doc = {
            'complaint_id': complaint_id,
            'user_id': ObjectId(session['user_id']),
            'category': category,
            'location': location,
            'description': description,
            'status': 'Pending',
            'priority': final_priority,
            'is_urgent': is_urgent,
            'department': department_info.get('name', 'General Department'),
            'department_code': department_info.get('code', 'GEN'),
            'assigned_to': None,
            'created_at': created_at,
            'updated_at': created_at,
            'sla_deadline': sla_deadline,
            'sla_breached': False,
            'comments': [],
            'progress': [],  # Progress tracking
            'proof_images': [],  # For worker proof uploads
            'feedback': None  # For rating system
        }
        
        # Add photo fields if image was uploaded
        if photo_path:
            complaint_doc['image_path'] = photo_path
            complaint_doc['photo'] = photo_path
        
        # Insert complaint into category-specific collection
        print("\nDEBUG: --- Database Insertion Started ---")
        print(f"DEBUG: Database name: {app.config['COMPLAINTS_DATABASE_NAME']}")
        print(f"DEBUG: Category: {category}")
        print(f"DEBUG: User ID: {session['user_id']}")
        print(f"DEBUG: Complaint document contains {len(complaint_doc)} fields:")
        for key, value in complaint_doc.items():
            if key == 'description':
                print(f"  - {key}: '{str(value)[:50]}...' (length: {len(str(value))})")
            elif isinstance(value, ObjectId):
                print(f"  - {key}: ObjectId('{value}')")
            else:
                print(f"  - {key}: {value}")
        
        try:
            if complaints_db is None:
                print("ERROR: complaints_db is None!")
                flash('Database connection error', 'danger')
                return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
            
            print("DEBUG: complaints_db connection OK")
            
            # Get the category-specific collection
            collection_name = get_category_collection_name(category)
            print(f"DEBUG: Collection name for category '{category}': {collection_name}")
            
            category_collection = get_category_collection(category)
            print(f"DEBUG: Category collection object: {category_collection}")
            
            if category_collection is None:
                print("ERROR: Could not get category collection!")
                print(f"DEBUG: Tried to get collection: {collection_name}")
                flash('Database connection error', 'danger')
                return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
            
            print(f"DEBUG: Category collection retrieved successfully")
            print(f"DEBUG: Collection database: {category_collection.database.name}")
            print(f"DEBUG: Collection name: {category_collection.name}")
            
            # Insert into category-specific collection
            print(f"\nDEBUG: Attempting to insert document into collection...")
            result = category_collection.insert_one(complaint_doc)
            print(f"DEBUG: Insert operation completed")
            print(f"DEBUG: Insert result type: {type(result)}")
            print(f"DEBUG: Insert result object: {result}")
            print(f"DEBUG: Inserted ID: {result.inserted_id}")
            
            if not result.inserted_id:
                print("ERROR: No inserted_id returned from insert_one()!")
                flash('Error: Failed to save complaint to database', 'danger')
                return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
            
            print(f"DEBUG: Document inserted with ID: {result.inserted_id}")
            
            # Verify the complaint was saved
            print(f"DEBUG: Verifying document was saved...")
            saved_complaint = category_collection.find_one({'_id': result.inserted_id})
            if not saved_complaint:
                print("ERROR: Complaint was not found after insert!")
                print(f"DEBUG: Searched for _id: {result.inserted_id}")
                print(f"DEBUG: Collection document count: {category_collection.count_documents({})}")
                flash('Error: Complaint was not saved correctly', 'danger')
                return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
            
            print(f"DEBUG: ✓ Verification passed - document found in database")
            print(f"DEBUG: Saved document keys: {list(saved_complaint.keys())}")
            
            print(f"\n{'='*70}")
            print(f"✓ SUCCESS: Complaint saved successfully!")
            print(f"  - Complaint ID: {complaint_id}")
            print(f"  - MongoDB _id: {result.inserted_id}")
            print(f"  - Collection: {collection_name}")
            print(f"  - Database: {app.config['COMPLAINTS_DATABASE_NAME']}")
            print(f"  - Full path: {app.config['COMPLAINTS_DATABASE_NAME']}.{collection_name}")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"✗ ERROR: Database insert failed!")
            print(f"  - Error type: {type(e).__name__}")
            print(f"  - Error message: {str(e)}")
            print(f"{'='*70}")
            import traceback
            traceback.print_exc()
            flash(f'Error saving complaint: {str(e)}', 'danger')
            return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
        
        # Log activity
        print("\nDEBUG: Logging activity...")
        try:
            log_activity(str(result.inserted_id), 'complaint_created', session['user_id'], 
                        {'complaint_id': complaint_id, 'category': category})
            print("DEBUG: Activity logged successfully")
        except Exception as e:
            print(f"WARNING: Activity log error: {e}")
        
        # Send email notification
        print("DEBUG: Attempting email notification...")
        try:
            from utils.email_service import send_complaint_submitted_email
            user = users_db.users.find_one({'_id': ObjectId(session['user_id'])})
            if user:
                send_complaint_submitted_email(
                    user.get('email', ''),
                    user.get('name', 'User'),
                    complaint_id,
                    category
                )
                print("DEBUG: Email notification sent")
            else:
                print("DEBUG: User not found for email notification")
        except Exception as e:
            print(f"WARNING: Email notification error: {e}")
        
        print(f"\nDEBUG: Redirecting to track_complaint page with ID: {result.inserted_id}")
        flash(f'Complaint submitted successfully! Your complaint ID is {complaint_id}', 'success')
        return redirect(url_for('track_complaint', complaint_id=str(result.inserted_id)))
    
    print("DEBUG: GET request - rendering form")
    return render_template('submit_complaint.html', 
                         categories=app.config['COMPLAINT_CATEGORIES'],
                         priorities=list(app.config['PRIORITY_LEVELS'].keys()))
    
    return render_template('submit_complaint.html', 
                         categories=app.config['COMPLAINT_CATEGORIES'],
                         priorities=list(app.config['PRIORITY_LEVELS'].keys()))

@app.route('/track_complaint/<complaint_id>')
@login_required
def track_complaint(complaint_id):
    """Track a specific complaint"""
    print(f"\n{'='*70}")
    print(f"DEBUG: track_complaint called with ID: {complaint_id}")
    print(f"{'='*70}")
    
    if db is None:
        print("ERROR: db is None")
        flash('Database connection error', 'danger')
        return render_template('track_complaint.html', complaint=None)
    
    try:
        complaint, category_collection = get_complaint_from_all_collections(complaint_id)
        
        if not complaint:
            print(f"ERROR: Complaint not found for ID: {complaint_id}")
            flash('Complaint not found', 'danger')
            return render_template('track_complaint.html', complaint=None)
        
        print(f"DEBUG: Found complaint - Category: {complaint.get('category')}, Status: {complaint.get('status')}")
        
        # Convert complaint to dict if it's not already
        if not isinstance(complaint, dict):
            print(f"WARNING: Complaint is not a dict, converting...")
            try:
                complaint = dict(complaint)
            except Exception as e:
                print(f"ERROR: Could not convert complaint to dict: {e}")
                flash('Invalid complaint data format', 'danger')
                return render_template('track_complaint.html', complaint=None)
        
        # Check if complaint is empty
        if not complaint or len(complaint) == 0:
            print(f"ERROR: Complaint is empty")
            flash('Complaint data is empty', 'danger')
            return render_template('track_complaint.html', complaint=None)
        
        # Store original _id as ObjectId before converting to string
        complaint_oid = None
        if '_id' in complaint and complaint['_id']:
            try:
                complaint_oid = ObjectId(complaint['_id']) if not isinstance(complaint['_id'], ObjectId) else complaint['_id']
                complaint['_id'] = str(complaint['_id'])
            except Exception as e:
                print(f"WARNING: Could not convert _id to ObjectId: {e}")
                complaint['_id'] = str(complaint.get('_id', complaint_id))
        else:
            print(f"ERROR: Complaint _id is missing")
            complaint['_id'] = str(complaint_id)
            try:
                complaint_oid = ObjectId(complaint_id)
            except:
                complaint_oid = None
        
        # Ensure all required fields exist
        complaint['user_id'] = str(complaint.get('user_id', ''))
        complaint['category'] = complaint.get('category', 'Unknown')
        complaint['location'] = complaint.get('location', 'N/A')
        complaint['description'] = complaint.get('description', 'No description provided')
        complaint['status'] = complaint.get('status', 'Pending')
        complaint['priority'] = complaint.get('priority', 'Normal')
        complaint['complaint_id'] = complaint.get('complaint_id', complaint['_id'][:8])
        complaint['department'] = complaint.get('department', 'General Department')
        complaint['department_code'] = complaint.get('department_code', 'GEN')
        complaint['is_urgent'] = complaint.get('is_urgent', False)
        complaint['created_at'] = complaint.get('created_at')
        complaint['updated_at'] = complaint.get('updated_at')
        complaint['sla_deadline'] = complaint.get('sla_deadline')
        
        # Check if user owns this complaint or is admin/staff
        user_role = session.get('user_role', 'citizen')
        if str(complaint['user_id']) != session['user_id'] and user_role not in ['admin', 'staff']:
            flash('You do not have access to this complaint', 'danger')
            return redirect(url_for('dashboard'))
        
        # Fix photo path
        if complaint.get('image_path') and not complaint.get('photo'):
            complaint['photo'] = complaint['image_path']
        elif complaint.get('photo') and not complaint.get('image_path'):
            complaint['image_path'] = complaint['photo']
        if complaint.get('photo'):
            if complaint['photo'].startswith('static/'):
                complaint['photo'] = complaint['photo'][7:]
            elif complaint['photo'].startswith('/static/'):
                complaint['photo'] = complaint['photo'][8:]
        
        # Get user info
        user = None
        if complaint.get('user_id'):
            try:
                user = users_db.users.find_one({'_id': ObjectId(complaint['user_id'])})
            except:
                pass
        
        if user:
            complaint['user_name'] = user.get('name', 'Unknown')
            complaint['user_email'] = user.get('email', 'Unknown')
        else:
            complaint['user_name'] = 'Unknown'
            complaint['user_email'] = 'Unknown'
        
        # Get assigned staff if any
        if complaint.get('assigned_to'):
            try:
                assigned_to_id = complaint['assigned_to']
                if isinstance(assigned_to_id, str):
                    assigned_to_id = ObjectId(assigned_to_id)
                staff = users_db.users.find_one({'_id': assigned_to_id})
                if staff:
                    complaint['assigned_staff_name'] = staff.get('name', 'Unknown')
            except Exception as e:
                print(f"Error getting assigned staff: {e}")
                complaint['assigned_staff_name'] = None
        
        # Get activity log
        activities = []
        try:
            if complaint_oid:
                activity_list = list(complaints_db.activity_logs.find({'complaint_id': complaint_oid})
                             .sort('timestamp', 1))
            else:
                activity_list = []
            
            for activity in activity_list:
                activity['_id'] = str(activity['_id'])
                if activity.get('user_id'):
                    activity['user_id'] = str(activity['user_id'])
                    user = users_db.users.find_one({'_id': ObjectId(activity['user_id'])})
                    activity['user_name'] = user.get('name', 'Unknown') if user else 'Unknown'
                else:
                    activity['user_name'] = 'Unknown'
                activities.append(activity)
        except Exception as e:
            print(f"Error getting activities: {e}")
        
        complaint['activities'] = activities
        complaint['age'] = get_complaint_age(complaint.get('created_at'))
        complaint['sla_breached'] = is_sla_breached(complaint.get('sla_deadline'))
        
        # Ensure comments, progress, and proof_images are lists
        if 'comments' not in complaint:
            complaint['comments'] = []
        if 'progress' not in complaint:
            complaint['progress'] = []
        if 'proof_images' not in complaint:
            complaint['proof_images'] = []
        
        # Ensure complaint is a dict before passing to template
        if not isinstance(complaint, dict):
            print(f"WARNING: Complaint is not a dict before template render, converting...")
            try:
                complaint = dict(complaint)
            except:
                print(f"ERROR: Could not convert complaint to dict")
                flash('Invalid complaint data format', 'danger')
                return render_template('track_complaint.html', complaint=None)
        
        # Ensure complaint is not empty
        if not complaint or len(complaint) == 0:
            print(f"ERROR: Complaint dict is empty before template render")
            flash('Complaint data is empty', 'danger')
            return render_template('track_complaint.html', complaint=None)
        
        print(f"DEBUG: Complaint data prepared - User: {complaint.get('user_name')}, Category: {complaint.get('category')}")
        print(f"DEBUG: Complaint keys count: {len(complaint.keys())}")
        print(f"DEBUG: Rendering template with complaint data")
        
        return render_template('track_complaint.html', complaint=complaint)
    except Exception as e:
        import traceback
        print(f"\n{'='*70}")
        print(f"ERROR in track_complaint: {e}")
        print(f"{'='*70}")
        traceback.print_exc()
        print(f"{'='*70}\n")
        flash(f'Error loading complaint: {str(e)}', 'danger')
        return render_template('track_complaint.html', complaint=None)

@app.route('/complaint/<complaint_id>/update', methods=['POST'])
@login_required
def update_complaint(complaint_id):
    """Update complaint (add comment from citizen)"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    try:
        complaint, category_collection = get_complaint_from_all_collections(complaint_id)
        if not complaint or str(complaint['user_id']) != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if category_collection is None:
            return jsonify({'success': False, 'message': 'Complaint collection not found'}), 404
        
        comment = request.json.get('comment', '').strip()
        if comment:
            comments = complaint.get('comments', [])
            comments.append({
                'comment': comment,
                'user_name': session.get('user_name', 'User'),
                'user_role': 'citizen',
                'timestamp': datetime.utcnow()
            })
            
            category_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {'$set': {
                    'comments': comments,
                    'updated_at': datetime.utcnow()
                }}
            )
            
            log_activity(complaint_id, 'comment_added', session['user_id'], {'comment': comment[:50]})
            
            return jsonify({'success': True, 'message': 'Comment added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with comprehensive statistics"""
    if complaints_db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    # Get comprehensive statistics (across all category collections)
    total_complaints = count_all_category_collections({})
    pending = count_all_category_collections({'status': 'Pending'})
    acknowledged = count_all_category_collections({'status': 'Acknowledged'})
    in_progress = count_all_category_collections({'status': 'In Progress'})
    resolved = count_all_category_collections({'status': 'Resolved'})
    closed = count_all_category_collections({'status': 'Closed'})
    urgent = count_all_category_collections({'is_urgent': True, 'status': {'$nin': ['Resolved', 'Closed']}})
    
    # SLA breaches
    sla_breached = count_all_category_collections({
        'status': {'$nin': ['Resolved', 'Closed']},
        'sla_deadline': {'$lt': datetime.utcnow()}
    })
    
    # Category-wise counts
    category_stats = {}
    for category in app.config['COMPLAINT_CATEGORIES']:
        category_collection = get_category_collection(category)
        if category_collection is not None:
            category_stats[category] = category_collection.count_documents({})
    
    # Priority distribution
    priority_stats = {}
    for priority in app.config['PRIORITY_LEVELS'].keys():
        priority_stats[priority] = count_all_category_collections({'priority': priority})
    
    # Recent complaints
    recent_complaints = query_all_category_collections({}, sort=('created_at', -1), limit=10)
    for complaint in recent_complaints:
        complaint['_id'] = str(complaint['_id'])
        complaint['user_id'] = str(complaint['user_id'])
        complaint['age'] = get_complaint_age(complaint.get('created_at'))
        complaint['sla_breached'] = is_sla_breached(complaint.get('sla_deadline'))
        
        # Fix photo path
        if complaint.get('image_path') and not complaint.get('photo'):
            complaint['photo'] = complaint['image_path']
        elif complaint.get('photo') and not complaint.get('image_path'):
            complaint['image_path'] = complaint['photo']
        if complaint.get('photo'):
            if complaint['photo'].startswith('static/'):
                complaint['photo'] = complaint['photo'][7:]
            elif complaint['photo'].startswith('/static/'):
                complaint['photo'] = complaint['photo'][8:]
    
    # Urgent complaints
    urgent_complaints = query_all_category_collections({
        'is_urgent': True,
        'status': {'$nin': ['Resolved', 'Closed']}
    }, sort=('created_at', -1), limit=5)
    for complaint in urgent_complaints:
        complaint['_id'] = str(complaint['_id'])
        complaint['user_id'] = str(complaint['user_id'])
    
    stats = {
        'total': total_complaints,
        'pending': pending,
        'acknowledged': acknowledged,
        'in_progress': in_progress,
        'resolved': resolved,
        'closed': closed,
        'urgent': urgent,
        'sla_breached': sla_breached,
        'category_stats': category_stats,
        'priority_stats': priority_stats
    }
    
    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         recent_complaints=recent_complaints,
                         urgent_complaints=urgent_complaints)

@app.route('/admin/complaints')
@admin_required
def admin_view_complaints():
    """Admin view all complaints with advanced filters"""
    if complaints_db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    
    # Build query
    query = {}
    if status:
        query['status'] = status
    if priority:
        query['priority'] = priority
    if search:
        query['$or'] = [
            {'complaint_id': {'$regex': search, '$options': 'i'}},
            {'location': {'$regex': search, '$options': 'i'}},
            {'description': {'$regex': search, '$options': 'i'}}
        ]
    
    # Get complaints with pagination (from specific category or all)
    if category:
        # Query specific category collection
        category_collection = get_category_collection(category)
        if category_collection is not None:
            query['category'] = category  # Keep category in query for consistency
            total = category_collection.count_documents(query)
            complaints = list(category_collection.find(query)
                             .sort('created_at', -1)
                             .skip((page - 1) * app.config['ADMIN_ITEMS_PER_PAGE'])
                             .limit(app.config['ADMIN_ITEMS_PER_PAGE']))
        else:
            total = 0
            complaints = []
    else:
        # Query all category collections
        total = count_all_category_collections(query)
        skip = (page - 1) * app.config['ADMIN_ITEMS_PER_PAGE']
        complaints = query_all_category_collections(query, sort=('created_at', -1), skip=skip, limit=app.config['ADMIN_ITEMS_PER_PAGE'])
    
    # Convert ObjectIds and add metadata
    for complaint in complaints:
        complaint['_id'] = str(complaint['_id'])
        complaint['user_id'] = str(complaint['user_id'])
        complaint['age'] = get_complaint_age(complaint.get('created_at'))
        complaint['sla_breached'] = is_sla_breached(complaint.get('sla_deadline'))
        
        # Fix photo path - normalize image_path and photo fields
        if complaint.get('image_path') and not complaint.get('photo'):
            complaint['photo'] = complaint['image_path']
        elif complaint.get('photo') and not complaint.get('image_path'):
            complaint['image_path'] = complaint['photo']
        # Ensure photo path is relative to static folder
        if complaint.get('photo'):
            # Remove 'static/' prefix if present, url_for will add it
            if complaint['photo'].startswith('static/'):
                complaint['photo'] = complaint['photo'][7:]
            elif complaint['photo'].startswith('/static/'):
                complaint['photo'] = complaint['photo'][8:]
        
        user = users_db.users.find_one({'_id': ObjectId(complaint['user_id'])})
        complaint['user_name'] = user.get('name', 'Unknown') if user else 'Unknown'
        complaint['user_email'] = user.get('email', 'Unknown') if user else 'Unknown'
        
        if complaint.get('assigned_to'):
            assigned_to_id = complaint['assigned_to']
            if isinstance(assigned_to_id, str):
                assigned_to_id = ObjectId(assigned_to_id)
            staff = users_db.users.find_one({'_id': assigned_to_id})
            complaint['assigned_to_name'] = staff.get('name', 'Unknown') if staff else 'Unknown'
            complaint['assigned_to'] = str(assigned_to_id)
        else:
            complaint['assigned_to'] = None
            complaint['assigned_to_name'] = None
    
    total_pages = (total + app.config['ADMIN_ITEMS_PER_PAGE'] - 1) // app.config['ADMIN_ITEMS_PER_PAGE']
    
    return render_template('admin_view_complaints.html', 
                         complaints=complaints,
                         categories=app.config['COMPLAINT_CATEGORIES'],
                         statuses=app.config['STATUS_OPTIONS'],
                         priorities=list(app.config['PRIORITY_LEVELS'].keys()),
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         category_filter=category,
                         status_filter=status,
                         priority_filter=priority,
                         search_filter=search)

@app.route('/admin/staff/list', methods=['GET'])
@admin_required
def admin_staff_list():
    """Get list of staff members for assignment"""
    if users_db is None:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    try:
        staff_members = list(users_db.users.find({'role': 'staff', 'is_active': True}))
        staff_list = []
        for staff in staff_members:
            staff_list.append({
                '_id': str(staff['_id']),
                'name': staff.get('name', 'Unknown'),
                'email': staff.get('email', ''),
                'staff_id': staff.get('staff_id', ''),
                'assigned_complaints': count_all_category_collections({'assigned_to': staff['_id']})
            })
        
        return jsonify({'success': True, 'staff': staff_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/complaint/<complaint_id>/assign', methods=['POST'])
@admin_required
def admin_assign_complaint(complaint_id):
    """Assign complaint to staff member"""
    if complaints_db is None or users_db is None:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    try:
        data = request.get_json()
        staff_id = data.get('staff_id')
        
        if not staff_id:
            return jsonify({'success': False, 'message': 'Staff ID is required'}), 400
        
        # Verify staff exists
        staff = users_db.users.find_one({'_id': ObjectId(staff_id), 'role': 'staff'})
        if not staff:
            return jsonify({'success': False, 'message': 'Staff member not found'}), 404
        
        # Get complaint
        complaint, category_collection = get_complaint_from_all_collections(complaint_id)
        if not complaint or category_collection is None:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        # Update complaint with assignment
        category_collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {
                '$set': {
                    'assigned_to': ObjectId(staff_id),
                    'assigned_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Add comment about assignment
        comments = complaint.get('comments', [])
        admin_user = users_db.users.find_one({'_id': ObjectId(session['user_id'])})
        admin_name = admin_user.get('name', 'Admin') if admin_user else 'Admin'
        comments.append({
            'comment': f'Complaint assigned to {staff.get("name", "Staff")}',
            'user_name': admin_name,
            'user_role': 'admin',
            'timestamp': datetime.utcnow()
        })
        category_collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$set': {'comments': comments}}
        )
        
        # Log activity
        log_activity(complaint_id, 'complaint_assigned', ObjectId(session['user_id']), {'staff_id': staff_id, 'staff_name': staff.get('name')})
        
        return jsonify({'success': True, 'message': 'Complaint assigned successfully'})
        
    except Exception as e:
        print(f"Error assigning complaint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/complaint/<complaint_id>')
@admin_required
def admin_complaint_details(complaint_id):
    """Admin view complaint details"""
    print(f"\n{'='*70}")
    print(f"DEBUG: admin_complaint_details called with ID: {complaint_id}")
    print(f"{'='*70}")
    
    if db is None:
        print("ERROR: db is None")
        flash('Database connection error', 'danger')
        return render_template('admin_complaint_details.html', 
                             complaint=None,
                             staff_members=[],
                             categories=app.config.get('COMPLAINT_CATEGORIES', []),
                             statuses=app.config.get('STATUS_OPTIONS', []),
                             priorities=list(app.config.get('PRIORITY_LEVELS', {}).keys()))
    
    try:
        # Convert complaint_id to ObjectId if it's a valid ObjectId string
        try:
            complaint_id_obj = ObjectId(complaint_id)
            print(f"DEBUG: Valid ObjectId: {complaint_id_obj}")
        except Exception as e:
            # If not valid ObjectId, try to find by complaint_id field
            print(f"DEBUG: Not a valid ObjectId format, will search by complaint_id field: {e}")
            complaint_id_obj = complaint_id
        
        print(f"DEBUG: Calling get_complaint_from_all_collections with: {complaint_id}")
        complaint, category_collection = get_complaint_from_all_collections(complaint_id)
        
        if not complaint:
            print(f"ERROR: Complaint not found for ID: {complaint_id}")
            print(f"DEBUG: Returning template with complaint=None")
            flash('Complaint not found', 'danger')
            return render_template('admin_complaint_details.html', 
                                 complaint=None,
                                 staff_members=[],
                                 categories=app.config.get('COMPLAINT_CATEGORIES', []),
                                 statuses=app.config.get('STATUS_OPTIONS', []),
                                 priorities=list(app.config.get('PRIORITY_LEVELS', {}).keys()))
        
        print(f"DEBUG: Found complaint!")
        print(f"DEBUG: Complaint type: {type(complaint)}")
        print(f"DEBUG: Complaint keys: {list(complaint.keys()) if hasattr(complaint, 'keys') else 'N/A'}")
        print(f"DEBUG: Category: {complaint.get('category', 'N/A')}, Status: {complaint.get('status', 'N/A')}")
        
        # Convert complaint to dict if it's not already
        if not isinstance(complaint, dict):
            print(f"WARNING: Complaint is not a dict, converting...")
            try:
                complaint = dict(complaint)
            except Exception as e:
                print(f"ERROR: Could not convert complaint to dict: {e}")
                flash('Invalid complaint data format', 'danger')
                return render_template('admin_complaint_details.html', 
                                     complaint=None,
                                     staff_members=[],
                                     categories=app.config.get('COMPLAINT_CATEGORIES', []),
                                     statuses=app.config.get('STATUS_OPTIONS', []),
                                     priorities=list(app.config.get('PRIORITY_LEVELS', {}).keys()))
        
        # Check if complaint is empty
        if not complaint or len(complaint) == 0:
            print(f"ERROR: Complaint is empty")
            flash('Complaint data is empty', 'danger')
            return render_template('admin_complaint_details.html', 
                                 complaint=None,
                                 staff_members=[],
                                 categories=app.config.get('COMPLAINT_CATEGORIES', []),
                                 statuses=app.config.get('STATUS_OPTIONS', []),
                                 priorities=list(app.config.get('PRIORITY_LEVELS', {}).keys()))
        
        # Store original _id as ObjectId before converting to string (needed for activity log lookup)
        complaint_oid = None
        if '_id' in complaint and complaint['_id']:
            try:
                complaint_oid = ObjectId(complaint['_id']) if not isinstance(complaint['_id'], ObjectId) else complaint['_id']
                complaint['_id'] = str(complaint['_id'])
            except Exception as e:
                print(f"WARNING: Could not convert _id to ObjectId: {e}")
                complaint['_id'] = str(complaint.get('_id', complaint_id))
        else:
            print(f"ERROR: Complaint _id is missing or invalid: {complaint.get('_id')}")
            complaint['_id'] = str(complaint_id)  # Use the ID from URL as fallback
            try:
                complaint_oid = ObjectId(complaint_id)
            except:
                complaint_oid = None
        complaint['user_id'] = str(complaint.get('user_id', ''))
        complaint['category'] = complaint.get('category', 'Unknown')
        complaint['location'] = complaint.get('location', 'N/A')
        complaint['description'] = complaint.get('description', 'No description provided')
        complaint['status'] = complaint.get('status', 'Pending')
        complaint['priority'] = complaint.get('priority', 'Normal')
        complaint['complaint_id'] = complaint.get('complaint_id', complaint['_id'][:8])
        complaint['department'] = complaint.get('department', 'General Department')
        complaint['department_code'] = complaint.get('department_code', complaint.get('department_code', 'GEN'))
        complaint['is_urgent'] = complaint.get('is_urgent', False)
        complaint['created_at'] = complaint.get('created_at')
        complaint['updated_at'] = complaint.get('updated_at')
        complaint['sla_deadline'] = complaint.get('sla_deadline')
        
        # Fix photo path - normalize image_path and photo fields
        if complaint.get('image_path') and not complaint.get('photo'):
            complaint['photo'] = complaint['image_path']
        elif complaint.get('photo') and not complaint.get('image_path'):
            complaint['image_path'] = complaint['photo']
        # Ensure photo path is relative to static folder
        if complaint.get('photo'):
            # Remove 'static/' prefix if present, url_for will add it
            if complaint['photo'].startswith('static/'):
                complaint['photo'] = complaint['photo'][7:]
            elif complaint['photo'].startswith('/static/'):
                complaint['photo'] = complaint['photo'][8:]
        
        # Get user info
        user = None
        if complaint.get('user_id'):
            try:
                user = users_db.users.find_one({'_id': ObjectId(complaint['user_id'])})
            except:
                pass
        
        if user:
            complaint['user_name'] = user.get('name', 'Unknown')
            complaint['user_email'] = user.get('email', 'Unknown')
            complaint['user_phone'] = user.get('phone', 'N/A')
        else:
            complaint['user_name'] = 'Unknown'
            complaint['user_email'] = 'N/A'
            complaint['user_phone'] = 'N/A'
        
        # Get assigned staff if any
        if complaint.get('assigned_to'):
            try:
                assigned_to_id = complaint['assigned_to']
                if isinstance(assigned_to_id, str):
                    assigned_to_id = ObjectId(assigned_to_id)
                staff = users_db.users.find_one({'_id': assigned_to_id})
                if staff:
                    complaint['assigned_staff_name'] = staff.get('name', 'Unknown')
                    complaint['assigned_staff_email'] = staff.get('email', 'Unknown')
                    complaint['assigned_to'] = str(staff['_id'])  # Ensure it's a string
            except Exception as e:
                print(f"Error getting assigned staff: {e}")
                complaint['assigned_staff_name'] = None
                complaint['assigned_staff_email'] = None
        else:
            complaint['assigned_to'] = None
        
        # Get all staff members for assignment
        staff_members = []
        try:
            staff_list = list(users_db.users.find({'role': {'$in': ['staff', 'admin']}}, {'name': 1, 'email': 1, 'role': 1}))
            for staff in staff_list:
                staff['_id'] = str(staff['_id'])
                staff_members.append(staff)
        except Exception as e:
            print(f"Error getting staff members: {e}")
        
        # Get activity log
        activities = []
        try:
            if complaint_oid:
                activity_list = list(complaints_db.activity_logs.find({'complaint_id': complaint_oid})
                                 .sort('timestamp', 1))
            else:
                activity_list = []
            for activity in activity_list:
                activity['_id'] = str(activity['_id'])
                if activity.get('user_id'):
                    activity['user_id'] = str(activity['user_id'])
                    user = users_db.users.find_one({'_id': ObjectId(activity['user_id'])})
                    activity['user_name'] = user.get('name', 'Unknown') if user else 'Unknown'
                else:
                    activity['user_name'] = 'Unknown'
                activities.append(activity)
        except Exception as e:
            print(f"Error getting activities: {e}")
        
        complaint['activities'] = activities
        complaint['age'] = get_complaint_age(complaint.get('created_at'))
        complaint['sla_breached'] = is_sla_breached(complaint.get('sla_deadline'))
        
        # Ensure comments and progress are lists
        if 'comments' not in complaint:
            complaint['comments'] = []
        if 'progress' not in complaint:
            complaint['progress'] = []
        if 'proof_images' not in complaint:
            complaint['proof_images'] = []
        



        print(f"DEBUG: Complaint data prepared - User: {complaint.get('user_name')}, Category: {complaint.get('category')}")
        print(f"DEBUG: Rendering template with complaint data")
        
        # Get staff members for the dropdown even if error occurred earlier
        try:
            staff_list = list(users_db.users.find({'role': {'$in': ['staff', 'admin']}}, {'name': 1, 'email': 1, 'role': 1}))
            staff_members = []
            for staff in staff_list:
                staff['_id'] = str(staff['_id'])
                staff_members.append(staff)
        except:
            staff_members = []
        
        # Ensure complaint is a dict before passing to template
        if not isinstance(complaint, dict):
            print(f"WARNING: Complaint is not a dict before template render, converting...")
            try:
                complaint = dict(complaint)
            except:
                print(f"ERROR: Could not convert complaint to dict")
                complaint = {}
        
        print(f"DEBUG: Final complaint object type: {type(complaint)}, keys: {list(complaint.keys())[:10] if complaint else 'empty'}")
        
        return render_template('admin_complaint_details.html', 
                             complaint=complaint,
                             staff_members=staff_members,
                             categories=app.config.get('COMPLAINT_CATEGORIES', []),
                             statuses=app.config.get('STATUS_OPTIONS', []),
                             priorities=list(app.config.get('PRIORITY_LEVELS', {}).keys()))
    except Exception as e:
        import traceback
        print(f"\n{'='*70}")
        print(f"ERROR in admin_complaint_details: {e}")
        print(f"{'='*70}")
        traceback.print_exc()
        print(f"{'='*70}\n")
        flash(f'Error loading complaint details: {str(e)}', 'danger')
        # Render template with error instead of redirecting
        return render_template('admin_complaint_details.html', 
                             complaint=None,
                             staff_members=[],
                             categories=app.config.get('COMPLAINT_CATEGORIES', []),
                             statuses=app.config.get('STATUS_OPTIONS', []),
                             priorities=list(app.config.get('PRIORITY_LEVELS', {}).keys()))

@app.route('/admin/complaint/<complaint_id>/update', methods=['POST'])
@admin_required
def admin_update_complaint(complaint_id):
    """Admin update complaint status"""
    print(f"\n{'='*70}")
    print(f"DEBUG: Admin updating complaint: {complaint_id}")
    print(f"{'='*70}")
    
    if db is None:
        print("ERROR: Database connection is None")
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    try:
        request_data = request.get_json()
        print(f"DEBUG: Request data: {request_data}")
        
        status = request_data.get('status') if request_data else None
        priority = request_data.get('priority') if request_data else None
        assigned_to = request_data.get('assigned_to') if request_data else None
        comment = request_data.get('comment', '').strip() if request_data else ''
        
        print(f"DEBUG: Status: {status}")
        print(f"DEBUG: Priority: {priority}")
        print(f"DEBUG: Assigned to: {assigned_to}")
        print(f"DEBUG: Comment: {comment[:50]}...")
        
        if status and status not in app.config['STATUS_OPTIONS']:
            print(f"ERROR: Invalid status: {status}")
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        # Get complaint before update (from category collection)
        complaint, category_collection = get_complaint_from_all_collections(complaint_id)
        if not complaint or category_collection is None:
            print(f"ERROR: Complaint not found: {complaint_id}")
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        print(f"DEBUG: Found complaint in collection: {category_collection.name}")
        print(f"DEBUG: Current status: {complaint.get('status')}")
        print(f"DEBUG: Current category: {complaint.get('category')}")
        
        old_status = complaint.get('status')
        old_assigned_to = complaint.get('assigned_to')
        
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        if status:
            update_data['status'] = status
            print(f"DEBUG: Updating status from '{old_status}' to '{status}'")
            # Update status to "Acknowledged" if assigning to worker
            if assigned_to and not old_assigned_to and status == 'Pending':
                update_data['status'] = 'Acknowledged'
        if priority:
            update_data['priority'] = priority
            # Recalculate SLA deadline
            update_data['sla_deadline'] = calculate_sla_deadline(priority, complaint.get('created_at', datetime.utcnow()))
            print(f"DEBUG: Updating priority to: {priority}")
        if assigned_to is not None:
            if assigned_to and assigned_to != 'None':
                update_data['assigned_to'] = ObjectId(assigned_to)
                if not status or status == 'Pending':
                    update_data['status'] = 'Acknowledged'
                print(f"DEBUG: Assigning to: {assigned_to}")
            else:
                update_data['assigned_to'] = None
                print(f"DEBUG: Removing assignment")
        
        print(f"DEBUG: Update data: {update_data}")
        
        # Update in the correct category collection
        result = category_collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$set': update_data}
        )
        
        print(f"DEBUG: Update result - Modified count: {result.modified_count}")
        print(f"DEBUG: Update result - Matched count: {result.matched_count}")
        
        if result.matched_count == 0:
            print(f"ERROR: No document matched for update")
            return jsonify({'success': False, 'message': 'Complaint not found for update'}), 404
        
        # Add comment if provided
        if comment:
            comments = complaint.get('comments', [])
            comments.append({
                'comment': comment,
                'admin_name': session.get('user_name', 'Admin'),
                'user_role': 'admin',
                'timestamp': datetime.utcnow()
            })
            category_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {'$set': {'comments': comments}}
            )
            print(f"DEBUG: Comment added")
        
        print(f"DEBUG: ✓ Complaint updated successfully")
        print(f"{'='*70}\n")
        
        # Send email notifications
        try:
            from utils.email_service import send_complaint_assigned_email, send_status_update_email
            
            # If assigned to worker, notify worker
            if assigned_to and assigned_to != 'None' and str(old_assigned_to) != str(assigned_to):
                worker = users_db.users.find_one({'_id': ObjectId(assigned_to)})
                if worker:
                    send_complaint_assigned_email(
                        worker.get('email', ''),
                        worker.get('name', 'Worker'),
                        complaint.get('complaint_id', complaint_id),
                        complaint.get('category', ''),
                        complaint.get('location', '')
                    )
            
            # If status changed to Resolved, notify user
            if status == 'Resolved' and old_status != 'Resolved':
                user = users_db.users.find_one({'_id': ObjectId(complaint['user_id'])})
                if user:
                    from utils.email_service import send_complaint_resolved_email
                    send_complaint_resolved_email(
                        user.get('email', ''),
                        user.get('name', 'User'),
                        complaint.get('complaint_id', complaint_id),
                        complaint.get('category', '')
                    )
            # Otherwise notify user of status update
            elif status and status != old_status:
                user = users_db.users.find_one({'_id': ObjectId(complaint['user_id'])})
                if user:
                    send_status_update_email(
                        user.get('email', ''),
                        user.get('name', 'User'),
                        complaint.get('complaint_id', complaint_id),
                        status
                    )
        except Exception as e:
            print(f"Email notification error: {e}")
        
        # Log activity
        log_activity(complaint_id, 'status_updated', session['user_id'], 
                    {'status': status, 'priority': priority, 'assigned_to': str(assigned_to) if assigned_to else None})
        
        return jsonify({'success': True, 'message': 'Complaint updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/complaint/<complaint_id>/urgent', methods=['POST'])
@admin_required
def admin_toggle_urgent(complaint_id):
    """Toggle urgent status of complaint"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    try:
        is_urgent = request.json.get('is_urgent', False)
        
        update_data = {
            'is_urgent': is_urgent,
            'priority': 'Urgent' if is_urgent else 'Normal',
            'updated_at': datetime.utcnow()
        }
        
        # Recalculate SLA if urgent
        if is_urgent:
            complaint, _ = get_complaint_from_all_collections(complaint_id)
            if complaint:
                update_data['sla_deadline'] = calculate_sla_deadline('Urgent', complaint.get('created_at', datetime.utcnow()))
        
        # Get the category collection for this complaint
        complaint, category_collection = get_complaint_from_all_collections(complaint_id)
        if not complaint or category_collection is None:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        category_collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$set': update_data}
        )
        
        log_activity(complaint_id, 'urgent_toggled', session['user_id'], {'is_urgent': is_urgent})
        
        return jsonify({'success': True, 'message': 'Urgent status updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics page with comprehensive charts"""
    if complaints_db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    # Category distribution (each category has its own collection)
    category_data = {}
    for category in app.config['COMPLAINT_CATEGORIES']:
        category_collection = get_category_collection(category)
        if category_collection is not None:
            category_data[category] = category_collection.count_documents({})
    
    # Status distribution (across all category collections)
    status_data = {}
    for status in app.config['STATUS_OPTIONS']:
        status_data[status] = count_all_category_collections({'status': status})
    
    # Priority distribution (across all category collections)
    priority_data = {}
    for priority in app.config['PRIORITY_LEVELS'].keys():
        priority_data[priority] = count_all_category_collections({'priority': priority})
    
    # Monthly trend (last 12 months, across all category collections)
    monthly_data = {}
    for i in range(12):
        month_start = datetime.utcnow() - timedelta(days=30*(i+1))
        month_end = datetime.utcnow() - timedelta(days=30*i)
        count = count_all_category_collections({
            'created_at': {
                '$gte': month_start,
                '$lt': month_end
            }
        })
        month_name = month_start.strftime('%b %Y')
        monthly_data[month_name] = count
    
    # Resolution time (average days to resolve, across all category collections)
    resolved_complaints = query_all_category_collections({'status': 'Resolved'})
    resolution_times = []
    for complaint in resolved_complaints:
        if complaint.get('created_at') and complaint.get('updated_at'):
            diff = complaint['updated_at'] - complaint['created_at']
            resolution_times.append(diff.days)
    
    avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    analytics_data = {
        'category': category_data,
        'status': status_data,
        'priority': priority_data,
        'monthly': monthly_data,
        'avg_resolution_time': round(avg_resolution_time, 1)
    }
    
    return render_template('admin_analytics.html', analytics=analytics_data)

@app.route('/admin/staff')
@admin_required
def admin_staff():
    """Manage staff members"""
    if complaints_db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    staff_members = list(users_db.users.find({'role': {'$in': ['admin', 'staff']}}))
    for staff in staff_members:
        staff['_id'] = str(staff['_id'])
        # Get assigned complaints count (across all category collections)
        staff['assigned_complaints'] = count_all_category_collections({'assigned_to': ObjectId(staff['_id'])})
    
    return render_template('admin_staff.html', staff_members=staff_members)

@app.route('/admin/staff/add', methods=['POST'])
@admin_required
def admin_add_staff():
    """Add new staff member"""
    if users_db is None:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    try:
        staff_id = request.form.get('staff_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validation
        if not staff_id or not name or not email or not password:
            return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400
        
        # Check if staff_id already exists
        existing_staff_id = users_db.users.find_one({'staff_id': staff_id})
        if existing_staff_id:
            return jsonify({'success': False, 'message': 'Staff ID already exists'}), 400
        
        # Check if email already exists
        existing_email = users_db.users.find_one({'email': email})
        if existing_email:
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create staff member
        staff_data = {
            'staff_id': staff_id,
            'name': name,
            'email': email,
            'phone': phone if phone else '',
            'password': hashed_password,
            'role': 'staff',
            'created_at': datetime.utcnow(),
            'is_active': True,
            'profile': {}
        }
        
        result = users_db.users.insert_one(staff_data)
        
        if result.inserted_id:
            # Log activity
            log_activity(str(result.inserted_id), 'staff_created', ObjectId(session['user_id']), {'staff_id': staff_id, 'name': name})
            return jsonify({'success': True, 'message': 'Staff member created successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to create staff member'}), 500
            
    except Exception as e:
        print(f"Error creating staff member: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/users')
@admin_required
def admin_users():
    """View all users"""
    if complaints_db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    
    query = {}
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'email': {'$regex': search, '$options': 'i'}}
        ]
    if role_filter:
        query['role'] = role_filter
    
    total = users_db.users.count_documents(query)
    users = list(users_db.users.find(query)
                .sort('created_at', -1)
                .skip((page - 1) * app.config['ADMIN_ITEMS_PER_PAGE'])
                .limit(app.config['ADMIN_ITEMS_PER_PAGE']))
    
    for user in users:
        user['_id'] = str(user['_id'])
        user['complaints_count'] = count_all_category_collections({'user_id': ObjectId(user['_id'])})
    
    total_pages = (total + app.config['ADMIN_ITEMS_PER_PAGE'] - 1) // app.config['ADMIN_ITEMS_PER_PAGE']
    
    return render_template('admin_users.html', 
                         users=users,
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         search_filter=search,
                         role_filter=role_filter)

# ==================== STAFF ROUTES ====================

@app.route('/staff/dashboard')
@staff_required
def staff_dashboard():
    """Staff dashboard - view assigned complaints"""
    if complaints_db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    staff_id = ObjectId(session['user_id'])
    
    # Get statistics (across all category collections)
    assigned_count = count_all_category_collections({'assigned_to': staff_id})
    pending = count_all_category_collections({'assigned_to': staff_id, 'status': 'Pending'})
    in_progress = count_all_category_collections({'assigned_to': staff_id, 'status': 'In Progress'})
    resolved = count_all_category_collections({'assigned_to': staff_id, 'status': 'Resolved'})
    
    # Get recent assigned complaints (across all category collections)
    recent_complaints = query_all_category_collections({'assigned_to': staff_id}, sort=('created_at', -1), limit=10)
    
    for complaint in recent_complaints:
        complaint['_id'] = str(complaint['_id'])
        complaint['user_id'] = str(complaint['user_id'])
        complaint['age'] = get_complaint_age(complaint.get('created_at'))
        complaint['sla_breached'] = is_sla_breached(complaint.get('sla_deadline'))
        
        # Get user info
        user = users_db.users.find_one({'_id': ObjectId(complaint['user_id'])})
        complaint['user_name'] = user.get('name', 'Unknown') if user else 'Unknown'
    
    stats = {
        'assigned': assigned_count,
        'pending': pending,
        'in_progress': in_progress,
        'resolved': resolved
    }
    
    return render_template('staff_dashboard.html', stats=stats, recent_complaints=recent_complaints)

@app.route('/worker/update_status', methods=['POST'])
@staff_required
def worker_update_status():
    """Worker update complaint status with proof"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    try:
        complaint_id = request.form.get('complaint_id')
        status = request.form.get('status')
        comment = request.form.get('comment', '').strip()
        worker_id = ObjectId(session['user_id'])
        
        if not complaint_id or not status:
            return jsonify({'success': False, 'message': 'Complaint ID and status are required'}), 400
        
        # Get complaint (from category collection)
        complaint, category_collection = get_complaint_from_all_collections(complaint_id)
        if not complaint or category_collection is None:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        # Verify complaint is assigned to this worker
        if str(complaint.get('assigned_to')) != str(worker_id):
            return jsonify({'success': False, 'message': 'This complaint is not assigned to you'}), 403
        
        # Handle proof image upload
        proof_path = None
        if 'proof_image' in request.files:
            file = request.files['proof_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"proof_{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                proof_path = f"uploads/{filename}"
        
        old_status = complaint.get('status')
        
        # Update complaint
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        
        if proof_path:
            if 'proof_images' not in complaint:
                update_data['proof_images'] = []
            proof_images = complaint.get('proof_images', [])
            proof_images.append({
                'path': proof_path,
                'uploaded_by': str(worker_id),
                'uploaded_at': datetime.utcnow()
            })
            update_data['proof_images'] = proof_images
        
        category_collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$set': update_data}
        )
        
        # Add comment/note
        if comment:
            comments = complaint.get('comments', [])
            comments.append({
                'comment': comment,
                'user_name': session.get('user_name', 'Staff'),
                'user_role': 'staff',
                'timestamp': datetime.utcnow()
            })
            category_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {'$set': {'comments': comments}}
            )
        
        # Add to progress log
        progress = complaint.get('progress', [])
        progress.append({
            'status': status,
            'updated_by': str(worker_id),
            'updated_at': datetime.utcnow(),
            'comment': comment if comment else None,
            'proof_image': proof_path if proof_path else None
        })
        category_collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$set': {'progress': progress}}
        )
        
        # Send email notification if resolved
        if status == 'Resolved' and old_status != 'Resolved':
            try:
                from utils.email_service import send_complaint_resolved_email
                user = users_db.users.find_one({'_id': ObjectId(complaint['user_id'])})
                if user:
                    send_complaint_resolved_email(
                        user.get('email', ''),
                        user.get('name', 'User'),
                        complaint.get('complaint_id', complaint_id),
                        complaint.get('category', '')
                    )
            except Exception as e:
                print(f"Email notification error: {e}")
        
        # Log activity
        log_activity(complaint_id, 'worker_status_update', worker_id, {'status': status, 'has_proof': bool(proof_path)})
        
        return jsonify({'success': True, 'message': 'Status updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/staff/complaints')
@staff_required
def staff_complaints():
    """Staff view assigned complaints with filters"""
    if complaints_db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    staff_id = ObjectId(session['user_id'])
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    page = int(request.args.get('page', 1))
    
    # Build query
    query = {'assigned_to': staff_id}
    if status_filter:
        query['status'] = status_filter
    if priority_filter:
        query['priority'] = priority_filter
    
    # Get complaints (across all category collections)
    total = count_all_category_collections(query)
    skip = (page - 1) * app.config['ITEMS_PER_PAGE']
    complaints = query_all_category_collections(query, sort=('created_at', -1), skip=skip, limit=app.config['ITEMS_PER_PAGE'])
    
    # Convert ObjectIds and enrich data
    for complaint in complaints:
        complaint['_id'] = str(complaint['_id'])
        complaint['user_id'] = str(complaint['user_id'])
        complaint['age'] = get_complaint_age(complaint.get('created_at'))
        complaint['sla_breached'] = is_sla_breached(complaint.get('sla_deadline'))
        
        # Handle photo/image_path field
        if 'image_path' in complaint and not complaint.get('photo'):
            complaint['photo'] = complaint.get('image_path')
        elif 'photo' in complaint and not complaint.get('image_path'):
            complaint['image_path'] = complaint.get('photo')
        
        # Get user info
        user = users_db.users.find_one({'_id': ObjectId(complaint['user_id'])})
        complaint['user_name'] = user.get('name', 'Unknown') if user else 'Unknown'
        complaint['user_email'] = user.get('email', 'Unknown') if user else 'Unknown'
        
        # Ensure proof_images is a list
        if 'proof_images' not in complaint:
            complaint['proof_images'] = []
        elif not isinstance(complaint.get('proof_images'), list):
            complaint['proof_images'] = []
        
        # Convert assigned_to ObjectId to string if present
        if 'assigned_to' in complaint and complaint['assigned_to']:
            complaint['assigned_to'] = str(complaint['assigned_to'])
    
    total_pages = (total + app.config['ITEMS_PER_PAGE'] - 1) // app.config['ITEMS_PER_PAGE']
    
    return render_template('staff_complaints.html',
                         complaints=complaints,
                         statuses=app.config['STATUS_OPTIONS'],
                         priorities=list(app.config['PRIORITY_LEVELS'].keys()),
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         status_filter=status_filter,
                         priority_filter=priority_filter)

# ==================== FEEDBACK ROUTES ====================

@app.route('/complaint/<complaint_id>/feedback', methods=['GET', 'POST'])
@login_required
def complaint_feedback(complaint_id):
    """Submit feedback and rating for resolved complaint"""
    if db is None:
        flash('Database connection error', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        complaint, category_collection = get_complaint_from_all_collections(complaint_id)
        
        if not complaint:
            flash('Complaint not found', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if user owns this complaint
        if str(complaint['user_id']) != session['user_id']:
            flash('You do not have access to this complaint', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if complaint is resolved
        if complaint.get('status') not in ['Resolved', 'Closed']:
            flash('Feedback can only be submitted for resolved complaints', 'warning')
            return redirect(url_for('track_complaint', complaint_id=complaint_id))
        
        # Check if feedback already submitted
        if complaint.get('feedback'):
            flash('You have already submitted feedback for this complaint', 'info')
            return redirect(url_for('track_complaint', complaint_id=complaint_id))
        
        if request.method == 'POST':
            rating = int(request.form.get('rating', 0))
            feedback_text = request.form.get('feedback', '').strip()
            
            if rating < 1 or rating > 5:
                flash('Please select a rating between 1 and 5', 'danger')
                return render_template('complaint_feedback.html', complaint_id=complaint_id)
            
            # Update complaint with feedback
            if category_collection is None:
                flash('Database error', 'danger')
                return redirect(url_for('dashboard'))
            
            feedback_data = {
                'rating': rating,
                'comments': feedback_text,
                'submitted_at': datetime.utcnow(),
                'user_id': ObjectId(session['user_id'])
            }
            
            category_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {'$set': {'feedback': feedback_data}}
            )
            
            # Log activity
            log_activity(complaint_id, 'feedback_submitted', session['user_id'], {'rating': rating})
            
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('track_complaint', complaint_id=complaint_id))
        
        complaint['_id'] = str(complaint['_id'])
        return render_template('complaint_feedback.html', 
                             complaint_id=complaint_id,
                             complaint=complaint)
    except Exception as e:
        print(f"Error in complaint_feedback: {e}")
        flash('Error loading feedback page', 'danger')
        return redirect(url_for('dashboard'))

# API Routes
@app.route('/api/complaint/<complaint_id>')
@login_required
def api_get_complaint(complaint_id):
    """API to get complaint details"""
    try:
        complaint, _ = get_complaint_from_all_collections(complaint_id)
        if not complaint:
            return jsonify({'success': False}), 404
        
        complaint['_id'] = str(complaint['_id'])
        complaint['user_id'] = str(complaint['user_id'])
        
        return jsonify({'success': True, 'complaint': complaint})
    except:
        return jsonify({'success': False}), 400

if __name__ == '__main__':
    if users_db is None or complaints_db is None:
        print("\n⚠️  WARNING: Cannot start application without MongoDB connection!")
        print("Please set up MongoDB before running the application.\n")
        exit(1)
    
    # Verify database connections are working
    try:
        users_db.command('ping')
        complaints_db.command('ping')
        print("✓ Database connections verified")
        print(f"  - Users Database: {app.config['USERS_DATABASE_NAME']}")
        print(f"  - Complaints Database: {app.config['COMPLAINTS_DATABASE_NAME']}")
    except Exception as e:
        print(f"✗ Database connection verification failed: {e}")
        exit(1)
    
    # Initialize database structure
    print("\n🔧 Initializing database structure...")
    initialize_database()
    
    # Create default admin user if doesn't exist
    try:
        existing_admin = users_db.users.find_one({'role': 'admin'})
        if not existing_admin:
            admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            admin_result = users_db.users.insert_one({
                'name': 'System Administrator',
                'email': 'admin@municipal.gov',
                'phone': '0000000000',
                'password': admin_password,
                'role': 'admin',
                'created_at': datetime.utcnow(),
                'is_active': True,
                'profile': {}
            })
            if admin_result.inserted_id:
                print("✓ Default admin user created (admin@municipal.gov / admin123)")
            else:
                print("⚠️  Failed to create admin user")
        else:
            print("✓ Admin user already exists")
    except Exception as e:
        print(f"⚠️  Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
    
    # Print current counts
    try:
        user_count = users_db.users.count_documents({})
        complaint_count = count_all_category_collections({})
        print(f"✓ Total users in users database: {user_count}")
        print(f"✓ Total complaints across all category collections: {complaint_count}")
        # Print counts per category
        for category in app.config['COMPLAINT_CATEGORIES']:
            category_collection = get_category_collection(category)
            if category_collection is not None:
                cat_count = category_collection.count_documents({})
                if cat_count > 0:
                    print(f"  - {category}: {cat_count} complaints")
    except Exception as e:
        print(f"⚠️  Could not count records: {e}")
    
    print("\n🚀 Starting Flask application...")
    print("📍 Server running at: http://localhost:5000")
    print("📖 Default admin: admin@municipal.gov / admin123")
    print("💡 Debug mode: ON - Check console for registration errors")
    print("\n💡 Tip: If you see socket errors on Windows, they're harmless")
    print("   and won't affect the application functionality.\n")
    
    # Windows-friendly configuration
    # use_reloader=False prevents socket errors on Windows with the reloader
    # threaded=True allows handling multiple requests simultaneously
    # For Windows, disabling reloader prevents the common WinError 10038
    import os
    if os.name == 'nt':  # Windows
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False, threaded=True)
    else:  # Linux/Mac
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

