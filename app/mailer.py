import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# --- CONFIGURATION ---
# Load environment variables from the .env file
load_dotenv()

# Securely fetch credentials
SENDER_EMAIL = os.getenv("GMAIL_USER")
SENDER_PASSWORD = os.getenv("GMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_resolution_email(to_email, customer_name, complaint_id, status, action_note):
    """
    Sends a formatted email to the customer when their ticket is updated.
    """
    
    # Safety Check: Ensure credentials exist before trying to send
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ Error: Email credentials not found. Make sure you have a .env file.")
        return False

    try:
        # 1. Setup the Email
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"Update on Complaint #{complaint_id}: {status}"

        # 2. Create the Email Body
        body = f"""
        Dear {customer_name},

        Your complaint (Ticket #{complaint_id}) has been updated.

        --------------------------------------------------
        Current Status: {status}
        Agent Note: {action_note}
        --------------------------------------------------

        If your issue is marked as 'Resolved', no further action is needed.
        If you have questions, please reply to this email.

        Best regards,
        Bank Support Team
        """
        
        msg.attach(MIMEText(body, 'plain'))

        # 3. Connect to Server and Send
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False