
import os
import requests
from flask import Flask, request, jsonify

# Initialize Flask app
app = Flask(__name__)

# WhatsApp API Credentials (Replace with your actual credentials)
ACCESS_TOKEN = "EAATESj1oB5YBOwnit7onxGWo6lUXDXaREKyqno9FpMy3PUUn4beHGP7r0TklXJZCnkA77Ax7RhfYp2bNwCKvUQ5ZBVGmT8pEFBZCb7nDTIfP8FGZA6OokiN2FNyJc2OemaZAb5OzklcGsdnSJamHJqB6VTneLGPKbywUNfhUbKrilSHZAMMt4L83BlQwFKHRE9P8EPZAk2ZBrxpCbmr1VjQ7KqCjnQwZD"
PHONE_NUMBER_ID = "618334968023252"
VERIFY_TOKEN = "1412803596375322"
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

def send_whatsapp_message(to, text, buttons=None):
    """Function to send a WhatsApp message using Meta API, with optional buttons."""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # If buttons are provided, send an interactive message
    if buttons:
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {
                    "buttons": buttons
                }
            }
        }
    else:
        # Send a normal text message
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
    
    # Debugging logs
    print("✅ Sending message to:", to)
    print("📩 Message body:", text)
    print("📡 WhatsApp API Response Status:", response.status_code)

    try:
        response_json = response.json()
        print("📝 WhatsApp API Response Data:", response_json)
    except Exception as e:
        print("❌ Error parsing response JSON:", e)

    return response.json()

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """Webhook for receiving WhatsApp messages"""
    if request.method == "GET":
        # Webhook verification
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification failed", 403

    if request.method == "POST":
        data = request.get_json()
        
        # Debugging print
        print("📥 Incoming Webhook Data:", data)

        if data and "entry" in data:
            for entry in data["entry"]:
                for change in entry["changes"]:
                    if "messages" in change["value"]:
                        for message in change["value"]["messages"]:
                            sender_id = message["from"]
                            text = message.get("text", {}).get("body", "").lower()

                            # Debugging log
                            print(f"📨 Received message from {sender_id}: {text}")

                            # Simple chatbot response logic
                            if "hello" in text:
                                buttons = [
                                    {"type": "reply", "reply": {"id": "Apply", "title": "Apply Leave"}},
                                    {"type": "reply", "reply": {"id": "Track", "title": "Track Days"}},
                                    {"type": "reply", "reply": {"id": "Check", "title": "Check Balance"}}
                                ]
                                send_whatsapp_message(sender_id, "Hello! How can I assist you?", buttons)
                            else:
                                send_whatsapp_message(sender_id, "I'm a bot. Say 'hello' to start!")

        return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    print("🚀 WhatsApp Chatbot is running on port 5000...")
    app.run(port=5000, debug=True)