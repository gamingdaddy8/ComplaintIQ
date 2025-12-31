import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# CONFIGURATION (Ideally, use environment variables for this!)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "marketingofficial560@gmail.com" # <--- REPLACE THIS
SENDER_PASSWORD = "euvj sxaj gjsj mnwp" # <--- REPLACE WITH YOUR APP PASSWORD

def send_resolution_email(to_email, customer_name, complaint_id, status, action_note):
    """Sends an email to the customer when their complaint status changes."""
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"Update on Complaint #{complaint_id}: {status}"

        # Email Body
        body = f"""
        Dear {customer_name},

        This is an update regarding your complaint (ID: #{complaint_id}).

        Current Status: {status}
        Bank Remarks: {action_note}

        If your issue is marked as 'Resolved', no further action is needed. 
        If 'Escalated', our senior team will contact you shortly.

        Thank you for banking with us.
        
        Regards,
        ComplaintIQ Automated System
        """

        msg.attach(MIMEText(body, 'plain'))

        # Connect to Server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # Send
        server.send_message(msg)
        server.quit()
        
        print(f"📧 Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False