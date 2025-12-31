import re
from nltk.sentiment import SentimentIntensityAnalyzer

class ComplaintAnalyzer:
    def __init__(self, keywords_dict=None):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # If keywords are provided (from DB), use them. Otherwise, use defaults.
        if keywords_dict:
            self.categories = keywords_dict
        else:
            self.categories = {
                "Loan": ["loan", "emi", "interest", "repayment"],
                "Credit Card": ["card", "credit", "debit", "limit"],
                "Account": ["account", "balance", "statement", "transfer"],
                "Fraud": ["fraud", "scam", "unauthorized", "hack"],
                "Customer Service": ["service", "support", "response", "delay"]
            }

    def update_keywords(self, new_keywords):
        """Updates the internal keyword list dynamically from the database."""
        self.categories = new_keywords
        print("✅ ComplaintAnalyzer keywords updated.")

    def clean_text(self, text):
        text = text.lower()
        # FIXED: Now allows numbers (0-9) so amounts like "5000 rs" are kept
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        return text

    def analyze(self, complaint):
        cleaned = self.clean_text(complaint)

        category = "General"
        # Dynamic category matching
        for c, words in self.categories.items():
            if any(w in cleaned for w in words):
                category = c
                break

        sentiment_score = self.sentiment_analyzer.polarity_scores(cleaned)['compound']
        sentiment = "Positive" if sentiment_score >= 0.05 else "Negative" if sentiment_score <= -0.05 else "Neutral"

        urgency = "Low"
        # Check for urgent keywords (You could also make this dynamic later if you wanted!)
        if any(w in cleaned for w in ["fraud", "scam", "unauthorized", "blocked", "urgent", "hacked"]):
            urgency = "High"
        elif any(w in cleaned for w in ["delay", "issue", "pending", "failed"]):
            urgency = "Medium"

        # Prioritization Logic
        if category == "Fraud" or urgency == "High":
            priority = "P1 - Critical"
            action = "Immediate escalation to fraud/security team"
        elif sentiment == "Negative" and urgency == "Medium":
            priority = "P2 - High"
            action = "Assign to senior customer support team"
        elif sentiment == "Neutral":
            priority = "P3 - Medium"
            action = "Standard support handling"
        else:
            priority = "P4 - Low"
            action = "Auto-response or FAQ handling"

        return {
            "complaint": complaint,
            "category": category,
            "sentiment": sentiment,
            "urgency": urgency,
            "priority": priority,
            "action": action
        }