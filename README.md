# Municipal Complaint Management System

A complete Intelligent Complaint Management System for Municipal Services built with Flask, MongoDB, and a beautiful responsive template.

## 🌟 Features

### Citizen Side
- **User Registration & Login** - Secure authentication with password hashing
- **Submit Complaints** - Report issues with category, location, description, and optional photo upload
- **Complaint Categories**:
  - Garbage Collection
  - Road Damage
  - Water Leakage
  - Drainage Problems
  - Streetlight Malfunction
- **Track Complaint Status** - Real-time status tracking (Pending → In Progress → Resolved)
- **Dashboard** - View all your submitted complaints in one place
- **Photo Upload** - Optional image uploads for better issue documentation

### Admin Side
- **Admin Dashboard** - Overview with statistics and recent complaints
- **View All Complaints** - Filter by category, status, and search functionality
- **Update Complaint Status** - Change status with AJAX updates
- **Mark Urgent Complaints** - Prioritize important issues
- **Add Comments** - Leave notes and updates for citizens
- **Analytics Dashboard** - Charts showing:
  - Complaints by category (bar chart)
  - Status distribution (doughnut chart)
  - Monthly trend (line chart)

## 📁 Project Structure

```
templatemo_593_personal_shape/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── templates/                      # Jinja2 templates
│   ├── base.html                  # Base template
│   ├── index.html                 # Home page
│   ├── register.html              # Registration page
│   ├── login.html                 # Login page
│   ├── dashboard.html             # Citizen dashboard
│   ├── submit_complaint.html      # Submit complaint form
│   ├── track_complaint.html       # Track single complaint
│   ├── admin_dashboard.html       # Admin dashboard
│   ├── admin_view_complaints.html # Admin view all complaints
│   └── admin_analytics.html       # Admin analytics with charts
├── static/
│   ├── css/
│   │   └── templatemo-personal-style.css  # Main stylesheet
│   ├── js/
│   │   └── templatemo-personal-javascripts.js  # JavaScript functions
│   ├── images/                    # Image assets
│   └── uploads/                   # User uploaded complaint photos
└── README.md                      # This file
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB (local or cloud instance)
- pip (Python package manager)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure MongoDB

1. Install MongoDB locally or use MongoDB Atlas (cloud)
2. Update `config.py` with your MongoDB connection string:
   ```python
   MONGODB_URI = 'mongodb://localhost:27017/'  # Local
   # OR
   MONGODB_URI = 'mongodb+srv://user:pass@cluster.mongodb.net/'  # Atlas
   ```

### Step 3: Set Environment Variables (Optional)

Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=municipal_complaints
```

Or update `config.py` directly.

### Step 4: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Step 5: Default Admin Account

On first run, a default admin account is created:
- **Email**: admin@municipal.gov
- **Password**: admin123

⚠️ **Important**: Change the admin password after first login!

## 🗄️ Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "name": String,
  "email": String (unique),
  "phone": String,
  "password": String (bcrypt hashed),
  "role": String ("citizen" or "admin"),
  "created_at": DateTime
}
```

### Complaints Collection
```javascript
{
  "_id": ObjectId,
  "user_id": ObjectId (reference to users),
  "category": String,
  "location": String,
  "description": String,
  "photo": String (file path, optional),
  "status": String ("Pending", "In Progress", "Resolved"),
  "department": String (auto-assigned based on category),
  "is_urgent": Boolean,
  "created_at": DateTime,
  "updated_at": DateTime,
  "comments": Array [
    {
      "comment": String,
      "admin_name": String,
      "timestamp": DateTime
    }
  ]
}
```

### Departments Auto-Assignment
- **Garbage Collection** → Sanitation Department
- **Road Damage** → Public Works Department
- **Water Leakage** → Water Department
- **Drainage Problems** → Public Works Department
- **Streetlight Malfunction** → Electrical Department

## 🎨 Template Integration

This system uses the existing template structure:
- **Navigation**: Fixed navbar with mobile menu
- **Hero Section**: Gradient background with floating shapes
- **Cards**: Portfolio-style cards for displaying complaints
- **Forms**: Consistent form styling with glassmorphism
- **Colors**: Uses CSS variables from the template
- **Responsive**: Fully mobile-responsive design

## 🔐 Security Features

- Password hashing with bcrypt
- Session management with Flask sessions
- Login required decorators for protected routes
- Admin role verification
- File upload validation (size and type)
- Secure filename handling

## 📱 API Endpoints

### Citizen Endpoints
- `GET /` - Home page
- `GET/POST /register` - User registration
- `GET/POST /login` - User login
- `GET /logout` - User logout
- `GET /dashboard` - Citizen dashboard
- `GET/POST /submit_complaint` - Submit new complaint
- `GET /track_complaint/<id>` - View complaint details

### Admin Endpoints
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/complaints` - View all complaints (with filters)
- `POST /admin/complaint/<id>/update` - Update complaint status
- `POST /admin/complaint/<id>/urgent` - Toggle urgent status
- `GET /admin/analytics` - Analytics dashboard

### API Endpoints
- `GET /api/complaint/<id>` - Get complaint details (JSON)

## 🎯 Usage

### For Citizens

1. **Register** an account
2. **Login** to access the dashboard
3. **Submit a complaint** with:
   - Category selection
   - Location address
   - Detailed description
   - Optional photo
   - Urgent flag if needed
4. **Track status** on the dashboard or detail page

### For Admins

1. **Login** with admin credentials
2. **View dashboard** for overview statistics
3. **Filter complaints** by category, status, or search
4. **Update status** directly from the complaints list
5. **Add comments** to communicate with citizens
6. **Mark urgent** for priority handling
7. **View analytics** for insights and trends

## 🛠️ Technologies Used

- **Backend**: Flask (Python)
- **Database**: MongoDB with PyMongo
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: bcrypt for password hashing
- **Charts**: Chart.js for analytics
- **Template**: Custom responsive template

## 📝 Notes

- All file uploads are stored in `static/uploads/`
- Maximum file size: 16MB
- Allowed file types: PNG, JPG, JPEG, GIF, PDF
- Sessions expire after 24 hours
- Auto-assignment of departments based on complaint category

## 🔧 Configuration

Edit `config.py` to customize:
- Complaint categories
- Department assignments
- Upload settings
- Session lifetime
- MongoDB connection

## 🐛 Troubleshooting

### MongoDB Connection Error
- Ensure MongoDB is running
- Check connection string in `config.py`
- Verify network/firewall settings

### File Upload Issues
- Check `static/uploads/` directory exists
- Verify file size limits
- Ensure proper file permissions

### Session Issues
- Clear browser cookies
- Check SECRET_KEY is set
- Verify session configuration

## 📄 License

This project uses a template from TemplateMo. Please refer to their license terms.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📧 Support

For issues or questions, please create an issue in the repository.

---

**Built with ❤️ for Municipal Services**

