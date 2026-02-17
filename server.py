from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from datetime import datetime, timedelta
from twilio.rest import Client as TwilioClient
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

load_dotenv()

# ----------------------------
# Flask App
# ----------------------------
app = Flask(__name__, template_folder=".")

# ----------------------------
# Supabase Setup
# ----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------
# Twilio Setup
# ----------------------------
ACCOUNT_SID = os.environ.get("account_sid")
AUTH_TOKEN = os.environ.get("auth_token")

twilio_client = TwilioClient(ACCOUNT_SID, AUTH_TOKEN)

TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio Sandbox


# ----------------------------
# Phone Number Normalizer
# ----------------------------
def normalize_phone_number(phone):
    """
    Ensures phone number is in international format.
    Defaults to +91 if country code is missing.
    """

    # Remove spaces, dashes
    phone = phone.replace(" ", "").replace("-", "")

    # If already in international format
    if phone.startswith("+"):
        return phone

    # If starts with 91 and length is 12 (e.g., 919876543210)
    if phone.startswith("91") and len(phone) == 12:
        return f"+{phone}"

    # If 10-digit Indian number
    if len(phone) == 10:
        return f"+91{phone}"

    # Fallback — return as is (Twilio will reject invalid)
    return phone


# ----------------------------
# WhatsApp Send Function
# ----------------------------
def send_whatsapp(phone_number, message_body):
    try:
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=f"whatsapp:{phone_number}"
        )
        print("Twilio Message SID:", message.sid)
        return True
    except Exception as e:
        print("Twilio Error:", str(e))
        return False


# ----------------------------
# Reminder Scheduler Function
# ----------------------------
def send_reminders():
    tomorrow = datetime.now() + timedelta(days=1)
    start_of_tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_day_after = start_of_tomorrow + timedelta(days=1)

    try:
        response = (
            supabase.table("Appointment_Data")
            .select("*")
            .gte("appointment_datetime", start_of_tomorrow.strftime("%Y-%m-%d %H:%M:%S"))
            .lt("appointment_datetime", start_of_day_after.strftime("%Y-%m-%d %H:%M:%S"))
            .execute()
        )

        appointments = response.data
        print(f"Found {len(appointments)} appointments for tomorrow.")

        for appointment in appointments:
            name = appointment.get("Name")
            phone = appointment.get("phone")
            appointment_time = appointment.get("appointment_datetime")

            reminder_message = f"""
Hello {name},

Reminder: You have an appointment tomorrow.

Date & Time: {appointment_time}

Please be on time.
"""

            send_whatsapp(phone, reminder_message)

    except Exception as e:
        print("Reminder Error:", str(e))


# ----------------------------
# Scheduler Setup
# ----------------------------
scheduler = BackgroundScheduler()
scheduler.start()

scheduler.add_job(send_reminders, 'cron', hour=12, minute=35, id='send_reminders_job')

atexit.register(lambda: scheduler.shutdown())


# ----------------------------
# Routes
# ----------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("website.html")


@app.route("/book-appointment", methods=["POST"])
def book_appointment():
    try:
        data = request.get_json()

        name = data.get("name")
        phone = normalize_phone_number(data.get("phone"))
        date = data.get("date")
        time = data.get("time")

        if not all([name, phone, date, time]):
            return jsonify({"status": "error"}), 400

        appointment_datetime = f"{date} {time}"

        # Check slot availability
        check_response = (
            supabase.table("Appointment_Data")
            .select("*")
            .eq("appointment_datetime", appointment_datetime)
            .execute()
        )

        if check_response.data:
            return jsonify({"status": "unavailable"}), 200

        # Insert new appointment
        supabase.table("Appointment_Data").insert({
            "appointment_datetime": appointment_datetime,
            "Name": name,
            "phone": phone
        }).execute()

        # Send Confirmation via WhatsApp
        confirmation_message = f"""
Hello {name},

Your appointment is confirmed ✅

Date: {date}
Time: {time}

Thank you!
"""

        send_whatsapp(phone, confirmation_message)

        return jsonify({"status": "success"}), 201

    except Exception as e:
        print("Booking Error:", str(e))
        return jsonify({"status": "error"}), 500


# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Starting Flask with Twilio messaging...")
    app.run(host="0.0.0.0", port=port, debug=False)
