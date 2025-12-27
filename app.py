import datetime
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from pymongo import MongoClient
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# --- 1. MONGODB ATLAS CONNECTION ---
# Using your provided connection string
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI)
    # Testing the connection
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB Atlas!")
    db = client['dhou-wanderer']
    bookings_collection = db['bookings']
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

# --- 2. EMAIL CONFIGURATION ---
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD")
)
mail = Mail(app)

# --- 3. ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/itinerary/<trip_name>')
def trip_details(trip_name):
    formatted_name = trip_name.replace('-', ' ').title()
    return render_template('details.html', trip=formatted_name)

@app.route('/book', methods=['POST'])
def book_trip():
    destination = request.form.get('destination')
    user_name = request.form.get('full_name')
    user_email = request.form.get('email')
    
    # SAVE to MongoDB Atlas
    booking_data = {
        'name': user_name,
        'email': user_email,
        'trip': destination,
        'status': 'Pending',
        'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    try:
        bookings_collection.insert_one(booking_data)
    except Exception as e:
        print(f"Database Insert Error: {e}")

    # SEND Emails
    try:
        msg = Message(f"Booking Received: {destination}", recipients=[user_email])
        msg.html = render_template('emails/booking_confirmation.html', name=user_name, trip=destination)
        mail.send(msg)
    except Exception as e:
        print(f"Email Error: {e}")

    return redirect(url_for('payment_page', trip=destination, amount="15000"))

@app.route('/payment')
def payment_page():
    trip = request.args.get('trip')
    amount = request.args.get('amount')
    return render_template('payment.html', trip=trip, amount=amount)

@app.route('/admin-dashboard')
def admin_page():
    # Security: Access via /admin-dashboard?pass=wanderer2025
    if request.args.get('pass') != os.getenv("ADMIN_PASS"):
        return "Unauthorized Access", 403
    
    try:
        # Pull from MongoDB and sort by newest first
        all_bookings = list(bookings_collection.find().sort('_id', -1))
    except Exception as e:
        print(f"Fetch Error: {e}")
        all_bookings = []
        
    return render_template('admin.html', bookings=all_bookings)

@app.route('/update-status/<booking_id>/<new_status>')
def update_status(booking_id, new_status):
    if request.args.get('pass') != os.getenv("ADMIN_PASS"):
        return "Unauthorized", 403
        
    bookings_collection.update_one(
        {'_id': ObjectId(booking_id)},
        {'$set': {'status': new_status}}
    )
    return redirect(url_for('admin_page', **{'pass': os.getenv("ADMIN_PASS")}))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')