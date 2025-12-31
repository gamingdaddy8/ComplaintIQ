import streamlit as st
import requests
import pandas as pd
import io
import plotly.express as px

# -------------------------
# CONFIG & CONSTANTS
# -------------------------
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="ComplaintIQ | Banking Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# UI POLISH: CUSTOM CSS
# -------------------------
def apply_custom_styling():
    st.markdown("""
    <style>
        /* 1. RESTORE Header (make it visible again) */
        [data-testid="stHeader"] {
            background-color: transparent !important; /* Makes it blend in */
            z-index: 1;
        }
        
        /* 2. Hide only the decorative color strip at the very top */
        [data-testid="stDecoration"] {
            display: none;
        }

        /* 3. THE HEADER LOGO (Floating Title) */
        .header-logo {
            position: fixed;
            top: 14px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            
            /* Styling */
            background: linear-gradient(90deg, #1F6FEB, #0D1117);
            color: white;
            padding: 8px 30px;
            border-radius: 12px;
            font-size: 26px; /* Increased Font Size */
            font-weight: 800;
            letter-spacing: 1px;
            border: 1px solid rgba(255,255,255,0.15);
            box-shadow: 0 4px 15px rgba(31, 111, 235, 0.3);
            white-space: nowrap;
        }

        /* 4. Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #161B22;
            border-right: 1px solid rgba(255,255,255,0.1);
            padding-top: 2rem;
        }
        
        /* 5. Button & Metrics */
        .stButton button {
            background-color: #238636;
            color: white;
            font-weight: 600;
            border-radius: 6px;
        }
        [data-testid="stMetricValue"] {
            color: #00E5FF;
        }
    </style>
    
    <div class="header-logo">
        🏦 ComplaintIQ
    </div>
    """, unsafe_allow_html=True)

# Apply styles immediately
apply_custom_styling()

# -------------------------
# SESSION STATE
# -------------------------
if "page" not in st.session_state: st.session_state.page = "login"
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []

# -------------------------
# AUTHENTICATION UI
# -------------------------
def show_login_page():
    # Centered Layout
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # Spacing to push content down
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        
        # Subtitle
        st.markdown("<h3 style='text-align: center; color: white;'>Agent Login</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8B949E; margin-bottom: 20px;'>Enterprise Banking Intelligence System</p>", unsafe_allow_html=True)
        
        # --- LOGIN FORM ---
        if st.session_state.page == "login":
            with st.form("login_form"):
                email = st.text_input("Employee Email")
                password = st.text_input("Password", type="password")
                
                submitted = st.form_submit_button("🔐 Login to Dashboard", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.warning("Please enter both email and password.")
                    else:
                        try:
                            # REAL API CALL
                            res = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
                            
                            if res.status_code == 200:
                                data = res.json()
                                if "user" in data:
                                    st.success("Welcome back!")
                                    st.session_state.authenticated = True
                                    st.session_state.user_info = data["user"]
                                    st.rerun()
                                else:
                                    st.error("Login failed: Invalid response from server.")
                            elif res.status_code == 401:  # Unauthorized
                                st.error("❌ Invalid Email or Password")
                            else:
                                st.error(f"❌ Server Error: {res.text}")
                                
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Could not connect to the Backend. Is it running?")
                        except Exception as e:
                            st.error(f"❌ Unexpected Error: {e}")

            st.markdown("<div style='text-align: center; color: #8B949E; margin-top: 10px;'>or</div>", unsafe_allow_html=True)
            
            if st.button("Create New Account", type="secondary", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()

        # --- SIGNUP FORM ---
        else:
            st.markdown("### New Agent Registration")
            with st.form("signup_form"):
                name = st.text_input("Full Name")
                new_email = st.text_input("Official Email")
                new_pass = st.text_input("Set Password", type="password")
                
                if st.form_submit_button("Register", use_container_width=True):
                    if not name or not new_email or not new_pass:
                        st.warning("Please fill all fields.")
                    else:
                        try:
                            # REAL API CALL
                            payload = {"email": new_email, "password": new_pass, "full_name": name}
                            res = requests.post(f"{API_URL}/register", json=payload)
                            
                            if res.status_code == 200:
                                st.success("✅ Account created! Redirecting to login...")
                                st.session_state.page = "login"
                                import time
                                time.sleep(2)
                                st.rerun()
                            else:
                                # Show the specific error from the backend (e.g. "Email exists")
                                try:
                                    err_msg = res.json().get("detail", "Registration failed.")
                                    st.error(f"⚠️ {err_msg}")
                                except:
                                    st.error("⚠️ Registration failed. Try a different email.")
                                    
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Could not connect to the Backend. Is it running?")
                        except Exception as e:
                            st.error(f"❌ Unexpected Error: {e}")
            
            if st.button("Back to Login", type="secondary", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# HELPER: Highlight Critical Rows
# -------------------------
def highlight_critical(val):
    """Pandas Styler: Highlights 'Critical' cells in Red."""
    color = '#ff4b4b' if val == 'P1 - Critical' else ''
    return f'color: {color}; font-weight: bold'

# -------------------------
# MAIN DASHBOARD
# -------------------------
def show_dashboard():
    # --- SIDEBAR BRANDING ---
    with st.sidebar:
        st.markdown("""
        # 🏦 ComplaintIQ
        **Agent Portal v2.0**
        """)
        st.markdown("---")
        
        # Navigation with Icons
        menu = st.radio("MENU", 
            ["Dashboard", "Analytics & Reports", "Resolution Center", "AI Assistant", "Settings"],
            captions=["Overview & Upload", "Trends & Export", "Manage Tickets", "Chat with Data", "Admin Controls"]
        )
        
        st.markdown("---")
        st.caption("Logged in as: **Admin**")
        if st.button("Logout", type="primary"):
            st.session_state.authenticated = False
            st.rerun()

    # --- 1. DASHBOARD TAB ---
    if menu == "Dashboard":
        st.title("📊 Operational Overview")
        st.markdown("Welcome back. Here is the current system status.")
        
        # Fetch Metrics
        try:
            response = requests.get(f"{API_URL}/dashboard-stats")
            stats = response.json() if response.status_code == 200 else {"total":0, "critical":0, "resolved":0}
        except: stats = {"total":0, "critical":0, "resolved":0}

        # Metrics Row
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Complaints", stats['total'], border=True)
        c2.metric("Critical Attention", stats['critical'], delta="High Priority", delta_color="inverse", border=True)
        c3.metric("Tickets Resolved", stats['resolved'], delta="Completed", border=True)

        st.markdown("---")
        
        # File Uploader Section
        col_upload, col_preview = st.columns([1, 2])
        
        with col_upload:
            st.subheader("📤 Batch Processing")
            st.info("Upload CSV containing: 'Customer Name', 'Account Number', 'Email', 'Phone No','Complaint'.")
            uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
            
            if uploaded_file and st.button("Analyze File", use_container_width=True):
                with st.spinner("AI Agent is classifying & notifying..."):
                    files = {"file": uploaded_file.getvalue()}
                    try:
                        res = requests.post(f"{API_URL}/analyze", files={"file": uploaded_file})
                        if res.status_code == 200:
                            data = res.json()
                            st.success(f"✅ Processed {data['total_new_complaints']} records!")
                            st.session_state.latest_data = data['sample_output']

                            import time
                            time.sleep(1.5) # Wait so user sees the "Success" message
                            st.rerun()
                        
                        else:
                            st.error(f"Error: {res.text}")
                    except Exception as e:
                        st.error(f"Connection failed: {e}")

        with col_preview:
            st.subheader("📋 Recent Analysis Preview")
            if "latest_data" in st.session_state:
                df_preview = pd.DataFrame(st.session_state.latest_data)
                # Apply Pandas Styling for Visual Pop
                st.dataframe(
                    df_preview[['category', 'priority', 'sentiment']].style.map(highlight_critical, subset=['priority']),
                    use_container_width=True
                )
            else:
                st.caption("No recent uploads. Upload a file to see preview.")

    # --- 2. ANALYTICS & REPORTS TAB ---
    elif menu == "Analytics & Reports":
        st.title("📈 Intelligence & Reporting")
        
        # Report Button
        c_text, c_btn = st.columns([4, 1])
        with c_text: st.caption("Visualize trends and generate PDF reports for management.")
        with c_btn:
            try:
                report_res = requests.get(f"{API_URL}/generate-report")
                if report_res.status_code == 200:
                    st.download_button("📄 Download PDF Report", report_res.content, "ComplaintIQ_Report.pdf", "application/pdf")
            except: st.warning("Backend offline")

        # Fetch Data
        try:
            res = requests.get(f"{API_URL}/all-complaints")
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                
                # Charts
                tab1, tab2 = st.tabs(["Category Distribution", "Timeline Analysis"])
                
                with tab1:
                    fig = px.pie(df, names='category', title='Complaints by Category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    if 'date_logged' in df.columns:
                        df['date_logged'] = pd.to_datetime(df['date_logged'])
                        daily = df.groupby(df['date_logged'].dt.date).size().reset_index(name='count')
                        fig2 = px.line(daily, x='date_logged', y='count', title='Daily Volume', markers=True)
                        st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No data available for analytics.")
        except Exception as e: st.error(f"Error loading analytics: {e}")

    # --- 3. RESOLUTION CENTER TAB ---
    elif menu == "Resolution Center":
        st.title("🎫 Ticket Resolution")
        st.caption("Update status to 'Resolved' to automatically notify customers via Email.")

        try:
            res = requests.get(f"{API_URL}/all-complaints")
            if res.status_code == 200 and res.json():
                df = pd.DataFrame(res.json())
                
                # Editable Grid
                edited_df = st.data_editor(
                    df,
                    key="ticket_editor",
                    num_rows="fixed",
                    column_config={
                        "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                        "customer_name": st.column_config.TextColumn("Customer", disabled=True),
                        "complaint": st.column_config.TextColumn("Issue", disabled=True, width="large"),
                        "priority": st.column_config.TextColumn("Priority", disabled=True),
                        "status": st.column_config.SelectboxColumn("Status", options=["Open", "In Progress", "Resolved", "Escalated"], required=True),
                        "action": st.column_config.TextColumn("Agent Notes", width="medium")
                    },
                    hide_index=True,
                    use_container_width=True
                )

                if st.button("💾 Save & Notify Customers", type="primary"):
                    # (Same robust save logic as before)
                    progress = st.progress(0)
                    updates = 0
                    orig_dict = df.set_index("id")[["status", "action"]].to_dict(orient="index")
                    
                    for idx, row in edited_df.iterrows():
                        curr_id = int(row["id"])
                        if curr_id in orig_dict:
                            orig_stat = orig_dict[curr_id]["status"]
                            orig_act = orig_dict[curr_id]["action"]
                            new_stat = row["status"]
                            new_act = row["action"] if row["action"] else ""
                            
                            if new_stat != orig_stat or new_act != (orig_act if orig_act else ""):
                                payload = {"id": curr_id, "status": new_stat, "action": new_act}
                                requests.post(f"{API_URL}/update-complaint", json=payload)
                                updates += 1
                    
                    progress.progress(100)
                    if updates > 0:
                        st.success(f"✅ Updated {updates} tickets! Emails sent where applicable.")
                        import time
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.info("No changes detected.")
            else:
                st.info("No active tickets found.")
        except Exception as e: st.error(f"Connection Error: {e}")

    # --- 4. AI CHAT TAB ---
    elif menu == "AI Assistant":
        st.title("🤖 ComplaintIQ Assistant")
        st.caption("Ask questions like 'Show me all Fraud cases' or 'Who is Rudresh Gawas?'")

        for msg in st.session_state.messages:
            avatar = "👤" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Query your banking database..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🤖"):
                try:
                    # 1. Get the FULL response (Text + Data)
                    res = requests.post(f"{API_URL}/chat", params={"query": prompt})
                    full_response = res.json() 
                    
                    # 2. Extract the Text Message
                    bot_reply = full_response.get("response", "Error processing request.")
                    
                    # 3. Display the Text
                    st.markdown(bot_reply)
                    
                    # 4. Display the Data Table (If it exists)
                    if "data" in full_response:
                        df_result = pd.DataFrame(full_response["data"])
                        st.dataframe(df_result, use_container_width=True)
                    
                    # 5. Save ONLY the text to chat history (to keep history clean)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")

    # --- 5. SETTINGS TAB ---
    elif menu == "Settings":
        st.title("⚙️ Admin Settings")
        
        st.subheader("🧠 Teach AI New Keywords")
        with st.form("keyword_form"):
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Category", ["Fraud", "Loan", "Credit Card", "Account"])
            word = c2.text_input("New Keyword")
            if st.form_submit_button("Add to Knowledge Base"):
                requests.post(f"{API_URL}/add-keyword", json={"category": cat, "word": word})
                st.success(f"AI updated with '{word}'")
                st.rerun()

        st.markdown("---")
        st.subheader("Existing Keywords")
        try:
            kw = requests.get(f"{API_URL}/keywords").json()
            for k, v in kw.items():
                with st.expander(f"{k} ({len(v)})"):
                    st.write(", ".join([f"`{x}`" for x in v]))
        except: st.error("Database offline")

# -------------------------
# ROUTER
# -------------------------
if st.session_state.authenticated:
    show_dashboard()
else:
    show_login_page()