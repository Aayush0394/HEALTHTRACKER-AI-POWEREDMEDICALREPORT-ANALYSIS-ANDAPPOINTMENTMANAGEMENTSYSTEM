import os
from pymongo import MongoClient

# --- MongoDB Connection ---
uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(uri)
db = client["Health_status_shower"]

def get_patient_appointments(patient_id):
    """
    Fetch all appointments for a given patient_id.
    Returns a list of dictionaries.
    """
    appointment_col = db["Appointment"]
    appointments_cursor = appointment_col.find({"Patient_id": patient_id})

    appointments = []
    for appt in appointments_cursor:
        appointments.append({

            "doctor_name": appt.get("Doctor_name", "Unknown"),

            "date": appt.get("Date", "N/A"),
            "time_slot": appt.get("Slot", "N/A")   # ✅ use correct field
        })

    return appointments
