# Municipal Complaint Management System - Modules Summary

## ✅ Completed Modules

### 1. Complaint Submission Module
- **Routes:**
  - `GET /complaint/new` - Display complaint submission form
  - `POST /complaint/create` - Submit complaint (handled by `/submit_complaint`)
- **Features:**
  - Category dropdown (12 categories)
  - Location field
  - Description textarea
  - Image upload (optional)
  - Priority selection (Low, Normal, High, Urgent)
  - Auto-assignment to department based on category
  - Auto-generation of complaint ID
  - Email notification on submission

### 2. User Complaint Tracking Page
- **Route:** `GET /dashboard` - User dashboard with all complaints
- **Route:** `GET /complaint/<complaint_id>` - Track individual complaint
- **Features:**
  - List all user complaints with status, category, date
  - View complaint details with progress tracking
  - Status badges (Pending, In Progress, Resolved, etc.)
  - Progress log with timestamps
  - Feedback button for resolved complaints
  - Proof images uploaded by workers

### 3. Admin Complaint Management
- **Routes:**
  - `GET /admin/complaints` - List all complaints with filters
  - `GET /admin/complaint/<id>` - View complaint details
  - `POST /admin/complaint/<id>/update` - Update complaint status/priority
  - `POST /admin/complaint/<id>/assign` - Assign complaint to worker
  - `POST /admin/complaint/<id>/urgent` - Toggle urgent status
- **Features:**
  - Advanced filters (category, status, priority, date, search)
  - Pagination for large datasets
  - Assign complaints to workers/staff
  - Change priority levels
  - Update status
  - Add admin notes/comments
  - View user information
  - View proof images
  - View progress log
  - View feedback and ratings

### 4. Worker/Staff Role
- **Routes:**
  - `GET /staff/dashboard` - Worker dashboard
  - `GET /staff/complaints` - Assigned complaints
  - `POST /worker/update_status` - Update status with proof
- **Features:**
  - View only assigned complaints
  - Update complaint status (Acknowledged, In Progress, Under Review, Resolved)
  - Upload proof images/videos
  - Add comments/notes
  - Progress tracking
  - Auto email notification when resolved

### 5. Complaint Assignment System
- **Route:** `POST /admin/complaint/<id>/assign`
- **Features:**
  - Admin can assign complaints to workers/staff
  - Select from available staff members
  - Set priority level during assignment
  - Add admin notes
  - Auto-update status to "Acknowledged"
  - Email notification to assigned worker

### 6. Email Notification System
- **Utility:** `utils/email_service.py`
- **Functions:**
  - `send_complaint_submitted_email()` - Sent when user submits complaint
  - `send_complaint_assigned_email()` - Sent when complaint assigned to worker
  - `send_complaint_resolved_email()` - Sent when complaint resolved
  - `send_status_update_email()` - Sent when status updated
- **Configuration:**
  - SMTP settings via environment variables
  - HTML and plain text emails
  - Graceful failure (doesn't break flow if email fails)

### 7. Feedback & Rating System
- **Route:** `GET /complaint/<id>/feedback` - Feedback form
- **Route:** `POST /complaint/<id>/feedback` - Submit feedback
- **Features:**
  - 5-star rating system
  - Optional text feedback/comments
  - Only for resolved/closed complaints
  - One feedback per complaint
  - Displayed in complaint details

### 8. Admin Analytics Page
- **Route:** `GET /admin/analytics`
- **Features:**
  - Charts using Chart.js:
    - Complaints per category
    - Complaints per status
    - Monthly complaint trends
    - Top problem areas (by location)
    - Priority distribution
    - Resolution time statistics
  - Export options (coming soon)

## 📊 MongoDB Collections

### `users`
```json
{
  "_id": ObjectId,
  "name": String,
  "email": String,
  "phone": String,
  "password": String (hashed),
  "role": "citizen" | "staff" | "admin",
  "is_active": Boolean,
  "created_at": DateTime,
  "last_login": DateTime
}
```

### `complaints`
```json
{
  "_id": ObjectId,
  "complaint_id": String (unique),
  "user_id": ObjectId,
  "category": String,
  "location": String,
  "description": String,
  "photo": String (path),
  "image_path": String (path),
  "status": String,
  "priority": String,
  "is_urgent": Boolean,
  "department": String,
  "department_code": String,
  "assigned_to": ObjectId (nullable),
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

### `activity_logs`
```json
{
  "_id": ObjectId,
  "complaint_id": ObjectId,
  "action": String,
  "user_id": ObjectId,
  "details": Object,
  "timestamp": DateTime,
  "ip_address": String
}
```

## 🔐 Authentication & Authorization

- **Roles:**
  - `citizen` - Can submit and track complaints
  - `staff` - Can view assigned complaints and update status
  - `admin` - Full access to all features

- **Decorators:**
  - `@login_required` - Requires user to be logged in
  - `@admin_required` - Requires admin role
  - `@staff_required` - Requires staff or admin role

## 🎨 Templates Created

1. `admin_complaint_details.html` - Detailed complaint view for admin
2. `complaint_feedback.html` - Feedback and rating form
3. Enhanced `track_complaint.html` - With feedback section
4. Enhanced `staff_dashboard.html` - With worker update form
5. Enhanced `staff_complaints.html` - With proof upload

## 🔧 Configuration

Email notifications are optional. To enable:
1. Set environment variables:
   ```
   ENABLE_EMAIL_NOTIFICATIONS=True
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```
2. Or update `config.py` directly

## 📝 Notes

- All file uploads are stored in `static/uploads/`
- Images are validated before upload
- Maximum file size: 16MB
- All timestamps are in UTC
- Activity logging tracks all important actions
- Email notifications work gracefully even if SMTP is not configured

## 🚀 Next Steps (Optional Enhancements)

- [ ] Export complaints to PDF/Excel
- [ ] SMS notifications
- [ ] Push notifications
- [ ] Mobile app
- [ ] Map integration for location
- [ ] Multi-language support
- [ ] Advanced reporting
- [ ] Workflow automation

