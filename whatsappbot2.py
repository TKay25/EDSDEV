
import os
import requests
from flask import Flask, request, jsonify
import json
from datetime import datetime
import psycopg2


# Initialize Flask app
app = Flask(__name__)

external_database_url = "postgresql://lmsdatabase_8ag3_user:6WD9lOnHkiU7utlUUjT88m4XgEYQMTLb@dpg-ctp9h0aj1k6c739h9di0-a.oregon-postgres.render.com/lmsdatabase_8ag3"
database = 'lmsdatabase_8ag3'

connection = psycopg2.connect(external_database_url)

cursor = connection.cursor()

# WhatsApp API Credentials (Replace with your actual credentials)
ACCESS_TOKEN = "EAATESj1oB5YBO46tPvKRqI3J1RdVWw7OIE8vA1wZBsbmIj4acTsOoGTPFHE5cSXhb3kquNLRurDefU1IMrxkBsrSLf8VIaEB66sFo5N01vH14ZAlsEc3EeqhZBJ2yRaxMZBT2rQQ24RbOZAm0MgS2D2WesxLDTcvyiqKUNxLMzuQHysklBOEZCSZBVCtSIe5YZBmxnb2Vbtomc9RlqZCLPjiHAwZB1wncR"
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
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification failed", 403

    if request.method == "POST":
        data = request.get_json()
        print("📥 Full incoming data:", json.dumps(data, indent=2))  # Debug raw data

        if data and "entry" in data:
            for entry in data["entry"]:
                for change in entry["changes"]:
                    if "messages" in change["value"]:
                        for message in change["value"]["messages"]:
                            sender_id = message["from"]
                            
                            sender_number = sender_id[-9:]  # Takes last 9 characters (e.g., "12345678")
                            print(sender_number)
                            print(f"📱 Sender's WhatsApp number: {sender_number}")  # Debug log

                            query = f"SELECT id, firstname, surname, whatsapp, leaveapprovername FROM {table_name};"
                            cursor.execute(query)
                            rows = cursor.fetchall()

                            df_employees = pd.DataFrame(rows, columns=["id","firstname", "surname", "whatsapp","Email", "Address", "Role","Leave Approver Name","Leave Approver ID","Leave Approver Email", "Leave Approver WhatsAapp", "Leave Days Balance","Days Accumulated per Month"])
                            print(df_employees)
                            userdf = df_employees[df_employees['id'] == sender_number].reset_index()
                            print("yeaarrrrr")
                            print(userdf)

                            # 1. FIRST check for button clicks
                            if message.get("type") == "interactive":
                                interactive = message.get("interactive", {})
                                if interactive.get("type") == "button_reply":
                                    button_id = interactive.get("button_reply", {}).get("id")
                                    print(f"🔘 Button clicked: {button_id}")
                                    
                                    if button_id == "Apply":
                                        send_whatsapp_message(
                                            sender_id, 
                                            "Ok. When would you like your leave to start?\n"
                                            "Please enter your response using the format: 👇🏻\n"
                                            "`start 24 january 2025`"
                                        )
                                        continue

                            # 2. THEN check for regular text messages
                            text = message.get("text", {}).get("body", "").lower()
                            print(f"📨 Message from {sender_id}: {text}")
                            
                            if "hello" in text.lower():
                                buttons = [
                                    {"type": "reply", "reply": {"id": "Apply", "title": "Apply Leave"}},
                                    {"type": "reply", "reply": {"id": "Track", "title": "Track Application"}},
                                    {"type": "reply", "reply": {"id": "Check", "title": "Check Balance"}}
                                ]
                                send_whatsapp_message(
                                    sender_id, 
                                    "Hello! Echelon Bot Here 😎. How can I assist you?", 
                                    buttons
                                )

                            elif "apply leave" in text.lower():
                                send_whatsapp_message(
                                    sender_id, 
                                    "Ok. When would you like your leave to start?\n\n"
                                    "Please enter your response using the format: 👇🏻\n"
                                    "`start 24 january 2025`"
                                )

                            elif "start" in text.lower():
                                # Extract the date part after "start"
                                date_part = text.split("start", 1)[1].strip()
                                
                                # Try to parse the date
                                try:
                                    parsed_date = datetime.strptime(date_part, "%d %B %Y")
                                    # If successful, respond with "yes"
                                    send_whatsapp_message(sender_id, "✅ Yes! Valid start date format.\n\n"
                                        "Now Enter the last day that you will be on leave.Use the format: 👇🏻\n"
                                        "`end 24 january 2025`"                      
                                                          )
                                    
                                    # Here you would typically store the date and continue the leave application process
                                except ValueError:
                                    # If parsing fails, respond with "no" and show correct format
                                    send_whatsapp_message(
                                        sender_id,
                                        "❌ No, incorrect message format. Please use:\n"
                                        "`start 24 january 2025`\n"
                                        "Example: `start 15 march 2024`"
                                    )

                            elif "end" in text.lower():
                                # Extract the date part after "start"
                                date_part = text.split("end", 1)[1].strip()
                                
                                # Try to parse the date
                                try:
                                    parsed_date = datetime.strptime(date_part, "%d %B %Y")
                                    # If successful, respond with "yes"
                                    send_whatsapp_message(sender_id, "✅ Leave Application Successful!\n\n"
                                        "To Check the status of you leave application, Type Hello.")
                                    # Here you would typically store the date and continue the leave application process
                                except ValueError:
                                    # If parsing fails, respond with "no" and show correct format
                                    send_whatsapp_message(
                                        sender_id,
                                        "❌ No, incorrect message format. Please use:\n"
                                        "`end 24 january 2025`\n"
                                        "Example: `end 15 march 2024`"
                                    )

                            else:
                                send_whatsapp_message(
                                    sender_id, 
                                    "Echelon Bot Here 😎. Say 'hello' to start!"
                                )

        return jsonify({"status": "received"}), 200
    

if __name__ == "__main__":
    print("🚀 WhatsApp Chatbot is running on port 5000...")
    app.run(port=5000, debug=True)