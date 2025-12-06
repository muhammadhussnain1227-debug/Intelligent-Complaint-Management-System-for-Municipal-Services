# Quick Setup Guide

## Step-by-Step Installation

### 1. Install Python Dependencies

```bash
cd templatemo_593_personal_shape
pip install -r requirements.txt
```

### 2. Install MongoDB

#### Option A: Local MongoDB
- Download from: https://www.mongodb.com/try/download/community
- Install and start MongoDB service
- Default connection: `mongodb://localhost:27017/`

#### Option B: MongoDB Atlas (Cloud)
- Sign up at: https://www.mongodb.com/cloud/atlas
- Create a free cluster
- Get your connection string
- Update `config.py` with your Atlas connection string

### 3. Configure the Application

Edit `config.py`:
```python
MONGODB_URI = 'mongodb://localhost:27017/'  # Local MongoDB
# OR
MONGODB_URI = 'mongodb+srv://username:password@cluster.mongodb.net/'  # Atlas
```

Or set environment variables:
```bash
# Windows (PowerShell)
$env:SECRET_KEY="your-secret-key"
$env:MONGODB_URI="mongodb://localhost:27017/"

# Linux/Mac
export SECRET_KEY="your-secret-key"
export MONGODB_URI="mongodb://localhost:27017/"
```

### 4. Run the Application

```bash
python app.py
```

The application will start at: `http://localhost:5000`

### 5. Default Admin Login

On first run, a default admin account is created:

- **Email**: `admin@municipal.gov`
- **Password**: `admin123`

⚠️ **IMPORTANT**: Change this password immediately after first login!

## Testing the System

### As a Citizen:

1. Go to `http://localhost:5000`
2. Click "Register" and create an account
3. Login with your credentials
4. Submit a complaint with:
   - Select a category
   - Enter location
   - Write description
   - Optionally upload a photo
5. View your dashboard to see all complaints
6. Track individual complaints

### As an Admin:

1. Login with admin credentials
2. View the admin dashboard for statistics
3. Go to "Complaints" to see all complaints
4. Filter by category, status, or search
5. Update complaint status
6. Add comments
7. Mark complaints as urgent
8. View analytics dashboard with charts

## Troubleshooting

### MongoDB Connection Error

**Error**: `MongoDB connection error`

**Solutions**:
- Check if MongoDB is running: `mongod --version`
- Verify connection string in `config.py`
- Check firewall settings
- For Atlas: Check IP whitelist and credentials

### Port Already in Use

**Error**: `Address already in use`

**Solution**: Change the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Use port 5001 instead
```

### Module Not Found

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### File Upload Not Working

**Error**: Photos not uploading

**Solutions**:
- Check `static/uploads/` directory exists
- Verify file size is under 16MB
- Check file permissions on uploads directory

## Production Deployment

Before deploying to production:

1. **Change SECRET_KEY** in `config.py` or environment variable
2. **Use environment variables** for sensitive data
3. **Set debug=False** in `app.py`
4. **Use a production WSGI server** (e.g., Gunicorn, uWSGI)
5. **Configure proper MongoDB security** (authentication, encryption)
6. **Set up SSL/TLS** certificates
7. **Configure file upload limits** and storage
8. **Set up logging** and monitoring
9. **Change default admin password**
10. **Regular backups** of MongoDB database

## Database Backup

### Backup MongoDB:

```bash
# Windows
mongodump --uri="mongodb://localhost:27017/" --db=municipal_complaints --out=backup

# Linux/Mac
mongodump --uri="mongodb://localhost:27017/" --db=municipal_complaints --out=backup
```

### Restore MongoDB:

```bash
mongorestore --uri="mongodb://localhost:27017/" --db=municipal_complaints backup/municipal_complaints
```

## Next Steps

- Customize complaint categories in `config.py`
- Add email notifications
- Implement SMS alerts for urgent complaints
- Add file export (CSV, PDF) for reports
- Set up automated status updates
- Add user profile management
- Implement complaint ratings/feedback

---

For more details, see `README.md`

