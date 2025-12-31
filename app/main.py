from fastapi import FastAPI, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import io
from app.data_handler import DataHandler
from app.chatbot_engine import ChatbotEngine
from app.complaint_analyzer import ComplaintAnalyzer # <--- IMPORTED BACK

# Optional: Report Generator
try:
    from app.report_generator import generate_pdf_report
except ImportError:
    generate_pdf_report = None

try:
    from app.mailer import send_resolution_email
except ImportError:
    send_resolution_email = None

app = FastAPI()

# 1. Initialize Database
db = DataHandler()

# 2. Initialize Custom Analyzer
# We pass the current DB keywords to it immediately
analyzer = ComplaintAnalyzer(keywords_dict=db.get_keywords())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class KeywordRequest(BaseModel):
    category: str
    word: str

class ComplaintUpdate(BaseModel):
    id: int
    status: str
    action: str

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "ComplaintIQ Backend is running"}

@app.post("/analyze")
async def analyze_complaints(file: UploadFile = File(...)):
    # 1. Read File
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except:
        return {"error": "Invalid CSV file."}

    # 2. CRITICAL: Sync Analyzer with Settings
    # This ensures new keywords from the Settings tab are used immediately
    latest_keywords = db.get_keywords()
    analyzer.update_keywords(latest_keywords)

    analyzed_data = []
    
    # 3. Process Rows using the External Analyzer
    for index, row in df.iterrows():
        text = str(row.get('complaint', ''))
        if not text or text.lower() == 'nan': continue
        
        # --- CALL THE CUSTOM ANALYZER ---
        result = analyzer.analyze(text)
        
        # Add Customer Metadata
        result["customer_name"] = str(row.get('Customer Name', 'Unknown'))
        result["account_number"] = str(row.get('Account Number', 'N/A'))
        result["email"] = str(row.get('Email', ''))
        result["phone"] = str(row.get('Phone', ''))
        
        analyzed_data.append(result)

    # 4. Save
    if analyzed_data:
        results_df = pd.DataFrame(analyzed_data)
        db.save_results(results_df)
        return {
            "message": "Success",
            "total_new_complaints": len(results_df),
            "sample_output": results_df.head(3).to_dict(orient="records")
        }
    else:
        return {"error": "No valid data found."}

@app.post("/chat")
def chat(query: str):
    """Smart Chatbot Endpoint"""
    current_data = db.load_data()
    keywords = db.get_keywords() 
    engine = ChatbotEngine(current_data, keywords)
    
    result = engine.respond(query)
    
    if isinstance(result, dict):
        return result 
    else:
        return {"response": result}

@app.get("/dashboard-stats")
def get_stats():
    return db.get_metrics()

@app.get("/all-complaints")
def get_all():
    df = db.load_data()
    return [] if df.empty else df.to_dict(orient="records")

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
        # 2. Check if we need to send email
        # We only email if status is Resolved/Escalated AND we have the mailer module
        if update_data.status in ["Resolved", "Escalated"] and send_resolution_email:
            # Get customer details
            details = db.get_complaint(update_data.id)
            
            if details and details.get("email"):
                print(f"📧 Sending email to {details['email']}...")
                try:
                    send_resolution_email(
                        to_email=details["email"],
                        customer_name=details["customer_name"],
                        complaint_id=update_data.id,
                        status=update_data.status,
                        action_note=update_data.action
                    )
                except Exception as e:
                    print(f"⚠️ Email failed: {e}")
        
        return {"message": "Update successful"}
    else:
        return {"error": "Failed to update database"}

@app.get("/generate-report")
def get_pdf_report():
    if generate_pdf_report is None: return {"error": "Module missing."}
    data = db.load_data()
    if data.empty: return {"error": "No data"}
    pdf_bytes = generate_pdf_report(data.to_dict(orient="records"))
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=complaint_report.pdf"})

# --- AUTH ---
@app.post("/login")
def login(user: UserLogin):
    u = db.authenticate_user(user.email, user.password)
    return {"user": u} if u else Response(status_code=401)

@app.post("/register")
def register(user: UserRegister):
    if db.create_user(user.email, user.password, user.full_name):
        return {"message": "User created"}
    return Response(status_code=400)

# --- SETTINGS ---
@app.get("/keywords")
def get_kw(): return db.get_keywords()

@app.post("/add-keyword")
def add_kw(k: KeywordRequest):
    if db.add_keyword(k.category, k.word): 
        return {"message": "Added"}
    return {"error": "Failed"}