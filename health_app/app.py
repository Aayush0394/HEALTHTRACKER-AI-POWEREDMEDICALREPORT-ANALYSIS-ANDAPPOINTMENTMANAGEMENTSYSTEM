import os
from dotenv import load_dotenv

# Load the project-root .env BEFORE importing modules that create MongoDB clients.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from MultipleFiles import Appointment, Report_mode, user_login, Showappointment
import doctorappointment  # Imported for managing Doctor workspace logic
import admin_management   # For matching verification with standard equality ==
import re

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this-secret")

# Upload folder configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# RAG runs as a separate Streamlit service (default local URL: http://localhost:8501).
@app.context_processor
def inject_rag_app_url():
    return {"rag_app_url": os.getenv("RAG_APP_URL", "http://localhost:8501")}


# ====================== ROUTES ======================

@app.route('/')
def index():
    # Route interceptor prioritizing roles dynamically
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    elif 'doctor' in session:
        return redirect(url_for('doctor_dashboard'))
    elif 'customer' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# ---------------- PATIENT-ONLY EXCLUSIVE PORTAL ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    if 'doctor' in session:
        return redirect(url_for('doctor_dashboard'))
    if 'customer' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email'].strip()

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash("❌ Invalid email format.", 'error')
            return render_template('login.html', active_panel='login')

        from pymongo import MongoClient
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        client = MongoClient(uri)
        db = client["Health_status_shower"]
        customer_collection = db["Customer"]

        customer = customer_collection.find_one({"email": email})

        if customer:
            session['customer'] = {
                'Patient_id': customer['Patient_id'],
                'Name': customer['Name'],
                'email': customer['email']
            }
            flash(f"✅ Welcome back, {customer['Name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash("❌ No account found with that email. Let's create one!", 'error')
            return render_template('login.html', active_panel='register', email_prefill=email)

    return render_template('login.html', active_panel='login')


# =========================================================================
# ======================== ADMIN ACCOUNT MANAGEMENT =======================
# =========================================================================

# ----------------- ADMIN REGISTER -----------------
@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        master_key = request.form['master_key']

        try:
            admin_management.register_admin(email, name, master_key)
            flash("✅ Admin registration successful! Please log in.", "success")
            return redirect(url_for('admin_login'))
        except ValueError as e:
            flash(str(e), "error")
            return render_template('admin_register.html')

    return render_template('admin_register.html')


# ----------------- ADMIN LOGIN -----------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        master_key = request.form['master_key']

        admin = admin_management.verify_admin_login(email, master_key)
        if admin:
            session['admin'] = {
                'email': admin['email'],
                'name': admin['name']
            }
            flash(f"💻 Welcome Admin {admin['name']}!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("❌ Invalid Email or incorrect Master Key.", "error")
            return render_template('admin_login.html')

    return render_template('admin_login.html')


# ----------------- ADMIN LOGOUT WORKFLOW -----------------
@app.route('/admin/logout')
def admin_logout():
    """Clears administrative credential variables from current user active session."""
    session.pop('admin', None)
    flash("🔓 Signed out successfully. Secure context ended.", "success")
    return redirect(url_for('admin_login'))


# =========================================================================
# ========================= ADMIN CONTROL DASHBOARD =======================
# =========================================================================

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    # Session Gatekeeping Layer
    if 'admin' not in session:
        flash("🔒 Admin access required.", "warning")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        action = request.form.get('action')

        # --- 1. DOCTOR ACTION WORKFLOWS ---
        if action == 'add_doctor':
            doc_name = request.form['doc_name']
            doc_email = request.form['doc_email']
            spec = request.form['specialization']
            avail = request.form['availability']
            doc_phone = request.form['doc_phone']
            chosen_slots = request.form.getlist('slots')

            try:
                admin_management.add_new_doctor(doc_name, doc_email, spec, avail, doc_phone, chosen_slots)
                flash(f"🩺 Dr. {doc_name} successfully onboarded into active registry!", "success")
            except ValueError as e:
                flash(str(e), "error")

        elif action == 'edit_doctor':
            doc_id = request.form['doctor_id']
            doc_name = request.form['doc_name']
            doc_email = request.form['doc_email']
            spec = request.form['specialization']
            avail = request.form['availability']
            doc_phone = request.form['doc_phone']
            chosen_slots = request.form.getlist('slots')

            if admin_management.update_doctor_profile(doc_id, doc_name, doc_email, spec, avail, doc_phone, chosen_slots):
                flash(f"📝 Profile for Doctor ID {doc_id} successfully updated and synced!", "success")
            else:
                flash("❌ Failed to update doctor profile. Record not found.", "error")

        elif action == 'delete_doctor':
            doc_id = request.form['doctor_id']
            if admin_management.delete_doctor_by_id(doc_id):
                flash(f"🗑️ Doctor profile {doc_id} completely removed from databases.", "success")
            else:
                flash("❌ Critical: Could not purge doctor record.", "error")

        # --- 2. PATIENT ACTION WORKFLOWS ---
        elif action == 'edit_patient':
            pat_id = request.form['patient_id']
            pat_name = request.form['name']
            pat_email = request.form['email']
            pat_phone = request.form['phone']
            pat_age = request.form['age']
            pat_gender = request.form['gender']

            if admin_management.update_patient_profile(pat_id, pat_name, pat_email, pat_phone, pat_age, pat_gender):
                flash("👥 Patient registration file updated successfully.", "success")
            else:
                flash("❌ Failed to update patient file.", "error")

        elif action == 'delete_patient':
            pat_id = request.form['patient_id']
            if admin_management.delete_patient_by_id(pat_id):
                flash("🗑️ Patient document has been cleanly expunged from records.", "success")
            else:
                flash("❌ Error tracking down targeted Patient profile.", "error")

        return redirect(url_for('admin_dashboard'))

    # --- 3. RENDERING DATA RETRIEVAL LAYERS ---
    patients = admin_management.get_all_patients()
    doctors = admin_management.get_all_doctors()

    return render_template(
        'admin_dashboard.html',
        admin=session['admin'],
        patients=patients,
        doctors=doctors
    )
# ---------------- DOCTOR-ONLY EXCLUSIVE REGISTRATIONLESS PORTAL ----------------
@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    if 'customer' in session:
        return redirect(url_for('dashboard'))
    if 'doctor' in session:
        return redirect(url_for('doctor_dashboard'))

    if request.method == 'POST':
        email = request.form['email'].strip()

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash("❌ Invalid email format.", 'error')
            return render_template('doctor_login.html')

        try:
            doctor_id = doctorappointment.existing_user(email)
            if doctor_id:
                session['doctor'] = {
                    'doctor_id': doctor_id,
                    'email': email
                }
                flash("🩺 Doctor authentication verified successfully!", 'success')
                return redirect(url_for('doctor_dashboard'))
            else:
                flash("❌ Authorization Denied. This email is not verified in our internal Doctor registry.", 'error')
                return render_template('doctor_login.html')
        except ValueError as e:
            flash(f"{str(e)}", 'error')
            return render_template('doctor_login.html')

    return render_template('doctor_login.html')


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if 'customer' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email'].strip()
        try:
            name = request.form['name'].strip()
            contact_number = request.form['contact_number'].strip()
            gender = request.form['gender'].strip().upper()
            age = int(request.form['age'].strip())
            pincode = int(request.form['pincode'].strip())

            new_customer_data = user_login.create_new_user_web(
                name, email, contact_number, gender, age, pincode
            )

            session['customer'] = {
                'Patient_id': new_customer_data['Patient_id'],
                'Name': new_customer_data['Name'],
                'email': new_customer_data['email']
            }
            flash("✅ Registration successful!", 'success')
            return redirect(url_for('dashboard'))

        except ValueError as e:
            flash(f"❌ Error: {e}", 'error')
            return render_template('login.html', active_panel='register', email_prefill=email)
        except Exception as e:
            flash(f"❌ Unexpected error: {e}", 'error')
            return render_template('login.html', active_panel='register', email_prefill=email)

    return render_template('login.html', active_panel='register')


@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'doctor' not in session:
        flash("Please log in as a doctor to access this panel.", 'warning')
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor']['doctor_id']

    today_data = doctorappointment.get_appointments(doctor_id, "1")
    upcoming_data = doctorappointment.get_appointments(doctor_id, "2")

    appointments_today = today_data.get('appointments', []) if isinstance(today_data, dict) else []
    appointments_upcoming = upcoming_data.get('appointments', []) if isinstance(upcoming_data, dict) else []

    return render_template('doctor_dashboard.html',
                           email=session['doctor']['email'],
                           appointments_today=appointments_today,
                           appointments_upcoming=appointments_upcoming)


@app.route('/dashboard')
def dashboard():
    if 'customer' not in session:
        flash("Please log in first.", 'warning')
        return redirect(url_for('login'))

    customer_name = session['customer']['Name']
    patient_id = session['customer']['Patient_id']
    appointments = Showappointment.get_patient_appointments(patient_id)

    return render_template('dashboard.html',
                           customer_name=customer_name,
                           appointments=appointments)


@app.route('/report_mode', methods=['GET', 'POST'])
def report_mode():
    if 'customer' not in session:
        flash("Please log in to access reports.", 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'report_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['report_file']
        if file.filename == '' or not file.filename.endswith('.pdf'):
            flash('Please upload a valid PDF file', 'error')
            return redirect(request.url)

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        try:
            report_text = Report_mode.extract_text_from_pdf(filepath)
            extracted_values = Report_mode.extract_medical_values(report_text)
            status_dict = Report_mode.check_health_simple(extracted_values)

            bar_chart = Report_mode.generate_bar_chart(extracted_values, status_dict)
            pie_chart = Report_mode.generate_pie_chart(status_dict)
            ring_charts = Report_mode.generate_ring_charts(extracted_values, status_dict)

            return render_template('report_results.html',
                                   extracted_values=extracted_values,
                                   status_dict=status_dict,
                                   bar_chart=bar_chart,
                                   pie_chart=pie_chart,
                                   ring_charts=ring_charts)
        except Exception as e:
            flash(f"Error processing report: {e}", 'error')
            return redirect(url_for('report_mode'))

    return render_template('report_upload.html')


@app.route('/appointment_booking')
def appointment_booking():
    if 'customer' not in session:
        flash("Please log in to book appointment.", 'warning')
        return redirect(url_for('login'))
    return render_template('appointment_booking.html')


# ====================== APPOINTMENT ENGINE MICRO-APIS ======================

@app.route('/api/specializations')
def api_specializations():
    return jsonify(Appointment.get_specializations_for_web())


@app.route('/api/doctors')
def api_doctors():
    spec = request.args.get('spec')
    if not spec:
        return jsonify([])
    doctors = Appointment.get_doctors_for_web(spec)
    return jsonify([{
        'doctor_id': str(d.get('doctor_id') or d.get('_id')),
        'name': d.get('name'),
        'specialization': d.get('specialization')
    } for d in doctors])


@app.route('/api/dates')
def api_dates():
    doctor_id = request.args.get('doctor_id')
    if not doctor_id:
        return jsonify([])
    for spec in Appointment.get_specializations_for_web():
        doctors = Appointment.get_doctors_for_web(spec)
        for doc in doctors:
            if str(doc.get('doctor_id') or doc.get('_id')) == doctor_id:
                availability_text = doc.get("availability", "")
                return jsonify(Appointment.get_valid_dates_for_doctor(availability_text))
    return jsonify([])


@app.route('/api/slots')
def api_slots():
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')
    if not doctor_id or not date:
        return jsonify([])
    return jsonify(Appointment.get_available_slots_web(doctor_id, date))


@app.route('/confirm_appointment', methods=['POST'])
def confirm_appointment():
    if 'customer' not in session:
        return jsonify({"success": False, "error": "Not logged in"})

    data = request.get_json()
    try:
        Appointment.book_appointment_web(
            session['customer']['Patient_id'],
            data.get('doctor_id'),
            data.get('doctor_name'),
            data.get('date'),
            data.get('slot')
        )
        return jsonify({"success": True, "message": "Appointment booked successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/show_appointments')
def show_appointments():
    if 'customer' not in session:
        flash("Please log in.", 'warning')
        return redirect(url_for('login'))

    patient_id = session['customer']['Patient_id']
    appointments = Showappointment.get_patient_appointments(patient_id)
    return render_template('show_appointments.html', appointments=appointments)


@app.route('/logout')
def logout():
    session.clear()  # Drop all contextual authentication structures
    flash("You have been logged out.", 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)