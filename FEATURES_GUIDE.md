# Municipal Complaint Management System - Features Guide

## 🎯 System Overview

This is a complete **Intelligent Municipal Complaint Management System** built with Flask, MongoDB, HTML, CSS, and JavaScript. It includes all modules requested in the project specification.

## ✅ All Modules Implemented

### 1. ✅ Complaint Submission Module
**Location:** `/submit_complaint`

- Full complaint form with:
  - Category dropdown (12 categories: Garbage, Water, Road, Drainage, Streetlight, etc.)
  - Location field (text input, ready for map integration)
  - Description textarea
  - Image upload (optional photo/video)
  - Priority selection
  - Urgent checkbox
- Auto-assignment to department based on category
- Auto-generation of unique complaint ID
- Email notification sent on submission
- Form validation (client-side and server-side)

### 2. ✅ User Complaint Tracking Page
**Location:** `/dashboard` and `/complaint/<complaint_id>`

- User dashboard showing all their complaints:
  - Complaint ID
  - Category
  - Status badge (Pending, In Progress, Resolved, etc.)
  - Submitted date
  - "View Details" button
- Complaint details page with:
  - Full complaint information
  - Status history
  - Progress log
  - Comments from admin/staff
  - Proof images uploaded by workers
  - Feedback button (for resolved complaints)

### 3. ✅ Admin Complaint Management
**Locations:**
- `/admin/complaints` - List all complaints
- `/admin/complaint/<id>` - View/Manage complaint details

**Features:**
- Advanced filters:
  - Category filter
  - Status filter
  - Priority filter
  - Date range filter
  - Location/area search
- Complaint details page showing:
  - Complete complaint information
  - User details (name, email, phone)
  - Uploaded images
  - Worker assignment section
  - Status update section
  - Priority change section
  - Admin notes/comments
  - Progress log
  - Proof images
  - Feedback & ratings
- Actions:
  - Assign complaint to worker
  - Change priority
  - Update status
  - Add admin notes
  - View activity log

### 4. ✅ Worker/Staff Role
**Locations:**
- `/staff/dashboard` - Worker dashboard
- `/staff/complaints` - Assigned complaints

**Features:**
- Worker dashboard showing:
  - Only complaints assigned to them
  - Status update dropdown
  - Proof image upload
  - Comments/notes section
- Actions:
  - Update status (Acknowledged, In Progress, Under Review, Resolved)
  - Upload proof images/videos
  - Add progress notes
  - Auto email notification when resolved

### 5. ✅ Complaint Assignment System
**Route:** `POST /admin/complaint/<id>/assign`

**Features:**
- Admin can assign complaints to any worker/staff
- Select from dropdown of available staff
- Set priority during assignment
- Add admin notes
- Auto-update status to "Acknowledged"
- Email notification sent to assigned worker

### 6. ✅ Email Notification System
**Location:** `utils/email_service.py`

**Notifications Sent:**
1. **Complaint Submitted** - Sent to user when complaint is submitted
2. **Complaint Assigned** - Sent to worker when complaint is assigned
3. **Complaint Resolved** - Sent to user when complaint is resolved
4. **Status Updated** - Sent to user when status changes

**Configuration:**
- Optional feature (system works without email)
- Configure via environment variables:
  ```bash
  ENABLE_EMAIL_NOTIFICATIONS=True
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=your-email@gmail.com
  SMTP_PASSWORD=your-app-password
  ```

### 7. ✅ Feedback & Rating System
**Route:** `/complaint/<id>/feedback`

**Features:**
- 5-star rating system
- Optional text feedback
- Only shown for resolved/closed complaints
- One feedback per complaint
- Displayed in complaint details
- Beautiful star rating UI

### 8. ✅ Admin Analytics Page
**Location:** `/admin/analytics`

**Charts Included:**
- Complaints per category (Pie chart)
- Complaints per status (Bar chart)
- Monthly complaint trends (Line chart)
- Top problem areas (Bar chart)
- Priority distribution (Pie chart)
- Resolution time statistics (Bar chart)

**Charts powered by:** Chart.js

## 📊 MongoDB Collections

### `users`
- Stores user accounts (citizens, staff, admin)
- Password hashed with bcrypt
- Role-based access control

### `complaints`
- Stores all complaint data
- Includes: user_id, category, location, description, images, status, priority, assigned_to, progress, feedback, etc.

### `activity_logs`
- Audit trail of all actions
- Tracks: complaint_id, action, user_id, details, timestamp, ip_address

## 🔐 Authentication & Authorization

### Roles:
1. **Citizen** - Can:
   - Register/Login
   - Submit complaints
   - Track their complaints
   - Submit feedback

2. **Staff/Worker** - Can:
   - Login to worker dashboard
   - View assigned complaints
   - Update status
   - Upload proof images
   - Add progress notes

3. **Admin** - Can:
   - All staff permissions
   - View all complaints
   - Assign complaints
   - Manage users
   - View analytics
   - Manage staff

## 🚀 Quick Start Guide

### 1. Installation
```bash
cd Complaint_Management_System_Municipal_Services
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. MongoDB Setup
- **Option 1:** Local MongoDB
  - Install MongoDB Community Edition
  - Start MongoDB service
- **Option 2:** MongoDB Atlas (Recommended)
  - Sign up at https://www.mongodb.com/cloud/atlas
  - Create free cluster
  - Get connection string
  - Update `MONGODB_URI` in `config.py`

### 3. Configure Email (Optional)
Create `.env` file or set environment variables:
```bash
ENABLE_EMAIL_NOTIFICATIONS=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 4. Run Application
```bash
python app.py
```

### 5. Access System
- Home: `http://localhost:5000`
- Register: `http://localhost:5000/register`
- Login: `http://localhost:5000/login`
- Admin Login:
  - Email: `admin@municipal.gov`
  - Password: `admin123`

## 📱 User Flows

### Citizen Flow:
1. Register → Login
2. Submit Complaint → Upload image (optional)
3. Track Complaint → View status
4. Get notified via email
5. Submit feedback when resolved

### Worker Flow:
1. Login with staff account
2. View assigned complaints
3. Update status to "In Progress"
4. Upload proof image
5. Add progress notes
6. Mark as "Resolved"

### Admin Flow:
1. Login with admin account
2. View all complaints
3. Filter/search complaints
4. Assign to worker
5. Change priority
6. View analytics
7. Manage users/staff

## 🎨 UI Features

- Responsive design (mobile-friendly)
- Status badges with colors
- Progress bars
- Image preview
- Form validation
- Loading states
- Flash messages
- Beautiful charts
- Professional layout

## 🔧 Configuration Files

- `config.py` - Main configuration
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (optional)

## 📝 Key Files

- `app.py` - Main Flask application
- `utils/helpers.py` - Helper functions
- `utils/decorators.py` - Authentication decorators
- `utils/email_service.py` - Email notification service
- `templates/` - HTML templates
- `static/` - CSS, JS, images, uploads

## 🎉 All Requirements Met!

✅ Complaint submission module with full form  
✅ User complaint tracking page  
✅ Admin complaint management with filters  
✅ Worker/staff role with dashboard  
✅ Complaint assignment system  
✅ Email notification system  
✅ Feedback & rating system  
✅ Admin analytics with charts  
✅ MongoDB integration  
✅ Authentication & authorization  
✅ File upload handling  
✅ Responsive UI  
✅ Form validation  

## 🚀 System is Ready for Production!

All modules are fully functional and integrated. The system is ready to deploy and use.

