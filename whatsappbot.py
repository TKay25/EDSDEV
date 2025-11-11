from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route('/whatsapp_webhook', methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.form.get('Body').strip()  # Get the message text
    sender = request.form.get('From')  # Get the sender's number

    print(f"Message from {sender}: {incoming_msg}")

    # Create a response object
    resp = MessagingResponse()
    
    if incoming_msg.lower() == "hi":
        reply = "Hello! Choose an option:\n1️⃣ Apply Leave\n2️⃣ Check Balance"
        resp.message(reply)
    elif incoming_msg == "1":
        resp.message("Enter your start date for leave (eg 12 Feb 2025):")
    elif incoming_msg == "2":
        resp.message("Your leave balance is 10 days.")
    else:
        resp.message("Sorry, I didn't understand that. Reply with 1 or 2.")

    return Response(str(resp), mimetype="application/xml")

if __name__ == '__main__':
    app.run(debug=False, port=5000)

