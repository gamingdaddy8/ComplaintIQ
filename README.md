# 🏦 ComplaintIQ - AI-Powered Banking Resolution System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![Status](https://img.shields.io/badge/Status-Completed-success)

**ComplaintIQ** is an intelligent, full-stack complaint management system designed for the Banking & Fintech sector. It automates the classification, prioritization, and resolution of customer tickets using Artificial Intelligence.

---

## 🚀 Key Features

### 🧠 AI & Automation
* **Automatic Sentiment Analysis:** Detects if a customer is Angry, Neutral, or Happy.
* **Smart Categorization:** Automatically routes tickets to *Loan, Credit Card, Fraud,* or *Account* departments.
* **Urgency Detection:** Flags "High Priority" issues (like Fraud) instantly.

### 🛡️ Security & Role Management
* **Secure Authentication:** Hashed password storage using `bcrypt`.
* **Role-Based Access:** Secure Agent Login and Registration portal.
* **Data Isolation:** Shared team dashboard for collaborative ticket resolution.

### 📊 Analytics & Reporting
* **Interactive Dashboard:** Real-time metrics on total, critical, and resolved cases.
* **PDF Reporting:** Auto-generates professional "Executive Summary" PDF reports for managers.
* **Batch Processing:** Upload CSV files to process thousands of complaints in seconds.

### 📧 Customer Engagement
* **Automated Email Alerts:** Sends real-time email notifications to customers when their ticket is resolved.

---

## 🛠️ Tech Stack

* **Backend:** FastAPI (Python)
* **Frontend:** Streamlit
* **Database:** SQLite (Production-ready for prototype) / PostgreSQL (Supported)
* **AI Engine:** HuggingFace Transformers (Sentiment Pipeline)
* **Visualization:** Plotly & Pandas

---

## ⚙️ Installation Guide

Follow these steps to run the project locally.

### Prerequisites
* Python 3.9 or higher
* Git

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/ComplaintIQ.git](https://github.com/YOUR_USERNAME/ComplaintIQ.git)
cd ComplaintIQ


2. Create Virtual Environment
Bash

python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
3. Install Dependencies
Bash

pip install -r requirements.txt
🏃‍♂️ How to Run
You need to run the Backend and Frontend in separate terminals.

Terminal 1: Start Backend (API)
Bash

uvicorn app.main:app --reload
Server will start at: http://127.0.0.1:8000

Terminal 2: Start Frontend (UI)
Bash

streamlit run frontend/app.py
App will open in your browser at: http://localhost:8501


--- Future Enhancements 
 Integration with WhatsApp Business API.

 Multi-Language Support (Hindi/Regional).

 Migration to Cloud PostgreSQL for global scaling.

Developed by Rudresh Gawas  | 2025