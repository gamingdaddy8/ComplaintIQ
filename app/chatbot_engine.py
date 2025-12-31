import pandas as pd

class ChatbotEngine:
    def __init__(self, df, keywords_dict):
        self.df = df
        self.keywords = keywords_dict

    def respond(self, query):
        """
        Smart Brain: Decides if the user wants a Summary, a Search, or Advice.
        """
        query = query.lower().strip()
        
        if self.df.empty:
            return "I have no data to analyze yet. Please upload a file."

        # --- SKILL 1: THE ANALYST (Summaries & Stats) ---
        if any(x in query for x in ["summary", "overview", "stats", "report"]):
            return self.generate_summary()
        
        if "how many" in query or "total" in query:
            return self.generate_count_response(query)

        # --- SKILL 2: THE PRIORITY CHECKER (New!) ---
        # Handles: "show critical", "give me critical cases", "high priority"
        if any(x in query for x in ["critical", "urgent", "high priority", "p1"]):
            return self.search_by_priority()

        # --- SKILL 3: THE INVESTIGATOR (Specific Lookup) ---
        
        # 1. Look for Account Number (Digits > 4)
        words = query.split()
        for word in words:
            clean_word = word.replace('?', '').replace('#', '')
            if clean_word.isdigit() and len(clean_word) > 4:
                return self.search_by_account(clean_word)

        # 2. Look for Customer Name
        search_df = self.df.copy()
        if 'customer_name' in search_df.columns:
            search_df['customer_name'] = search_df['customer_name'].fillna("Unknown").astype(str)
            for name in search_df['customer_name']:
                if len(name) > 3 and name.lower() in query:
                    return self.search_by_name(name)

        # 3. Look for Keywords (Fraud, Loan, etc.)
        for category, words_list in self.keywords.items():
            for word in words_list:
                if word in query:
                    return self.search_by_category(category, word)

        # --- SKILL 4: FALLBACK ---
        return "I can help! You can ask for a **'Summary'**, **'Critical cases'**, search for a **Name** (e.g., 'Rudresh'), or specific issues like **'Fraud'**."

    # ---------------------------------------------------------
    # INTERNAL HELPER FUNCTIONS
    # ---------------------------------------------------------

    def generate_summary(self):
        total = len(self.df)
        if 'category' in self.df.columns:
            top_cat = self.df['category'].mode()[0]
            cat_count = len(self.df[self.df['category'] == top_cat])
        else:
            top_cat = "General"
            cat_count = 0
            
        critical_count = len(self.df[self.df['priority'] == 'P1 - Critical']) if 'priority' in self.df.columns else 0
        
        return (
            f"Here is the current situation summary:\n\n"
            f"**Total Complaints:** {total}\n"
            f"**Top Issue:** '{top_cat}' with {cat_count} cases.\n"
            f"**Critical Attention Needed:** {critical_count} cases require immediate action.\n\n"
            f"Would you like to see the 'Critical' cases?"
        )

    def generate_count_response(self, query):
        for category in self.keywords.keys():
            if category.lower() in query:
                count = len(self.df[self.df['category'] == category])
                return f"There are **{count}** complaints related to **{category}**."
        return f"I have a total of **{len(self.df)}** complaints in the system."

    def search_by_priority(self):
        """New function to handle 'Critical' queries."""
        if 'priority' not in self.df.columns:
            return "I cannot check priority because the 'priority' column is missing."
            
        # Filter for Critical cases
        matches = self.df[self.df['priority'] == 'P1 - Critical']
        
        if not matches.empty:
            return {
                "response": f"🚨 I found **{len(matches)} Critical (P1)** cases that need immediate attention:",
                "data": matches.to_dict(orient="records")
            }
        else:
            return "Good news! There are currently **0 Critical** cases in the system."

    def search_by_account(self, acc_num):
        search_df = self.df.copy()
        if 'account_number' in search_df.columns:
            search_df['account_number'] = search_df['account_number'].fillna("0").astype(str).str.replace(".0", "", regex=False)
            match = self.df[search_df['account_number'] == acc_num]
            
            if not match.empty:
                return {
                    "response": f"✅ Found **{len(match)}** record(s) for Account **#{acc_num}**:",
                    "data": match.to_dict(orient="records")
                }
        return f"I checked the database, but I couldn't find Account #{acc_num}."

    def search_by_name(self, name):
        match = self.df[self.df['customer_name'].astype(str).str.lower() == name.lower()]
        return {
            "response": f"👤 Found **{len(match)}** complaint(s) from **{name}**:",
            "data": match.to_dict(orient="records")
        }

    def search_by_category(self, category, keyword):
        matches = self.df[self.df['category'] == category]
        if not matches.empty:
            return {
                "response": f"📂 I found **{len(matches)}** cases related to **{category}** (keyword matched: '{keyword}'):",
                "data": matches.to_dict(orient="records")
            }
        return f"I understood you are looking for '{category}', but there are no open complaints in that category right now."