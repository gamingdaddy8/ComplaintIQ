import re
from difflib import get_close_matches

class ChatbotEngine:
    def __init__(self, results_df):
        self.results_df = results_df

        self.intent_synonyms = {
            "critical": ["critical", "urgent", "serious", "important", "high priority"],
            "fraud": ["fraud", "scam", "unauthorized", "hacked"],
            "summary": ["summary", "overview", "report", "insights"],
            "count": ["count", "how many", "number", "total"]
        }

    def normalize(self, text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        return text

    def match_intent(self, query, keywords):
        for word in keywords:
            if word in query:
                return True
            if get_close_matches(word, query.split(), cutoff=0.75):
                return True
        return False

    def respond(self, user_query):
        query = self.normalize(user_query)

        if self.match_intent(query, self.intent_synonyms["critical"]):
            return self.results_df[self.results_df["priority"] == "P1 - Critical"]

        elif self.match_intent(query, self.intent_synonyms["fraud"]):
            return self.results_df[self.results_df["category"] == "Fraud"]

        elif self.match_intent(query, self.intent_synonyms["count"]):
            return self.results_df["priority"].value_counts()

        elif self.match_intent(query, self.intent_synonyms["summary"]):
            return self.results_df.groupby("category").size()

        else:
            return "Sorry, I couldn't understand the request."
