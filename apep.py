from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_argon2 import Argon2
from flask_socketio import SocketIO
from datetime import datetime, timedelta
import os, uuid, random

app = Flask(__name__)  # Use __name__
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure value or use an env variable
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'

# Ensure profile picture folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
argon2 = Argon2(app)
socketio = SocketIO(app)

# Allowed file extensions for profile pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Hardcoded crypto prices dictionary (prices in USD per 1 unit)
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

###########################################
#             Database Models             #
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
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    experience = db.Column(db.String(20))
    profile_pic = db.Column(db.String(255), default="default_male.png")
    watchlist = db.Column(db.Text, default="[]")
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
    onboarding_completed = db.Column(db.Boolean, default=False)

class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    crypto_name = db.Column(db.String(50))
    balance = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    crypto_name = db.Column(db.String(50))
    amount = db.Column(db.Float)
    usd_value = db.Column(db.Float)
    transaction_type = db.Column(db.String(50))
    hash_id = db.Column(db.String(255))
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

###########################################
#        Helper Functions & Routes        #
###########################################

def initialize_admin_holdings(admin):
    """For every crypto in crypto_prices, create a Holding with a huge balance if not exists."""
    for crypto in crypto_prices.keys():
        existing = Holding.query.filter_by(admin_id=admin.id, crypto_name=crypto).first()
        if not existing:
            new_hold = Holding(admin_id=admin.id, crypto_name=crypto, balance=999999999.999)
            db.session.add(new_hold)
    db.session.commit()

# ----- User Routes -----
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
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('signup'))
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username) | (User.phone_number == phone_number)
        ).first()
        if existing_user:
            flash("Email, username, or phone number already exists!", "danger")
            return redirect(url_for('signup'))
        hashed_password = argon2.generate_password_hash(password)
        new_user = User(first_name=first_name, last_name=last_name, username=username,
                        email=email, phone_number=phone_number, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        session.permanent = True
        return redirect(url_for('user_onboarding'))
    return render_template('user_signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_username = request.form['email_or_username']
        password = request.form['password']
        user = User.query.filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()
        if user and argon2.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session.permanent = True
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
        user.country = request.form['country']
        user.dob = request.form['dob']
        user.gender = request.form['gender']
        user.experience = request.form['experience']
        profile_pic = request.files.get('profile_pic')
        if profile_pic and allowed_file(profile_pic.filename):
            filename = f"user_{user.id}." + profile_pic.filename.rsplit('.', 1)[1].lower()
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.profile_pic = filename
        user.onboarding_completed = True
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('user_onboarding.html', user=user)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    
    # Calculate total balance from crypto holdings.
    total_balance_usd = 0.0
    holdings = {}
    for crypto in crypto_prices.keys():
        record = Holding.query.filter_by(user_id=user.id, crypto_name=crypto).first()
        if record:
            holdings[crypto] = f"{record.balance:.4f}"
            total_balance_usd += record.balance * crypto_prices.get(crypto, 0)
        else:
            holdings[crypto] = "0.0000"
    
    # Update user's USD balance based on crypto holdings.
    user.balance = total_balance_usd
    db.session.commit()
    
    return render_template('user_dashboard.html', user=user, holdings=holdings)

# ----- Admin Routes -----
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
        existing_admin = Admin.query.filter(
            (Admin.email == email) | (Admin.username == username)
        ).first()
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
        admin = Admin.query.filter(
            (Admin.email == email_or_username) | (Admin.username == email_or_username)
        ).first()
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
        admin.country = request.form['country']
        admin.street_name = request.form['street_name']
        admin.dob = request.form['dob']
        admin.gender = request.form['gender']
        admin.opinion = request.form['opinion']
        profile_pic = request.files.get('profile_pic')
        if profile_pic and allowed_file(profile_pic.filename):
            filename = f"admin_{admin.id}." + profile_pic.filename.rsplit('.', 1)[1].lower()
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            admin.profile_pic = filename
        admin.onboarding_completed = True
        db.session.commit()
        # Initialize admin holdings with huge amounts for all cryptos.
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
    return render_template('admin_dashboard.html', admin=admin, holdings=holdings)

# New Admin Send Funds Route
@app.route('/admin/send_funds', methods=['GET', 'POST'])
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
            usd_value = amount * crypto_prices[crypto_name],
            transaction_type = "Admin Fund Transfer",
            hash_id = str(uuid.uuid4())
        )
        db.session.add(transaction)
        db.session.commit()
        flash(f"Successfully sent {amount} of {crypto_name} to {user.username}", "success")
        return redirect(url_for('send_funds'))
    return render_template('send_funds.html', admin=admin, users=users, crypto_list=crypto_list)

# ----- Trade Route -----
@app.route('/trade', methods=['GET', 'POST'])
def trade():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        crypto_name = request.form.get('crypto_name')
        # The quantity entered represents the lot size the user wishes to trade.
        quantity = float(request.form.get('quantity'))
        trade_type = request.form.get('trade_type')  # "buy" or "sell"
        leverage = float(request.form.get('leverage', 1))
        
        if crypto_name not in crypto_prices:
            flash("Invalid crypto selected", "danger")
            return redirect(url_for('trade'))
        
        price = crypto_prices[crypto_name]
        usd_value = quantity * price * leverage
        
        if trade_type == 'buy':
            if user.balance < usd_value:
                flash("Insufficient USD balance. Please fund your account to execute a trade.", "danger")
                return redirect(url_for('trade'))
            # Deduct the USD cost but do not immediately add to crypto balance.
            user.balance -= usd_value
            # Instead, record the buy execution in a container (e.g., via flash or storing in Transaction).
            flash(f"Buy order executed: {quantity} {crypto_name} bought for ${usd_value:.2f}. (Execution recorded)", "success")
            # Optionally, store the execution details in a separate log (here we record the transaction)
        
        elif trade_type == 'sell':
            holding = Holding.query.filter_by(user_id=user.id, crypto_name=crypto_name).first()
            if not holding or holding.balance < quantity:
                flash("Insufficient crypto balance to execute a sell order.", "danger")
                return redirect(url_for('trade'))
            factor = random.uniform(0.95, 1.05)
            sell_value = quantity * price * factor * leverage
            profit_loss = sell_value - usd_value
            # Deduct the sold crypto from the execution container (simulate that the crypto was held earlier)
            holding.balance -= quantity
            user.balance += sell_value
            if profit_loss >= 0:
                flash(f"Sell order executed: Profit of ${profit_loss:.2f}.", "success")
            else:
                flash(f"Sell order executed: Loss of ${abs(profit_loss):.2f}.", "warning")
        else:
            flash("Invalid trade type selected.", "danger")
            return redirect(url_for('trade'))
        
        # Record the transaction
        hash_id = uuid.uuid4().hex
        new_transaction = Transaction(user_id=user.id, crypto_name=crypto_name,
                                      amount=quantity, usd_value=usd_value,
                                      transaction_type=trade_type, hash_id=hash_id)
        db.session.add(new_transaction)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('trade.html', user=user, crypto_prices=crypto_prices)

# ----- Staking Route -----
@app.route('/staking', methods=['GET', 'POST'])
def staking():
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
            flash(f"Dear {user.username}, you have insufficient {crypto_name} assets. Please deposit funds to execute staking.", "danger")
            return redirect(url_for('staking'))
        # Deduct the staked amount
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
    return render_template('staking.html', user=user, crypto_prices=crypto_prices, new_stake=new_stake)

@app.route('/my_stakes')
def my_stakes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    stakes = Staking.query.filter_by(user_id=user.id).order_by(Staking.end_date).all()
    return render_template('my_stakes.html', user=user, stakes=stakes)

# ----- Settings Route -----
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        new_last_name = request.form.get('last_name')
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if new_last_name:
            user.last_name = new_last_name
        if new_password:
            if new_password != confirm_password:
                flash("Passwords do not match", "danger")
                return redirect(url_for('settings'))
            user.password = argon2.generate_password_hash(new_password)
        db.session.commit()
        flash("Settings updated", "success")
        return redirect(url_for('dashboard'))
    return render_template('settings.html', user=user)

# ----- Delete Account Route -----
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
#          Logout Route (Renamed)         #
###########################################
@app.route('/logout', endpoint="logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

###########################################
#          Create Database Tables         #
###########################################
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True)