import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configured via environment variables for security
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "MY_SECURE_VERIFY_TOKEN_123")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "YOUR_META_PAGE_ACCESS_TOKEN")

# Add your target keywords (case-insensitive)
KEYWORDS = ["link", "price", "info", "details", "dm", "buy"]

@app.route("/", methods=["GET"])
def home():
    return "Bot is running online!", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Handshake verification required by Meta Developer Portal."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return challenge, 200
    return "Verification token mismatch", 403

@app.route("/webhook", methods=["POST"])
def handle_comments():
    """Receives Instagram reel comments in real-time."""
    data = request.json
    
    try:
        entries = data.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                comment_text = value.get("text", "")
                comment_id = value.get("id")
                user_id = value.get("from", {}).get("id")

                # Keyword detection (Word boundary check)
                if comment_text and is_keyword_matched(comment_text):
                    print(f"Match found! Comment: '{comment_text}'")
                    send_private_dm(comment_id)

    except Exception as e:
        print(f"Error handling webhook payload: {e}")
        
    return jsonify({"status": "received"}), 200

def is_keyword_matched(text):
    for kw in KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
            return True
    return False

def send_private_dm(comment_id):
    """Sends a private message trigger using Meta Graph API v19.0."""
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"comment_id": comment_id},
        "message": {"text": "Hey there! Thanks for reaching out. Here is the link you requested: https://yourwebsite.com"}
    }
    
    response = requests.post(url, json=payload)
    print("Graph API Response:", response.status_code, response.json())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)