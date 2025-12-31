from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import io

# ... (existing imports) ...

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

from app.complaint_analyzer import ComplaintAnalyzer
from app.chatbot_engine import ChatbotEngine
from app.data_handler import DataHandler
from app.mailer import send_resolution_email  # <--- NEW IMPORT for Email Feature
from fastapi.responses import Response # <--- Needed to send file
from app.report_generator import generate_pdf_report # <--- Your new file

app = FastAPI(title="ComplaintIQ API")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# INITIALIZATION
# -------------------------
# 1. Initialize Database Handler FIRST
db = DataHandler()

# 2. Load Keywords from Database
keywords_from_db = db.get_keywords()

# 3. Initialize Logic Classes with those keywords
analyzer = ComplaintAnalyzer(keywords_dict=keywords_from_db)

@app.get("/")
def home():
    return {"message": "ComplaintIQ Backend is running"}

# -------------------------
# CSV Analysis Endpoint (UPDATED FOR CUSTOMER DATA)
# -------------------------
@app.post("/analyze")
async def analyze_complaints(file: UploadFile = File(...)):
    # Read the file content
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    # VALIDATION: Check for required columns
    # We now require Customer Name and Email to support notifications
    required_cols = ["complaint", "Customer Name", "Email"]
    if not all(col in df.columns for col in required_cols):
        return {"error": f"CSV must contain columns: {required_cols}"}

    analyzed_data = []

    # Iterate through rows to keep customer data synced with analysis
    for index, row in df.iterrows():
        # 1. Analyze the text
        result = analyzer.analyze(row["complaint"])
        
        # 2. Attach Customer Info to the result
        result["customer_name"] = row.get("Customer Name", "Unknown")
        result["email"] = row.get("Email", "")
        result["phone"] = row.get("Phone", "")
        result["account_number"] = row.get("Account Number", "")
        
        analyzed_data.append(result)

    results_df = pd.DataFrame(analyzed_data)

    # Save to Database (Persistence!)
    db.save_results(results_df)

    return {
        "message": "Complaints analyzed and saved successfully",
        "total_new_complaints": len(results_df),
        "sample_output": results_df.head(3).to_dict(orient="records")
    }

# -------------------------
# Chatbot Endpoint
# -------------------------
@app.post("/chat")
def chat(query: str):
    # Load latest data from DB every time we chat
    current_data = db.load_data()
    
    if current_data.empty:
        return {"error": "No data available. Please upload a file first."}

    # Re-initialize chatbot with latest data
    chatbot = ChatbotEngine(current_data)
    response = chatbot.respond(query)

    if isinstance(response, str):
        return {"response": response}

    if isinstance(response, pd.Series):
        return {"response": response.to_dict()}
        
    return {
        "response": response.to_dict(orient="records")
    }

@app.get("/dashboard-stats")
def get_stats():
    """Returns metrics for the Dashboard"""
    return db.get_metrics()

# -------------------------
# Analytics Endpoint
# -------------------------
@app.get("/all-complaints")
def get_all_complaints():
    """Returns all records for the Analytics Dashboard"""
    df = db.load_data()
    if df.empty:
        return []
    return df.to_dict(orient="records")

# -------------------------
# Ticket Resolution Endpoint (UPDATED WITH EMAIL TRIGGER)
# -------------------------
class ComplaintUpdate(BaseModel):
    id: int
    status: str
    action: str

@app.post("/update-complaint")
def update_complaint_status(update_data: ComplaintUpdate):
    """Updates status and sends email if resolved."""
    
    # 1. Update Database
    success = db.update_complaint(
        update_data.id, 
        update_data.status, 
        update_data.action
    )
    
    if success:
        # 2. Check if we need to send email (Only if Resolved/Escalated)
        if update_data.status in ["Resolved", "Escalated"]:
            # Fetch customer details for this specific complaint ID
            complaint_details = db.get_complaint(update_data.id)
            
            # Send the email if the user has an email address
            if complaint_details and complaint_details.get("email"):
                print(f"Attempting to email {complaint_details['email']}...")
                send_resolution_email(
                    to_email=complaint_details["email"],
                    customer_name=complaint_details["customer_name"],
                    complaint_id=update_data.id,
                    status=update_data.status,
                    action_note=update_data.action
                )
        
        return {"message": "Update successful"}
    else:
        return {"error": "Failed to update database"}

# -------------------------
# Settings / Keywords Endpoints
# -------------------------
class KeywordAdd(BaseModel):
    category: str
    word: str

@app.get("/keywords")
def get_keywords():
    """Fetch current keywords for the Settings page."""
    return db.get_keywords()

@app.post("/add-keyword")
def add_new_keyword(data: KeywordAdd):
    """Adds a new keyword to DB and updates the live AI model."""
    success = db.add_keyword(data.category, data.word)
    
    if success:
        # Crucial: Update the running AI instance immediately!
        new_list = db.get_keywords()
        analyzer.update_keywords(new_list)
        return {"message": f"Added '{data.word}' to category '{data.category}'"}
    else:
        return {"error": "Keyword already exists or failed to add."}

# NEW: PDF Report Endpoint
# -------------------------
@app.get("/generate-report")
def get_pdf_report():
    """Generates and returns a PDF file of all complaints."""
    # 1. Get data from DB
    data = db.load_data()
    
    if data.empty:
        return {"error": "No data available to generate report"}
    
    # Convert DataFrame to list of dicts
    records = data.to_dict(orient="records")
    
    # 2. Generate PDF using our helper
    pdf_bytes = generate_pdf_report(records)
    
    # 3. Return as a File Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=complaint_report.pdf"}
    )

# AUTHENTICATION Endpoints
# -------------------------
@app.post("/register")
def register_user(user: UserRegister):
    success = db.create_user(user.email, user.password, user.full_name)
    if success:
        return {"message": "User registered successfully"}
    else:
        return {"error": "Email already exists"}

@app.post("/login")
def login_user(user: UserLogin):
    user_data = db.authenticate_user(user.email, user.password)
    if user_data:
        return {"message": "Login successful", "user": user_data}
    else:
        return {"error": "Invalid credentials"}