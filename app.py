from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from flask_argon2 import Argon2
from flask_socketio import SocketIO, emit, join_room  # include join_room and emit
from datetime import datetime, timedelta
import os, uuid, random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['CHAT_UPLOAD_FOLDER'] = 'static/chat_uploads'
app.config['BANNER_UPLOAD_FOLDER'] = 'static/banners'

db = SQLAlchemy(app)
argon2 = Argon2(app)
socketio = SocketIO(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'mp3', 'wav'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Custom Template Filter ---
@app.template_filter('endswith')
def endswith_filter(s, suffix):
    try:
        return s.lower().endswith(suffix)
    except Exception:
        return False

# Hardcoded crypto prices dictionary
crypto_prices = {
    "Bitcoin (BTC)": 83740,
    "Ethereum (ETH)": 4200,
    "Tether (USDT)": 1.00,
    "Binance Coin (BNB)": 250,
    "Solana (SOL)": 20,
    "XRP (XRP)": 0.50,
    "Dogecoin (DOGE)": 0.08,
    "Cardano (ADA)": 0.35,
    "Shiba Inu (SHIB)": 0.00001,
    "Avalanche (AVAX)": 15,
    "Chainlink (LINK)": 7,
    "Polkadot (DOT)": 5,
    "Polygon (MATIC)": 0.90,
    "Litecoin (LTC)": 90,
    "Bitcoin Cash (BCH)": 302.60,
    "Stellar (XLM)": 0.291831,
    "Uniswap (UNI)": 8.24,
    "Cosmos (ATOM)": 4.75,
    "Monero (XMR)": 213.13,
    "Aptos (APT)": 6.14,
    "Arbitrum (ARB)": 0.434939,
    "VeChain (VET)": 0.02910299,
    "Maker (MKR)": 1743.84,
    "Hedera (HBAR)": 0.201225,
    "Filecoin (FIL)": 3.32,
    "Algorand (ALGO)": 0.241575,
    "Aave (AAVE)": 208.74,
    "Flow (FLOW)": 0.488564,
    "Synthetix (SNX)": 0.927417,
    "Tezos (XTZ)": 0.783848,
    "The Sandbox (SAND)": 0.326515,
    "Decentraland (MANA)": 0.299293,
    "Axie Infinity (AXS)": 3.78,
    "Render (RNDR)": 3.87,
    "Quant (QNT)": 100.26,
    "Optimism (OP)": 1.17,
    "Fantom (FTM)": 0.729751,
    "Neo (NEO)": 9.74,
    "Gala (GALA)": 0.02027405,
    "KuCoin Token (KCS)": 12.03,
    "Lido DAO (LDO)": 1.41,
    "PancakeSwap (CAKE)": 2.12,
    "Enjin Coin (ENJ)": 0.116149,
    "Rocket Pool (RPL)": 6.62,
    "Thorchain (RUNE)": 0.136948,
    "Chiliz (CHZ)": 0.052024,
    "Dash (DASH)": 26.76,
    "IOTA (MIOTA)": 0.209007,
    "Helium (HNT)": 3.28,
    "Convex Finance (CVX)": 2.44,
    "Kadena (KDA)": 0.509776,
    "Ravencoin (RVN)": 0.01386665,
    "Waves (WAVES)": 1.57,
    "Harmony (ONE)": 0.061425,
    "Zilliqa (ZIL)": 0.01399517,
    "SafeMoon (SAFEMOON)": 0.000000009017,
    "Serum (SRM)": 0.01737995,
    "Celo (CELO)": 0.402366,
    "Decred (DCR)": 12.48,
    "Loopring (LRC)": 0.126042
}

# Dictionary mapping crypto names to icon URLs (update as needed)
crypto_icons = {
    "Bitcoin (BTC)": "https://files.catbox.moe/placeholder.png",
    "Ethereum (ETH)": "https://files.catbox.moe/placeholder.png",
    "Tether (USDT)": "https://files.catbox.moe/placeholder.png",
    "Bitcoin Cash (BCH)": "https://files.catbox.moe/l5665s.png",
    "Arbitrum (ARB)": "https://files.catbox.moe/723gdc.png",
    "Maker (MKR)": "https://files.catbox.moe/0m0pil.png",
    "Hedera (HBAR)": "https://files.catbox.moe/y9pouz.png",
    "Filecoin (FIL)": "https://files.catbox.moe/r6fgay.png",
    "Algorand (ALGO)": "https://files.catbox.moe/w3uvom.png",
    "Aave (AAVE)": "https://files.catbox.moe/w9ykzr.png",
    "Flow (FLOW)": "https://files.catbox.moe/qwxads.png",
    "Synthetix (SNX)": "https://files.catbox.moe/vmuo76.png",
    "Tezos (XTZ)": "https://files.catbox.moe/ve9jyu.png",
    "The Sandbox (SAND)": "https://files.catbox.moe/maw8xs.png",
    "Decentraland (MANA)": "https://files.catbox.moe/whm8s1.png",
    "Axie Infinity (AXS)": "https://files.catbox.moe/8o27ns.png",
    "Render (RNDR)": "https://files.catbox.moe/uhcpzp.png",
    "Quant (QNT)": "https://files.catbox.moe/tl7mwc.png",
    "Optimism (OP)": "https://files.catbox.moe/bm39zi.png",
    "Fantom (FTM)": "https://files.catbox.moe/6mlfck.png",
    "Neo (NEO)": "https://files.catbox.moe/6kyya6.png",
    "Gala (GALA)": "https://files.catbox.moe/7qxwap.png",
    # etc.
}

###########################################
# Database Models
###########################################

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Float, default=0.00)
    country = db.Column(db.String(50))
    country_code = db.Column(db.String(20))
    country_flag = db.Column(db.String(10))
    profile_pic = db.Column(db.String(255), default="")  # For an uploaded file name
    profile_pic_url = db.Column(db.String(255), default="")  # NEW: To store the default URL if no file is uploaded
    onboarding_completed = db.Column(db.Boolean, default=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Float, default=0.00)
    country = db.Column(db.String(50))
    street_name = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    opinion = db.Column(db.String(255))
    profile_pic = db.Column(db.String(255), default="default_admin.png")
    profile_pic_url = db.Column(db.String(255), default="")  # <-- New column added here
    onboarding_completed = db.Column(db.Boolean, default=False)

class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    crypto_name = db.Column(db.String(50))
    balance = db.Column(db.Float, default=0.0)

# New Model: MiningPlan
class MiningPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plan_type = db.Column(db.String(50), default="MT4")
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    expire_date = db.Column(db.DateTime)
    profit_rate = db.Column(db.Float)  # e.g., 0.05 means 5% per day profit
    crypto_used = db.Column(db.String(50))
    mining_started = db.Column(db.Boolean, default=False)
    mining_count = db.Column(db.Float, default=0.0000)
    status = db.Column(db.String(20), default="active")  # active, expired, closed
    
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    crypto_name = db.Column(db.String(50))
    amount = db.Column(db.Float)
    usd_value = db.Column(db.Float)
    transaction_type = db.Column(db.String(50))
    hash_id = db.Column(db.String(255))
    status = db.Column(db.String(20), default="success")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Staking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    crypto_name = db.Column(db.String(50))
    amount = db.Column(db.Float)
    staking_period = db.Column(db.String(20))
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    reward = db.Column(db.Float, default=0.0)

class Banner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    display_time = db.Column(db.Integer, nullable=False)
    transition = db.Column(db.String(50), nullable=False)

class ContentSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flash_message = db.Column(db.Text, nullable=True)
    flash_color = db.Column(db.String(7), nullable=True)
    quote_text = db.Column(db.Text, nullable=True)
    quote_logo = db.Column(db.String(255), nullable=True)
    quote_color = db.Column(db.String(7), nullable=True)
    quote_alignment = db.Column(db.String(10), nullable=True)
    experience_description = db.Column(db.Text, nullable=True)
    # News feed update fields
    newsfeed_content = db.Column(db.Text, nullable=True)
    newsfeed_font = db.Column(db.String(50), nullable=True)
    newsfeed_alignment = db.Column(db.String(10), nullable=True)
    newsfeed_media = db.Column(db.String(255), nullable=True)
    newsfeed_media_position = db.Column(db.String(10), nullable=True)
    newsfeed_publish = db.Column(db.String(50), nullable=True)
    # Featured news feed update fields
    newsfeed_headline = db.Column(db.String(255), nullable=True)
    newsfeed_subheading = db.Column(db.String(255), nullable=True)
    newsfeed_message = db.Column(db.Text, nullable=True)
    newsfeed_featured_media = db.Column(db.String(255), nullable=True)

###########################################
# Helper Functions & SocketIO Events
###########################################

def initialize_admin_holdings(admin):
    for crypto in crypto_prices.keys():
        existing = Holding.query.filter_by(admin_id=admin.id, crypto_name=crypto).first()
        if not existing:
            new_hold = Holding(admin_id=admin.id, crypto_name=crypto, balance=999999999.999)
            db.session.add(new_hold)
    db.session.commit()

def init_executions():
    if 'executions' not in session:
        session['executions'] = {}

def send_notification(recipient_id, data):
    """
    Send a notification event to the specified recipient.
    
    :param recipient_id: The ID (user or admin) to which the notification should be sent.
    :param data: A dictionary containing data like sender name, message text, etc.
    """
    socketio.emit('new_chat_notification', data, room=str(recipient_id))

def HoldingsForTrade(user_id):
    holdings = {}
    for crypto in crypto_prices.keys():
        record = Holding.query.filter_by(user_id=user_id, crypto_name=crypto).first()
        if record:
            holdings[crypto] = f"{record.balance:.4f}"
        else:
            holdings[crypto] = "0.0000"
    return holdings

@socketio.on('offer')
def handle_offer(data):
    target = data.get('target')
    emit('offer', data, room=target)

@socketio.on('answer')
def handle_answer(data):
    target = data.get('target')
    emit('answer', data, room=target)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    target = data.get('target')
    emit('ice_candidate', data, room=target)

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        join_room(str(session['user_id']))
    elif 'admin_id' in session:
        join_room(str(session['admin_id']))

###########################################
# New Route for Chat (for User)
###########################################

###########################################
# User Routes
###########################################

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validate passwords...
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('signup'))
        
        # Check if user exists...
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username) | (User.phone_number == phone_number)
        ).first()
        if existing_user:
            flash("Email, username, or phone number already exists!", "danger")
            return redirect(url_for('signup'))
        
        hashed_password = argon2.generate_password_hash(password)
        
        # Retrieve country information from the form
        country_name = request.form['country_name']
        country_code = request.form.get('country_code', '')
        country_flag = request.form.get('country_flag', '')
        
        # Create the new user with additional country fields
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            phone_number=phone_number,
            password=hashed_password,
            country=country_name,
            country_code=country_code,
            country_flag=country_flag
        )
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        session.permanent = True
        init_executions()
        return redirect(url_for('user_onboarding'))
    
    return render_template('user_signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_username = request.form['email_or_username']  # Correct field name
        password = request.form['password']
        user = User.query.filter((User.email == email_or_username) | (User.username == email_or_username)).first()
        if user and argon2.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session.permanent = True
            init_executions()
            if not user.onboarding_completed:
                return redirect(url_for('user_onboarding'))
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        flash("Invalid credentials!", "danger")
    return render_template('user_login.html')

@app.route('/user_onboarding', methods=['GET', 'POST'])
def user_onboarding():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        # Save country information (from the 'country_name' field in your form)
        user.country = request.form.get('country_name', '')
        user.dob = request.form['dob']
        user.gender = request.form['gender']
        user.experience = request.form['experience']
        
        # Process profile picture upload:
        profile_pic = request.files.get('profile_pic')
        if profile_pic and allowed_file(profile_pic.filename):
            filename = f"user_{user.id}." + profile_pic.filename.rsplit('.', 1)[1].lower()
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.profile_pic = filename
            user.profile_pic_url = ""  # Clear the URL when a file is uploaded
        else:
            # No file uploaded: choose a default image URL based on gender.
            default_user_images_male = [
                "https://files.catbox.moe/1nq0v5.png",
                "https://files.catbox.moe/aptcve.png",
                "https://files.catbox.moe/y4nl42.png",
                "https://files.catbox.moe/o6jqi8.png"
            ]
            default_user_images_female = [
                "https://files.catbox.moe/hcsbev.png",
                "https://files.catbox.moe/4tin25.png",
                "https://files.catbox.moe/087gg0.png"
            ]
            if user.gender == "Female":
                user.profile_pic_url = random.choice(default_user_images_female)
            else:
                user.profile_pic_url = random.choice(default_user_images_male)
            user.profile_pic = ""  # Clear any file name
        user.onboarding_completed = True
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('user_onboarding.html', user=user)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    total_balance_usd = 0.0
    holdings = {}
    for crypto in crypto_prices.keys():
        record = Holding.query.filter_by(user_id=user.id, crypto_name=crypto).first()
        if record:
            holdings[crypto] = f"{record.balance:.4f}"
            total_balance_usd += record.balance * crypto_prices.get(crypto, 0)
        else:
            holdings[crypto] = "0.0000"
    user.balance = total_balance_usd
    db.session.commit()
    content_settings = ContentSetting.query.first()
    return render_template('user_dashboard.html', user=user, holdings=holdings,
                           crypto_prices=crypto_prices, crypto_icons=crypto_icons,
                           selected_crypto=list(holdings.keys())[0] if holdings else None,
                           content_settings=content_settings,
                           banners=Banner.query.all(),
                           transactions=Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).all(),
                           total_stakes=0, total_trades=0)

###########################################
# Admin Routes
###########################################

@app.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('admin_signup'))
        existing_admin = Admin.query.filter((Admin.email == email) | (Admin.username == username)).first()
        if existing_admin:
            flash("Email or username already exists!", "danger")
            return redirect(url_for('admin_signup'))
        hashed_password = argon2.generate_password_hash(password)
        new_admin = Admin(username=username, email=email, password=hashed_password)
        db.session.add(new_admin)
        db.session.commit()
        session['admin_id'] = new_admin.id
        session.permanent = True
        return redirect(url_for('admin_onboarding'))
    return render_template('admin_signup.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email_or_username = request.form['email_or_username']
        password = request.form['password']
        admin = Admin.query.filter((Admin.email == email_or_username) | (Admin.username == email_or_username)).first()
        if admin and argon2.check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            session.permanent = True
            if not admin.onboarding_completed:
                return redirect(url_for('admin_onboarding'))
            flash("Admin login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        flash("Invalid credentials!", "danger")
    return render_template('admin_login.html')

@app.route('/admin_onboarding', methods=['GET', 'POST'])
def admin_onboarding():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    admin = Admin.query.get(session['admin_id'])
    if request.method == 'POST':
        # Save country and other info
        admin.country = request.form.get('country_name', '')
        admin.street_name = request.form['street_name']
        admin.dob = request.form['dob']
        admin.gender = request.form['gender']
        admin.opinion = request.form['opinion']
        
        # Process profile picture upload or set a default image URL
        profile_pic = request.files.get('profile_pic')
        default_admin_images = [
            "https://files.catbox.moe/1nq0v5.png",
            "https://files.catbox.moe/aptcve.png",
            "https://files.catbox.moe/y4nl42.png",
            "https://files.catbox.moe/o6jqi8.png"
        ]
        if profile_pic and allowed_file(profile_pic.filename):
            filename = f"admin_{admin.id}." + profile_pic.filename.rsplit('.', 1)[1].lower()
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            admin.profile_pic = filename
            admin.profile_pic_url = ""  # Clear the URL since a file was uploaded
        else:
            # No file uploaded: clear profile_pic and assign a default image URL
            admin.profile_pic = ""
            admin.profile_pic_url = random.choice(default_admin_images)
        
        admin.onboarding_completed = True
        db.session.commit()
        initialize_admin_holdings(admin)
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_onboarding.html', admin=admin)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    admin = Admin.query.get(session['admin_id'])
    holdings = {}
    for crypto in crypto_prices.keys():
        record = Holding.query.filter_by(admin_id=admin.id, crypto_name=crypto).first()
        holdings[crypto] = f"{record.balance:.3f}" if record else "0.000"
    content_settings = ContentSetting.query.first()
    return render_template('admin_dashboard.html', admin=admin, holdings=holdings,
                           crypto_prices=crypto_prices, crypto_icons=crypto_icons,
                           selected_crypto=list(holdings.keys())[0] if holdings else None,
                           content_settings=content_settings,
                           banners=Banner.query.filter_by(admin_id=admin.id).all(),
                           transactions=Transaction.query.filter_by(admin_id=admin.id).order_by(Transaction.timestamp.desc()).all(),
                           total_users=User.query.count(),
                           total_transactions=Transaction.query.count())

@app.route('/send_funds', methods=['GET', 'POST'])
def send_funds():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    admin = Admin.query.get(session['admin_id'])
    users = User.query.all()
    crypto_list = list(crypto_prices.keys())
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        crypto_name = request.form['crypto_name']
        amount = float(request.form['amount'])
        user = User.query.get(user_id)
        
        admin_holding = Holding.query.filter_by(admin_id=admin.id, crypto_name=crypto_name).first()
        if not admin_holding or admin_holding.balance < amount:
            flash("Insufficient funds in admin account!", "danger")
            return redirect(url_for('send_funds'))
        
        # Deduct funds from admin and add to user's holding
        admin_holding.balance -= amount
        user_holding = Holding.query.filter_by(user_id=user.id, crypto_name=crypto_name).first()
        if user_holding:
            user_holding.balance += amount
        else:
            new_holding = Holding(user_id=user.id, crypto_name=crypto_name, balance=amount)
            db.session.add(new_holding)
        
        transaction = Transaction(
            user_id=user.id,
            admin_id=admin.id,
            crypto_name=crypto_name,
            amount=amount,
            usd_value=amount * crypto_prices[crypto_name],
            transaction_type="Admin Fund Transfer",
            hash_id=str(uuid.uuid4())
        )
        db.session.add(transaction)
        db.session.commit()
        flash(f"Successfully sent {amount} of {crypto_name} to {user.username}", "success")
        
        # Send a notification to the user
        send_notification(user.id, {
            'sender': admin.username,
            'message': f"You have received {amount} of {crypto_name} from the admin."
        })
        
        return redirect(url_for('send_funds'))
    
    return render_template('send_funds.html', admin=admin, users=users, crypto_list=crypto_list)
    
@app.route('/trade', methods=['GET', 'POST'])
def trade():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    init_executions()
    if request.method == 'POST':
        order_type = request.form.get('order_type')
        order_kind = request.form.get('order_kind')
        quantity = float(request.form.get('quantity'))
        price = request.form.get('price')
        side = request.form.get('side')
        new_tx = Transaction(
            user_id=user.id,
            crypto_name="Trade",
            amount=quantity,
            usd_value=quantity * (float(price) if price else 0),
            transaction_type=order_type,
            hash_id=str(uuid.uuid4()),
            status="pending"
        )
        db.session.add(new_tx)
        db.session.commit()
        flash("Order submitted!", "success")
    trade_balance_usd = 10000.00  # Example trade account balance
    trade_crypto_balance = "0.5000 BTC"  # Example trade crypto holding
    content_settings = ContentSetting.query.first()
    return render_template('trade.html', user=user,
                           trade_balance_usd=trade_balance_usd,
                           trade_crypto_balance=trade_crypto_balance,
                           holdings=HoldingsForTrade(user.id),
                           crypto_prices=crypto_prices,
                           crypto_icons=crypto_icons,
                           selected_crypto=list(crypto_prices.keys())[0],
                           banners=Banner.query.all(),
                           transactions=Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).all())

def HoldingsForTrade(user_id):
    holdings = {}
    for crypto in crypto_prices.keys():
        record = Holding.query.filter_by(user_id=user_id, crypto_name=crypto).first()
        if record:
            holdings[crypto] = f"{record.balance:.4f}"
        else:
            holdings[crypto] = "0.0000"
    return holdings

@app.route('/staking_route', methods=['GET', 'POST'])
def staking_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    new_stake = None
    if request.method == 'POST':
        crypto_name = request.form.get('crypto_name')
        amount = float(request.form.get('amount'))
        staking_period = request.form.get('staking_period')
        holding = Holding.query.filter_by(user_id=user.id, crypto_name=crypto_name).first()
        if not holding or holding.balance < amount:
            flash(f"Dear {user.username}, insufficient {crypto_name} to stake.", "danger")
            return redirect(url_for('staking_route'))
        holding.balance -= amount
        periods = {"7 days": 7, "30 days": 30, "70 days": 70, "1 year": 365}
        days = periods.get(staking_period, 7)
        end_date = datetime.utcnow() + timedelta(days=days)
        reward_percentage = {"7 days": 0.01, "30 days": 0.05, "70 days": 0.10, "1 year": 0.20}
        reward = amount * reward_percentage.get(staking_period, 0.01)
        new_stake = Staking(user_id=user.id, crypto_name=crypto_name, amount=amount,
                            staking_period=staking_period, end_date=end_date, reward=reward)
        db.session.add(new_stake)
        db.session.commit()
        flash("Staking initiated successfully!", "success")
    
    # Add user_holdings to the context by using your HoldingsForTrade function
    user_holdings = HoldingsForTrade(user.id)
    return render_template('staking.html', user=user, crypto_prices=crypto_prices, new_stake=new_stake, user_holdings=user_holdings)
    
@app.route('/my_stakes')
def my_stakes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    stakes = Staking.query.filter_by(user_id=user.id).order_by(Staking.end_date).all()
    return render_template('my_stakes.html', user=user, stakes=stakes)

@app.route('/transfer')
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    holdings = HoldingsForTrade(user.id)
    content_settings = ContentSetting.query.first()
    return render_template('transfer.html', user=user, holdings=holdings, content_settings=content_settings)
    
@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    crypto = request.form.get('crypto')
    wallet = request.form.get('wallet')
    try:
        amount = float(request.form.get('amount') or 0)
    except ValueError:
        flash("Invalid amount.", "danger")
        return redirect(url_for('transfer'))
    fee = amount * 0.01  # 1% fee
    if amount < 0.0001:
        flash("Minimum withdrawal amount is 0.0001.", "danger")
        return redirect(url_for('transfer'))
    holding = Holding.query.filter_by(user_id=user.id, crypto_name=crypto).first()
    if not holding or holding.balance < amount:
        flash("Insufficient balance for withdrawal.", "danger")
        return redirect(url_for('transfer'))
    holding.balance -= (amount + fee)
    new_tx = Transaction(
        user_id=user.id,
        crypto_name=crypto,
        amount=amount,
        usd_value=amount * crypto_prices.get(crypto, 0),
        transaction_type="Withdrawal",
        hash_id=str(uuid.uuid4()),
        status="pending"
    )
    db.session.add(new_tx)
    db.session.commit()
    flash("Withdrawal submitted and is pending. It may take a while to process. Check your dashboard for transaction status.", "success")
    return redirect(url_for('dashboard'))
    
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        profile_pic = request.files.get('profile_pic')
        if new_username:
            user.username = new_username
        if new_email:
            user.email = new_email
        if new_password:
            if new_password != confirm_password:
                flash("Passwords do not match", "danger")
                return redirect(url_for('settings'))
            user.password = argon2.generate_password_hash(new_password)
        if profile_pic and allowed_file(profile_pic.filename):
            filename = f"user_{user.id}." + profile_pic.filename.rsplit('.', 1)[1].lower()
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.profile_pic = filename
        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for('dashboard'))
    return render_template('settings.html', user=user)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash("Account deleted", "info")
    return redirect(url_for('signup'))

###########################################
# Chat & Admin Chat Routes
###########################################

@app.route('/chat_advisors')
def chat_advisors():
    advisors = Admin.query.all()
    return render_template('chat_advisors.html', advisors=advisors)

@app.route('/chat/<int:advisor_id>', methods=['GET', 'POST'])
def chat_conversation(advisor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    advisor = Admin.query.get(advisor_id)
    if request.method == 'POST':
        message_text = request.form.get('message')
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{file.filename}"
            file.save(os.path.join(app.config['CHAT_UPLOAD_FOLDER'], filename))
            message_text = filename
        if message_text:
            new_msg = ChatMessage(sender_id=user.id, receiver_id=advisor.id,
                                  sender_type='user', message=message_text)
            db.session.add(new_msg)
            db.session.commit()
            return redirect(url_for('chat_conversation', advisor_id=advisor.id))
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == user.id) & (ChatMessage.receiver_id == advisor.id)) |
        ((ChatMessage.sender_id == advisor.id) & (ChatMessage.receiver_id == user.id))
    ).order_by(ChatMessage.timestamp).all()
    return render_template('chat_conversation.html', user=user, advisor=advisor, messages=messages)

@app.route('/admin_settings', methods=['GET', 'POST'])
def admin_settings():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    admin = Admin.query.get(session['admin_id'])
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        profile_pic = request.files.get('profile_pic')
        if new_username:
            admin.username = new_username
        if new_email:
            admin.email = new_email
        if new_password:
            if new_password != confirm_password:
                flash("Passwords do not match", "danger")
                return redirect(url_for('admin_settings'))
            admin.password = argon2.generate_password_hash(new_password)
        if profile_pic and allowed_file(profile_pic.filename):
            filename = f"admin_{admin.id}." + profile_pic.filename.rsplit('.', 1)[1].lower()
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            admin.profile_pic = filename
        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_settings.html', admin=admin)

@app.route('/admin/chat_list')
def admin_chat_list():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    admin = Admin.query.get(session['admin_id'])
    try:
        # If you want all valid users regardless of chat activity:
        users = User.query.all()
    except Exception as e:
        app.logger.error("Error retrieving users: " + str(e))
        flash("Error retrieving users: " + str(e), "danger")
        users = []
    return render_template('admin_chat_list.html', admin=admin, users=users)

@app.route('/admin/chat/<int:user_id>', methods=['GET', 'POST'])
def admin_chat(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    admin = Admin.query.get(session['admin_id'])
    user = User.query.get(user_id)
    if request.method == 'POST':
        message_text = request.form.get('message')
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{file.filename}"
            file.save(os.path.join(app.config['CHAT_UPLOAD_FOLDER'], filename))
            message_text = filename
        if message_text:
            new_msg = ChatMessage(sender_id=admin.id, receiver_id=user.id,
                                  sender_type='admin', message=message_text)
            db.session.add(new_msg)
            db.session.commit()
            return redirect(url_for('admin_chat', user_id=user.id))
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == admin.id) & (ChatMessage.receiver_id == user.id)) |
        ((ChatMessage.sender_id == user.id) & (ChatMessage.receiver_id == admin.id))
    ).order_by(ChatMessage.timestamp).all()
    return render_template('admin_chat.html', admin=admin, user=user, messages=messages)

###########################################
# Content Edit Route (Admin Only)
###########################################
@app.route('/content_edit', methods=['GET', 'POST'])
def content_edit():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    admin = Admin.query.get(session['admin_id'])
    content_settings = ContentSetting.query.first()
    if not content_settings:
        content_settings = ContentSetting(
            flash_message="Welcome to our platform!",
            flash_color="#d4edda",
            quote_text="Your inspirational quote here.",
            quote_logo="",
            quote_color="#555",
            quote_alignment="left",
            experience_description="",
            # New news feed fields with default values:
            newsfeed_content="",
            newsfeed_font="Arial",
            newsfeed_alignment="left",
            newsfeed_media="",
            newsfeed_media_position="top",
            newsfeed_publish=""
        )
        db.session.add(content_settings)
        db.session.commit()
    if request.method == 'POST':
        # Banner Management
        if 'banner_file' in request.files:
            file = request.files.get('banner_file')
            if file and allowed_file(file.filename):
                filename = f"{uuid.uuid4().hex}_{file.filename}"
                file.save(os.path.join(app.config['BANNER_UPLOAD_FOLDER'], filename))
                display_time = request.form.get('display_time', type=int) or 5
                transition = request.form.get('transition') or 'slide'
                new_banner = Banner(admin_id=admin.id, image=filename,
                                    display_time=display_time, transition=transition)
                db.session.add(new_banner)
                flash("New banner uploaded successfully!", "success")
        # Flash Message
        if 'flash_message' in request.form:
            content_settings.flash_message = request.form.get('flash_message')
            content_settings.flash_color = request.form.get('flash_color')
        # Quote Book
        if 'quote_text' in request.form:
            content_settings.quote_text = request.form.get('quote_text')
            content_settings.quote_color = request.form.get('quote_color')
            content_settings.quote_alignment = request.form.get('quote_alignment')
            if 'quote_logo' in request.files:
                qlogo = request.files.get('quote_logo')
                if qlogo and allowed_file(qlogo.filename):
                    qfilename = f"{uuid.uuid4().hex}_{qlogo.filename}"
                    qlogo.save(os.path.join(app.config['BANNER_UPLOAD_FOLDER'], qfilename))
                    content_settings.quote_logo = qfilename
        # Experience Description (if any)
        if 'experience_description' in request.form:
            content_settings.experience_description = request.form.get('experience_description')
        # Transfer Page Editors
        if 'transfer_text1' in request.form:
            content_settings.transfer_text1 = request.form.get('transfer_text1')
        if 'transfer_text_color1' in request.form:
            content_settings.transfer_text_color1 = request.form.get('transfer_text_color1')
        if 'transfer_text2' in request.form:
            content_settings.transfer_text2 = request.form.get('transfer_text2')
        if 'transfer_text_color2' in request.form:
            content_settings.transfer_text_color2 = request.form.get('transfer_text_color2')
        # (Handle Crypto Payment Details as needed)
        # --- NEW: Handle News Feed Fields ---
        if 'newsfeed_content' in request.form:
            content_settings.newsfeed_content = request.form.get('newsfeed_content')
        if 'newsfeed_font' in request.form:
            content_settings.newsfeed_font = request.form.get('newsfeed_font')
        if 'newsfeed_alignment' in request.form:
            content_settings.newsfeed_alignment = request.form.get('newsfeed_alignment')
        if 'newsfeed_media' in request.files:
            nf_media = request.files.get('newsfeed_media')
            if nf_media and allowed_file(nf_media.filename):
                nf_filename = f"{uuid.uuid4().hex}_{nf_media.filename}"
                # Ensure a folder exists for news feed media
                newsfeed_media_folder = os.path.join(app.root_path, 'static', 'newsfeed_media')
                os.makedirs(newsfeed_media_folder, exist_ok=True)
                nf_media.save(os.path.join(newsfeed_media_folder, nf_filename))
                content_settings.newsfeed_media = nf_filename
        if 'newsfeed_media_position' in request.form:
            content_settings.newsfeed_media_position = request.form.get('newsfeed_media_position')
        if 'newsfeed_publish' in request.form:
            content_settings.newsfeed_publish = request.form.get('newsfeed_publish')
        # Commit all changes
        db.session.commit()
        return redirect(url_for('content_edit'))
    banners = Banner.query.filter_by(admin_id=admin.id).all()
    return render_template('content_html.html', admin=admin, banners=banners, content_settings=content_settings)

@app.route('/delete_banner/<int:banner_id>', methods=['POST'])
def delete_banner(banner_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    banner = Banner.query.get(banner_id)
    if banner:
        banner_path = os.path.join(app.config['BANNER_UPLOAD_FOLDER'], banner.image)
        if os.path.exists(banner_path):
            os.remove(banner_path)
        db.session.delete(banner)
        db.session.commit()
        flash("Banner deleted successfully.", "info")
    return redirect(url_for('content_edit'))

###########################################
# Additional Routes (Placeholders)
###########################################
@app.route('/voice_call/<int:advisor_id>')
def voice_call(advisor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    advisor = Admin.query.get(advisor_id)
    return render_template('voice_call.html', advisor=advisor)

@app.route('/live_market')
def live_market():
    return render_template('live_market.html')

@app.route('/news_feed')
def news_feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    content_settings = ContentSetting.query.first()
    latest_update = content_settings.newsfeed_content if content_settings else ""
    latest_update_date = content_settings.newsfeed_publish if content_settings else ""
    previous_update = "<p>No previous update.</p>"
    previous_update_date = ""
    return render_template('news_feed.html',
                           user=user,
                           latest_update=latest_update,
                           latest_update_date=latest_update_date,
                           previous_update=previous_update,
                           previous_update_date=previous_update_date,
                           featured_headline=content_settings.newsfeed_headline if content_settings else "",
                           featured_media=content_settings.newsfeed_featured_media if content_settings else "",
                           featured_subheading=content_settings.newsfeed_subheading if content_settings else "",
                           featured_message=content_settings.newsfeed_message if content_settings else "",
                           featured_publish=content_settings.newsfeed_publish if content_settings else "")

###########################################
# New Routes for Mining Plan Purchase and Mining Start
###########################################

@app.route('/purchase_mining_plan', methods=['POST'])
def purchase_mining_plan():
    """
    Purchase an MT4 mining plan at a fixed price of $500.
    Checks if the user has at least $500 worth of the selected crypto.
    Only allows purchase if the user does not already have an active plan.
    Deducts the equivalent crypto amount from the user's holdings.
    For the first plan, sets a 7-day expiry and a fixed profit rate.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    
    # Ensure the user does not have an active mining plan
    active_plan = MiningPlan.query.filter_by(user_id=user.id, status="active").first()
    if active_plan:
        flash("You already have an active mining plan.", "danger")
        return redirect(url_for('mining'))
    
    crypto_used = request.form.get('crypto')
    if crypto_used not in crypto_prices:
        flash("Invalid crypto selection.", "danger")
        return redirect(url_for('mining'))
    
    # Check user's holding for the selected crypto
    holding = Holding.query.filter_by(user_id=user.id, crypto_name=crypto_used).first()
    crypto_price = crypto_prices[crypto_used]
    if not holding or holding.balance * crypto_price < 500:
        flash(f"Insufficient balance. You need at least $500 worth of {crypto_used}.", "danger")
        return redirect(url_for('mining'))
    
    # Deduct the required crypto amount (fixed $500 price)
    crypto_deduction = 500 / crypto_price
    holding.balance -= crypto_deduction
    
    # Create the mining plan (first plan: 7 days expiry; you can later adjust profit_rate as needed)
    purchase_date = datetime.utcnow()
    expire_date = purchase_date + timedelta(days=7)
    profit_rate = 0.05  # example profit rate for the first MT4 plan (5% daily)
    new_plan = MiningPlan(user_id=user.id,
                          purchase_date=purchase_date,
                          expire_date=expire_date,
                          profit_rate=profit_rate,
                          crypto_used=crypto_used,
                          status="active")
    db.session.add(new_plan)
    db.session.commit()
    
    flash("Mining plan purchased successfully! Your plan expires in 7 days.", "success")
    return redirect(url_for('mining'))


@app.route('/start_mining', methods=['POST'])
def start_mining():
    """
    Starts mining for the active mining plan.
    Sets the mining_started flag to True so that the frontend can enable the mining counter.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    active_plan = MiningPlan.query.filter_by(user_id=user.id, status="active").first()
    if not active_plan:
        flash("No active mining plan found.", "danger")
        return redirect(url_for('mining'))
    
    active_plan.mining_started = True
    db.session.commit()
    flash("Mining started!", "success")
    return redirect(url_for('mining'))


@app.route('/mining')
def mining():
    """
    Renders the mining dashboard.
    Passes the active mining plan (if any) so that the frontend can show:
      - The unlocked plan with an indicator (e.g. Every Hour Mining)
      - The mining count box with a Start Mining button if mining hasn't started
      - A locked state (with glowing border) for plans not available.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    active_plan = MiningPlan.query.filter_by(user_id=user.id, status="active").first()
    return render_template('mining.html', user=user, active_plan=active_plan)

@app.route('/notifications')
def notifications():
    return "Notifications here."

@app.route('/rewards_bonus')
def rewards_bonus():
    return "Rewards and Bonus info here."

###########################################
# Logout Route
###########################################
@app.route('/logout', endpoint="logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

###########################################
# Create Database Tables
###########################################
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True)