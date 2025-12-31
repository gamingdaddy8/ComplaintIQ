import sqlite3
import pandas as pd
from datetime import datetime
import bcrypt

class DataHandler:
    def __init__(self, db_name="complaints.db"):
        self.db_name = db_name
        self.create_table()

    def get_conn(self):
        """Helper to get a fresh connection every time."""
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def create_table(self):
        """Creates tables if they don't exist."""
        conn = self.get_conn()
        
        # 1. Complaints Table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint TEXT,
            category TEXT,
            sentiment TEXT,
            urgency TEXT,
            priority TEXT,
            action TEXT,
            status TEXT DEFAULT 'Open',
            date_logged TEXT,
            customer_name TEXT,
            account_number TEXT,
            email TEXT,
            phone TEXT
        )
        """)

        # 2. Keywords Table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            category TEXT,
            word TEXT,
            UNIQUE(category, word)
        )
        """)

        # 3. Users Table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            full_name TEXT
        )
        """)
        
        # Seed Keywords
        check = conn.execute("SELECT count(*) FROM keywords").fetchone()[0]
        if check == 0:
            defaults = [
                ('Loan', 'emi'), ('Loan', 'interest'), ('Loan', 'loan'),
                ('Credit Card', 'card'), ('Credit Card', 'limit'), ('Credit Card', 'statement'),
                ('Fraud', 'scam'), ('Fraud', 'hack'), ('Fraud', 'unauthorized'),
                ('Account', 'balance'), ('Account', 'saving'), ('Account', 'deposit')
            ]
            conn.executemany("INSERT INTO keywords (category, word) VALUES (?, ?)", defaults)
        
        conn.commit()
        conn.close()

    # --- CORE METHODS ---

    def save_results(self, df):
        conn = self.get_conn()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for _, row in df.iterrows():
            conn.execute("""
                INSERT INTO complaints (
                    complaint, category, sentiment, urgency, priority, 
                    action, status, date_logged, customer_name, 
                    account_number, email, phone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['complaint'], 
                row['category'], 
                row['sentiment'], 
                row['urgency'], 
                row['priority'], 
                row.get('action', 'Pending Review'), 
                'Open', 
                current_time, 
                str(row.get('customer_name', 'Unknown')), 
                str(row.get('account_number', 'N/A')), 
                str(row.get('email', '')), 
                str(row.get('phone', ''))
            ))
        
        conn.commit()
        conn.close()

    def load_data(self):
        conn = self.get_conn()
        try:
            df = pd.read_sql("SELECT * FROM complaints", conn)
        except:
            df = pd.DataFrame()
        finally:
            conn.close()
        return df

    def get_metrics(self):
        df = self.load_data()
        if df.empty: return {"total": 0, "critical": 0, "resolved": 0}
        
        return {
            "total": len(df),
            "critical": len(df[df["priority"] == "P1 - Critical"]),
            "resolved": len(df[df["status"] == "Resolved"])
        }

    # --- MISSING METHODS RESTORED HERE ---
    
    def update_complaint(self, complaint_id, status, action):
        """Updates the status and action of a complaint."""
        conn = self.get_conn()
        try:
            conn.execute("UPDATE complaints SET status = ?, action = ? WHERE id = ?", (status, action, complaint_id))
            conn.commit()
            return True
        except: 
            return False
        finally: 
            conn.close()

    def get_complaint(self, complaint_id):
        """Fetches a single complaint (Used for sending emails)."""
        conn = self.get_conn()
        try:
            cursor = conn.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,))
            row = cursor.fetchone()
            if row:
                # Convert tuple to dict
                cols = [description[0] for description in cursor.description]
                return dict(zip(cols, row))
        except: 
            pass
        finally: 
            conn.close()
        return None

    # --- SETTINGS & AUTH ---
        
    def get_keywords(self):
        conn = self.get_conn()
        cursor = conn.execute("SELECT category, word FROM keywords")
        kb = {}
        for cat, word in cursor.fetchall():
            if cat not in kb: kb[cat] = []
            kb[cat].append(word)
        conn.close()
        return kb

    def add_keyword(self, category, word):
        conn = self.get_conn()
        try:
            conn.execute("INSERT INTO keywords (category, word) VALUES (?, ?)", (category, word.lower()))
            conn.commit()
            return True
        except: return False
        finally: conn.close()
    
    def create_user(self, email, password, full_name):
        conn = self.get_conn()
        try:
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            conn.execute("INSERT INTO users (email, password, full_name) VALUES (?, ?, ?)", 
                         (email, hashed, full_name))
            conn.commit()
            return True
        except: return False
        finally: conn.close()

    def authenticate_user(self, email, password):
        conn = self.get_conn()
        row = conn.execute("SELECT password, full_name FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if row and bcrypt.checkpw(password.encode(), row[0]):
            return {"email": email, "name": row[1]}
        return None