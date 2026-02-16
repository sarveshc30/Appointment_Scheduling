from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from datetime import datetime, timedelta
import smtplib
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

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

def send_email(recipient_email, subject, body):
    """Send email using SMTP"""
    try:
        connection = smtplib.SMTP("smtp.gmail.com")
        connection.starttls()
        connection.login(user=email_sender, password=email_password)
        message = f"Subject: {subject}\n\n{body}"
        connection.sendmail(from_addr=email_sender, to_addrs=recipient_email, msg=message)
        connection.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_reminders():
    """Send reminder emails for appointments tomorrow"""
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
            email_address = appointment.get("email")
            appointment_time = appointment.get("appointment_datetime")
            
            body = f"Dear {name},\n\nThis is a reminder for your appointment scheduled on {appointment_time}.\n\nBest regards,\nYour Company"
            send_email(email_address, "Appointment Reminder", body)

    except Exception as e:
        print(f"An error occurred while fetching appointments: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Schedule send_reminders() to run daily at 1:27 PM
scheduler.add_job(send_reminders, 'cron', hour=13, minute=30, id='send_reminders_job')

# Shut down scheduler when Flask exits
atexit.register(lambda: scheduler.shutdown())

@app.route("/", methods=["GET"])
def index():
    """Serve the appointment booking form"""
    return render_template("website.html")

@app.route("/book-appointment", methods=["POST"])
def book_appointment():
    """Handle appointment booking from the form"""
    try:
        data = request.get_json()
        name = data.get("name")
        email_address = data.get("email")
        date = data.get("date")
        time = data.get("time")

        # Validate input
        if not all([name, email_address, date, time]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Combine date and time into a single datetime string
        appointment_datetime = f"{date} {time}"

        # Check availability (if slot already booked)
        try:
            check_response = (
                supabase.table("Appointment_Data")
                .select("*")
                .eq("appointment_datetime", appointment_datetime)
                .execute()
            )

            if check_response.data:
                return jsonify({"status": "unavailable", "message": "Slot already booked"}), 200
        except Exception as e:
            print(f"Error checking availability: {e}")

        # Insert new appointment
        try:
            insert_response = (
                supabase.table("Appointment_Data")
                .insert({
                    "appointment_datetime": appointment_datetime,
                    "Name": name,
                    "email": email_address
                })
                .execute()
            )

            # Send confirmation email
            confirmation_body = f"Dear {name},\n\nYour appointment has been booked successfully!\n\nDate: {date}\nTime: {time}\n\nThank you!"
            send_email(email_address, "Appointment Confirmation", confirmation_body)

            return jsonify({"status": "success", "message": "Appointment booked successfully"}), 201

        except Exception as e:
            print(f"Error inserting appointment: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    try:
        print("Starting Flask server with scheduled daily reminders at 1:27 PM...")
        app.run(debug=True, host="0.0.0.0", port=5000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
