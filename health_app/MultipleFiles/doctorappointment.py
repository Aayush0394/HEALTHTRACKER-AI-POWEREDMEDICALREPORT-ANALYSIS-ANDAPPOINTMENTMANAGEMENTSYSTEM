import os
from pymongo import MongoClient
from datetime import datetime
import re

# MongoDB connection
uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(uri)

db = client["Health_status_shower"]
collection = db["Doctor"]

def existing_user(email):
    email = email.strip()
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        raise ValueError("📧 Invalid email format. Use something like user@example.com")

    existing = collection.find_one({'email': email})
    if existing:
        doctor_id = str(existing["doctor_id"])
        return doctor_id
    else:
        return None

def get_appointments(D_id, choice):
    if not D_id:
        return {"error": "Doctor ID not found."}

    appointment_col = db["Appointment"]
    today = datetime.today().strftime("%Y-%m-%d")

    if choice == "1":
        appointments = list(appointment_col.find({"Doctor_id": D_id, "Date": today}))
        label = f"Appointments for today ({today})"
    elif choice == "2":
        appointments = list(appointment_col.find({"Doctor_id": D_id, "Date": {"$gt": today}}))
        label = "Upcoming appointments"
    else:
        return {"error": "❌ Invalid choice"}

    if not appointments:
        return {"message": "⚠️ No appointments found."}

    return {"label": label, "appointments": appointments}
