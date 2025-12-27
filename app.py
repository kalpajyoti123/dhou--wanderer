from flask import Flask, render_template, request, flash, redirect, url_for
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "dhou_wanderer_key_2025"

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'dhouwanderer@gmail.com'
# UPDATED PASSWORD: wemm vgfm hmsv ycij
app.config['MAIL_PASSWORD'] = 'wemm vgfm hmsv ycij' 
app.config['MAIL_DEFAULT_SENDER'] = ('Wanderer Travels', 'dhouwanderer@gmail.com')

mail = Mail(app)

# --- ROUTES ---

@app.route('/')
def home():
    """Main Landing Page"""
    return render_template('index.html')

@app.route('/itinerary/<trip_name>')
def trip_details(trip_name):
    """Dynamic Route for Destinations"""
    formatted_name = trip_name.replace('-', ' ').title()
    return render_template('details.html', trip=formatted_name)

@app.route('/book', methods=['POST'])
def book_trip():
    """Handles Form Submission, Emailing, and Payment Redirect"""
    destination = request.form.get('destination', 'Unknown Expedition')
    user_name = request.form.get('full_name', 'Valued Traveler')
    user_email = request.form.get('email')
    return redirect(url_for('payment_page', trip=request.form.get('destination'), amount="15000"))

    if not user_email:
        flash("Error: Email address is required.")
        return redirect(url_for('home'))

    # 1. Send HTML Confirmation Email to User
    msg = Message(f"Booking Received: {destination}", recipients=[user_email])
    msg.html = render_template('emails/booking_confirmation.html', 
                               name=user_name, 
                               trip=destination)
    
    # 2. Send Notification Email to You
    admin_msg = Message("NEW BOOKING ALERT", recipients=['dhouwanderer@gmail.com'])
    admin_msg.body = f"New booking request!\n\nName: {user_name}\nEmail: {user_email}\nTrip: {destination}"

    try:
        mail.send(msg)
        mail.send(admin_msg)
    except Exception as e:
        print(f"Email Error: {e}")
        # We proceed to payment even if email fails to keep the user in the funnel

    # 3. Redirect to Payment Page
    # Defaulting amount to 15000 for the expedition deposit
    return redirect(url_for('payment_page', trip=destination, amount="15000"))

@app.route('/payment')
def payment_page():
    """Final Payment Screen"""
    trip = request.args.get('trip', 'Expedition')
    amount = request.args.get('amount', '15000')
    return render_template('payment.html', trip=trip, amount=amount)
if __name__ == '__main__':
    # host='0.0.0.0' allows other devices on the network to connect
    app.run(debug=True, host='0.0.0.0')