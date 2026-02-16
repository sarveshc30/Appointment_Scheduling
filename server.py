from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, template_folder=".")

# Initialize Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Email configuration
email_sender: str = os.environ.get("EMAIL")
email_password: str = os.environ.get("SMTP_GMAIL_PASSWORD")


# ----------------------------
# Email Sending Function
# ----------------------------
def send_email(recipient_email, subject, body):
    """Send email using Gmail SMTP SSL"""
    try:
        msg = EmailMessage()
        msg["From"] = email_sender
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_sender, email_password)
            server.send_message(msg)

        print("Email sent successfully.")
        return True

    except Exception as e:
        print(f"Email failed: {e}")
        return False


# ----------------------------
# Routes
# ----------------------------
@app.route("/", methods=["GET"])
def index():
    """Serve the appointment booking form"""
    return render_template("website.html")


@app.route("/book-appointment", methods=["POST"])
def book_appointment():
    """Handle appointment booking"""
    try:
        data = request.get_json()
        name = data.get("name")
        email_address = data.get("email")
        date = data.get("date")
        time = data.get("time")

        # Validate input
        if not all([name, email_address, date, time]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Combine date and time
        appointment_datetime = f"{date} {time}"

        # Check availability
        check_response = (
            supabase.table("Appointment_Data")
            .select("*")
            .eq("appointment_datetime", appointment_datetime)
            .execute()
        )

        if check_response.data:
            return jsonify({"status": "unavailable"}), 200

        # Insert appointment
        supabase.table("Appointment_Data").insert({
            "appointment_datetime": appointment_datetime,
            "Name": name,
            "email": email_address
        }).execute()

        # Send confirmation email
        confirmation_body = f"""
Dear {name},

Your appointment has been booked successfully!

Date: {date}
Time: {time}

Thank you!
"""

        send_email(email_address, "Appointment Confirmation", confirmation_body)

        return jsonify({"status": "success"}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------------------
# Run Server (Render Compatible)
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
