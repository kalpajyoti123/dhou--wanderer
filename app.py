import os
import datetime
import certifi
from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# --- 1. SECURITY & CONFIGURATION ---
# Uses environment variables when live, defaults to a local key for testing
app.secret_key = os.environ.get('SECRET_KEY', 'dhou_wanderer_key_2025')

# --- 2. MONGODB ATLAS CONNECTION ---
# The 'ca' variable points to a bundle of trusted security certificates
ca = certifi.where()

# Use your specific connection string
DEFAULT_URI = "mongodb+srv://dhouwanderer_db_user:bXLzzf90peXqPAVv@dhouwanderer0.6jbswlp.mongodb.net/dhou-wanderer?retryWrites=true&w=majority&appName=dhouwanderer0"
MONGO_URI = os.environ.get('MONGO_URI', DEFAULT_URI)

try:
    # We add 'tlsCAFile=ca' here to fix the SSL Handshake error you encountered
    client = MongoClient(MONGO_URI, tlsCAFile=ca)
    # Ping the database to confirm the connection is active
    client.admin.command('ping')
    db = client['dhou-wanderer']
    bookings_collection = db['bookings']
    print("✅ Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

# --- 3. EMAIL CONFIGURATION ---
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='dhouwanderer@gmail.com',
    # Replace 'MAIL_PASS' in your hosting dashboard with your Gmail App Password
    MAIL_PASSWORD=os.environ.get('MAIL_PASS', 'wemm vgfm hmsv ycij'),
    MAIL_DEFAULT_SENDER=('Wanderer Travels', 'dhouwanderer@gmail.com')
)
mail = Mail(app)

# --- 4. WEBSITE ROUTES ---

@app.route('/')
def home():
    """Main Landing Page"""
    return render_template('index.html')

@app.route('/itinerary/<trip_name>')
def trip_details(trip_name):
    """Individual Trip Detail Pages"""
    formatted_name = trip_name.replace('-', ' ').title()
    return render_template('details.html', trip=formatted_name)

@app.route('/book', methods=['POST'])
def book_trip():
    """Captures Form Data, Saves to Cloud, and Sends Email"""
    destination = request.form.get('destination', 'Expedition')
    user_name = request.form.get('full_name', 'Traveler')
    user_email = request.form.get('email')
    
    # Data to save in MongoDB
    booking_doc = {
        'name': user_name,
        'email': user_email,
        'trip': destination,
        'status': 'Pending',
        'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    try:
        # Save to MongoDB Atlas
        bookings_collection.insert_one(booking_doc)
        
        # Send Automated Confirmation Email
        msg = Message(f"Booking Received: {destination}", recipients=[user_email])
        msg.html = render_template('emails/booking_confirmation.html', 
                                   name=user_name, 
                                   trip=destination)
        mail.send(msg)
    except Exception as e:
        print(f"Error during booking process: {e}")

    # Redirect to Payment Page
    return redirect(url_for('payment_page', trip=destination, amount="15000"))

@app.route('/payment')
def payment_page():
    """Payment Gateway and QR Code Page"""
    trip = request.args.get('trip', 'Expedition')
    amount = request.args.get('amount', '15000')
    return render_template('payment.html', trip=trip, amount=amount)

# --- 5. ADMIN DASHBOARD ---

@app.route('/admin-dashboard')
def admin_page():
    """Secure Dashboard to View Bookings"""
    # Access via: yoursite.com/admin-dashboard?pass=wanderer2025
    password = request.args.get('pass')
    if password != "wanderer2025":
        return "Unauthorized Access", 403
    
    # Fetch all travelers from MongoDB, newest first
    all_bookings = list(bookings_collection.find().sort('_id', -1))
    
    # Calculate Total Revenue from 'Confirmed' bookings only
    total_revenue = sum(15000 for b in all_bookings if b.get('status') == 'Confirmed')
    
    return render_template('admin.html', bookings=all_bookings, revenue=total_revenue)

@app.route('/update-status/<booking_id>/<new_status>')
def update_status(booking_id, new_status):
    """Updates Payment Status (e.g., Pending -> Confirmed)"""
    if request.args.get('pass') != "wanderer2025":
        return "Unauthorized", 403
        
    bookings_collection.update_one(
        {'_id': ObjectId(booking_id)},
        {'$set': {'status': new_status}}
    )
    return redirect(url_for('admin_page', **{'pass': 'wanderer2025'}))

# --- 6. LAUNCH ---
if __name__ == '__main__':
    # Local port 5000; host '0.0.0.0' allows external access
    app.run(debug=True, host='0.0.0.0')