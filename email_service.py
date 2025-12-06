"""
Email Notification Service
Handles sending emails for complaint notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def send_email(to_email, subject, message, html_content=None):
    """
    Send email notification
    Args:
        to_email: Recipient email address
        subject: Email subject
        message: Plain text message
        html_content: Optional HTML content
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        # Check if email notifications are enabled
        if not current_app.config.get('ENABLE_EMAIL_NOTIFICATIONS', False):
            print(f"Email notifications disabled. Would send to {to_email}: {subject}")
            return True  # Return True to not break the flow
        
        # Get SMTP configuration
        smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_user = current_app.config.get('SMTP_USER', '')
        smtp_password = current_app.config.get('SMTP_PASSWORD', '')
        
        if not smtp_user or not smtp_password:
            print(f"SMTP credentials not configured. Email not sent to {to_email}")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_email
        
        # Add plain text and HTML
        part1 = MIMEText(message, 'plain')
        msg.attach(part1)
        
        if html_content:
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"✓ Email sent successfully to {to_email}: {subject}")
        return True
        
    except Exception as e:
        print(f"✗ Error sending email to {to_email}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def send_complaint_submitted_email(user_email, user_name, complaint_id, category):
    """Send email when complaint is submitted"""
    subject = f"Complaint Submitted Successfully - {complaint_id}"
    message = f"""
Dear {user_name},

Your complaint has been submitted successfully!

Complaint ID: {complaint_id}
Category: {category}

You can track the status of your complaint by logging into your account.

Thank you for reporting this issue. We will review it and get back to you soon.

Best regards,
Municipal Services Team
    """
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #6366f1;">Complaint Submitted Successfully!</h2>
            <p>Dear {user_name},</p>
            <p>Your complaint has been submitted successfully!</p>
            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Complaint ID:</strong> {complaint_id}</p>
                <p><strong>Category:</strong> {category}</p>
            </div>
            <p>You can track the status of your complaint by logging into your account.</p>
            <p>Thank you for reporting this issue. We will review it and get back to you soon.</p>
            <p>Best regards,<br>Municipal Services Team</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, message, html_content)

def send_complaint_assigned_email(worker_email, worker_name, complaint_id, category, location):
    """Send email when complaint is assigned to worker"""
    subject = f"New Complaint Assigned - {complaint_id}"
    message = f"""
Dear {worker_name},

A new complaint has been assigned to you:

Complaint ID: {complaint_id}
Category: {category}
Location: {location}

Please log in to your dashboard to view details and take action.

Best regards,
Municipal Services Team
    """
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #3b82f6;">New Complaint Assigned</h2>
            <p>Dear {worker_name},</p>
            <p>A new complaint has been assigned to you:</p>
            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Complaint ID:</strong> {complaint_id}</p>
                <p><strong>Category:</strong> {category}</p>
                <p><strong>Location:</strong> {location}</p>
            </div>
            <p>Please log in to your dashboard to view details and take action.</p>
            <p>Best regards,<br>Municipal Services Team</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(worker_email, subject, message, html_content)

def send_complaint_resolved_email(user_email, user_name, complaint_id, category):
    """Send email when complaint is resolved"""
    subject = f"Complaint Resolved - {complaint_id}"
    message = f"""
Dear {user_name},

Great news! Your complaint has been resolved:

Complaint ID: {complaint_id}
Category: {category}

Please log in to view details and provide feedback if you wish.

Thank you for your patience.

Best regards,
Municipal Services Team
    """
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #10b981;">Complaint Resolved!</h2>
            <p>Dear {user_name},</p>
            <p>Great news! Your complaint has been resolved:</p>
            <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
                <p><strong>Complaint ID:</strong> {complaint_id}</p>
                <p><strong>Category:</strong> {category}</p>
            </div>
            <p>Please log in to view details and provide feedback if you wish.</p>
            <p>Thank you for your patience.</p>
            <p>Best regards,<br>Municipal Services Team</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, message, html_content)

def send_status_update_email(user_email, user_name, complaint_id, status):
    """Send email when complaint status is updated"""
    subject = f"Complaint Status Updated - {complaint_id}"
    message = f"""
Dear {user_name},

Your complaint status has been updated:

Complaint ID: {complaint_id}
New Status: {status}

Please log in to view more details.

Best regards,
Municipal Services Team
    """
    
    return send_email(user_email, subject, message)

