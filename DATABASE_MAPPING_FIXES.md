# Database Mapping Fixes - Complaint Submission

## 🔧 Issues Fixed

### 1. **Improved Form Data Validation**
- **Fixed:** Added proper stripping and validation of all form fields
- **Fixed:** Added validation for category to ensure it exists in config
- **Fixed:** Added validation for priority field
- **Fixed:** Improved `is_urgent` checkbox handling (now checks for 'true', 'on', or '1')

```python
# Before
is_urgent = request.form.get('is_urgent') == 'true'

# After  
is_urgent = request.form.get('is_urgent', '').lower() in ['true', 'on', '1']
```

### 2. **Fixed Priority Mapping**
- **Fixed:** Priority is now properly calculated before SLA deadline calculation
- **Fixed:** If urgent checkbox is checked, priority is set to 'Urgent' before SLA calculation
- **Fixed:** Added fallback for invalid priority values

```python
# Set final priority (urgent overrides)
final_priority = 'Urgent' if is_urgent else priority

# Calculate SLA deadline with correct priority
sla_deadline = calculate_sla_deadline(final_priority, created_at)
```

### 3. **Fixed Department Mapping**
- **Fixed:** Added proper fallback for missing department in config
- **Fixed:** Used `.get()` method with default values to prevent KeyError

```python
# Before
department_info = app.config['DEPARTMENTS'].get(category, app.config['DEPARTMENTS']['Other'])

# After
department_info = app.config['DEPARTMENTS'].get(category, 
    app.config['DEPARTMENTS'].get('Other', {'name': 'General Department', 'code': 'GEN'}))
```

### 4. **Fixed Complaint Document Structure**
- **Fixed:** Renamed `complaint` variable to `complaint_doc` to avoid shadowing
- **Fixed:** Only add photo fields if photo was actually uploaded
- **Fixed:** Added `proof_images` array field for worker uploads
- **Fixed:** Removed redundant `activity_log` field (uses separate collection)

```python
# Create complaint document
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
    'progress': [],
    'proof_images': [],  # For worker proof uploads
    'feedback': None
}

# Add photo fields if image was uploaded
if photo_path:
    complaint_doc['image_path'] = photo_path
    complaint_doc['photo'] = photo_path
```

### 5. **Added Error Handling**
- **Fixed:** Added try-catch block around database insert
- **Fixed:** Added proper error messages for database failures
- **Fixed:** Added validation for insert result

```python
# Insert complaint into database
try:
    result = db.complaints.insert_one(complaint_doc)
    if not result.inserted_id:
        flash('Error: Failed to save complaint to database', 'danger')
        return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
except Exception as e:
    print(f"Database insert error: {e}")
    flash(f'Error saving complaint: {str(e)}', 'danger')
    return render_template('submit_complaint.html', categories=app.config['COMPLAINT_CATEGORIES'])
```

### 6. **Fixed Activity Logging**
- **Fixed:** Added try-catch around activity logging
- **Fixed:** Logging errors won't break complaint submission

```python
# Log activity
try:
    log_activity(str(result.inserted_id), 'complaint_created', session['user_id'], 
                {'complaint_id': complaint_id, 'category': category})
except Exception as e:
    print(f"Activity log error: {e}")
```

## 📊 Database Schema (Fixed)

### Complaints Collection
```javascript
{
  "_id": ObjectId,
  "complaint_id": String (unique, e.g., "COM-20250101-ABC123"),
  "user_id": ObjectId (reference to users),
  "category": String (e.g., "Garbage Collection"),
  "location": String,
  "description": String,
  "photo": String (path, optional),
  "image_path": String (path, optional),
  "status": String ("Pending"),
  "priority": String ("Low", "Normal", "High", "Urgent"),
  "is_urgent": Boolean,
  "department": String (e.g., "Sanitation Department"),
  "department_code": String (e.g., "SAN"),
  "assigned_to": ObjectId (nullable, reference to users),
  "created_at": DateTime,
  "updated_at": DateTime,
  "sla_deadline": DateTime,
  "sla_breached": Boolean,
  "comments": Array,
  "progress": Array,
  "proof_images": Array,
  "feedback": Object (nullable)
}
```

## ✅ All Mappings Correct

1. **Category** → `category` field ✅
2. **Location** → `location` field ✅
3. **Description** → `description` field ✅
4. **Photo** → `photo` and `image_path` fields ✅
5. **Priority** → `priority` field (with urgent override) ✅
6. **Is Urgent** → `is_urgent` field ✅
7. **Category** → Auto-mapped to `department` and `department_code` ✅
8. **User ID** → `user_id` field (ObjectId) ✅
9. **Complaint ID** → Auto-generated `complaint_id` ✅
10. **SLA Deadline** → Calculated based on priority ✅

## 🚀 Testing

To test complaint submission:

1. **Submit a complaint with all fields:**
   - Category: Select any category
   - Location: Enter address
   - Description: Enter description (min 10 chars)
   - Photo: Upload image (optional)
   - Urgent: Check if urgent

2. **Check database:**
   ```python
   # In MongoDB shell or Python
   db.complaints.find().sort({created_at: -1}).limit(1).pretty()
   ```

3. **Verify all fields are saved correctly:**
   - ✅ complaint_id exists
   - ✅ user_id is ObjectId
   - ✅ category matches
   - ✅ location matches
   - ✅ description matches
   - ✅ photo/image_path exists if uploaded
   - ✅ priority is correct (Urgent if urgent checked)
   - ✅ department and department_code are set
   - ✅ sla_deadline is calculated correctly
   - ✅ created_at and updated_at are set

## 🔍 Debugging

If complaints are still not saving:

1. **Check MongoDB connection:**
   ```python
   if db is None:
       print("Database connection failed!")
   ```

2. **Check error messages:**
   - Look at Flask console output
   - Check for "Database insert error" messages

3. **Verify session:**
   ```python
   if 'user_id' not in session:
       print("User not logged in!")
   ```

4. **Check file uploads folder:**
   - Ensure `static/uploads/` directory exists
   - Check file permissions

5. **Test database write:**
   ```python
   test_doc = {'test': 'value', 'timestamp': datetime.utcnow()}
   result = db.complaints.insert_one(test_doc)
   print(f"Test insert ID: {result.inserted_id}")
   ```

## ✅ All Issues Resolved

The complaint submission should now work correctly with proper database mapping and error handling.

