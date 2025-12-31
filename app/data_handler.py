import sqlite3
import pandas as pd
from datetime import datetime
import bcrypt  # <--- WE USE THIS DIRECTLY NOW

class DataHandler:
    def __init__(self, db_name="complaints.db"):
        # check_same_thread=False is needed for FastAPI multithreading
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        """Creates all necessary tables if they don't exist."""
        
        # 1. Complaints Table
        query_complaints = """
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint TEXT,
            category TEXT,
            sentiment TEXT,
            urgency TEXT,
            priority TEXT,
            action TEXT,
            status TEXT DEFAULT 'Open',
            date_logged TIMESTAMP,
            customer_name TEXT,
            account_number TEXT,
            email TEXT,
            phone TEXT
        )
        """
        self.conn.execute(query_complaints)

        # 2. Keywords Table
        query_keywords = """
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            word TEXT UNIQUE
        )
        """
        self.conn.execute(query_keywords)

        # 3. Users Table (For Login)
        query_users = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            role TEXT DEFAULT 'Agent'
        )
        """
        self.conn.execute(query_users)
        
        self.conn.commit()
        self.initialize_keywords()

    def initialize_keywords(self):
        """Adds default keywords if table is empty."""
        try:
            check = self.conn.execute("SELECT count(*) FROM keywords").fetchone()[0]
            if check == 0:
                defaults = {
                    "Loan": ["loan", "emi", "interest", "repayment"],
                    "Credit Card": ["card", "credit", "debit", "limit"],
                    "Account": ["account", "balance", "statement", "transfer"],
                    "Fraud": ["fraud", "scam", "unauthorized", "hack"],
                    "Customer Service": ["service", "support", "response", "delay"]
                }
                for cat, words in defaults.items():
                    for w in words:
                        self.conn.execute("INSERT INTO keywords (category, word) VALUES (?, ?)", (cat, w))
                self.conn.commit()
                print("✅ Default keywords initialized.")
        except Exception as e:
            print(f"⚠️ Warning initializing keywords: {e}")

    # --- CORE METHODS ---

    def save_results(self, results_df):
        if "date_logged" not in results_df.columns:
            results_df["date_logged"] = datetime.now()
        if "status" not in results_df.columns:
            results_df["status"] = "Open"
        results_df.to_sql("complaints", self.conn, if_exists="append", index=False)

    def load_data(self):
        return pd.read_sql("SELECT * FROM complaints", self.conn)

    def get_metrics(self):
        df = self.load_data()
        if df.empty: return {"total": 0, "critical": 0, "resolved": 0}
        return {
            "total": len(df),
            "critical": len(df[df["priority"] == "P1 - Critical"]),
            "resolved": len(df[df["status"] == "Resolved"])
        }

    def get_complaint(self, complaint_id):
        cursor = self.conn.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,))
        row = cursor.fetchone()
        if row:
            cols = [description[0] for description in cursor.description]
            return dict(zip(cols, row))
        return None

    def update_complaint(self, complaint_id, status, action):
        try:
            self.conn.execute("UPDATE complaints SET status = ?, action = ? WHERE id = ?", (status, action, complaint_id))
            self.conn.commit()
            return True
        except: return False

    def get_keywords(self):
        cursor = self.conn.execute("SELECT category, word FROM keywords")
        keywords = {}
        for row in cursor.fetchall():
            cat, word = row
            if cat not in keywords: keywords[cat] = []
            keywords[cat].append(word)
        return keywords

    def add_keyword(self, category, word):
        try:
            self.conn.execute("INSERT INTO keywords (category, word) VALUES (?, ?)", (category, word.lower()))
            self.conn.commit()
            return True
        except: return False

    # --- NEW SECURITY METHODS (DIRECT BCRYPT) ---

    def get_password_hash(self, password):
        """Hashes password using bcrypt directly."""
        # Convert password to bytes
        pwd_bytes = password.encode('utf-8')
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        # Return as string for storage
        return hashed.decode('utf-8')

    def verify_password(self, plain_password, hashed_password):
        """Verifies password using bcrypt directly."""
        try:
            pwd_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(pwd_bytes, hashed_bytes)
        except ValueError:
            return False

    def create_user(self, email, password, full_name):
        """Registers a new user."""
        try:
            hashed_pw = self.get_password_hash(password)
            self.conn.execute(
                "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)", 
                (email, hashed_pw, full_name)
            )
            self.conn.commit()
            print(f"✅ Created user: {email}")
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️ Registration Failed: {email} already exists.")
            return False
        except Exception as e:
            print(f"❌ CRITICAL DB ERROR: {e}") 
            return False

    def authenticate_user(self, email, password):
        """Checks email and password."""
        cursor = self.conn.execute("SELECT password_hash, full_name, role FROM users WHERE email=?", (email,))
        row = cursor.fetchone()
        if row:
            stored_hash = row[0]
            if self.verify_password(password, stored_hash):
                return {"email": email, "name": row[1], "role": row[2]}
        return None
        
    def close(self):
        self.conn.close()