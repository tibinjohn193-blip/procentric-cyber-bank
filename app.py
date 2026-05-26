import os
import time
import sqlite3
from flask import Flask, render_template, redirect, url_for, request, flash, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'procentric_super_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///procentric_bank.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Integer, default=5000)
    score = db.Column(db.Integer, default=0)
    solved_challenges = db.Column(db.String(300), default="")

SHOP_STOCK = {"iphone": 1}

FLAGS = {
    "sql_i": "FLAG{A03_SQL_INJECTION_BYPASS_SUCCESS}",
    "crypto": "FLAG{A02_PLAINTEXT_PASSWORD_EXPOSED}",
    "idor": "FLAG{A01_IDOR_BANK_STATEMENT_LEAK}",
    "design_stock": "FLAG{A04_INSECURE_DESIGN_STOCK_BYPASS}",
    "race_cond": "FLAG{RACE_CONDITION_TRANSACTION_FRAUD}",
    "config": "FLAG{A05_SECURITY_MISCONFIGURATION_EXPOSED}",
    "xss": "FLAG{A03_XSS_STORED_SCRIPT_EXECUTION}",
    "csrf": "FLAG{A01_CSRF_MONEY_DRAINED_WITHOUT_TOKEN}",
    "brute": "FLAG{A07_BRUTE_FORCE_CREDENTIAL_STUFFING}",
    "integrity": "FLAG{A08_INSECURE_COOKIE_DESERIALIZATION_ADMIN}"
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            conn = sqlite3.connect('instance/procentric_bank.db')
            cursor = conn.cursor()
            query = f"SELECT id FROM user WHERE username = '{username}' AND password = '{password}'"
            cursor.execute(query)
            user_row = cursor.fetchone()
            conn.close()
            
            if user_row:
                user = User.query.get(user_row[0])
                login_user(user)
                resp = make_response(redirect(url_for('scoreboard')))
                resp.set_cookie('role', 'customer')
                return resp
        except Exception as e:
            pass

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            resp = make_response(redirect(url_for('scoreboard')))
            resp.set_cookie('role', 'customer')
            return resp
            
        flash('Invalid Username or Password!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please Log In.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/scoreboard')
@login_required
def scoreboard():
    all_users = User.query.order_by(User.score.desc()).all()
    user_role = request.cookies.get('role')
    is_admin = True if user_role == 'admin' else False
    return render_template('scoreboard.html', users=all_users, is_admin=is_admin, stock=SHOP_STOCK["iphone"])

@app.route('/instant-withdraw', methods=['POST'])
@login_required
def instant_withdraw():
    amount = int(request.form.get('amount'))
    if current_user.balance >= amount:
        time.sleep(0.4) 
        current_user.balance -= amount
        db.session.commit()
        if current_user.balance < 0:
            flash(f"Exploit Successful! Race Condition Triggered. Flag: {FLAGS['race_cond']}")
        else:
            flash(f"Successfully withdrew INR {amount}")
    else:
        flash("Insufficient funds for instantaneous withdrawal!")
    return redirect(url_for('scoreboard'))

@app.route('/buy-gift', methods=['POST'])
@login_required
def buy_gift():
    qty = int(request.form.get('qty'))
    price = 10000
    total_cost = price * qty
    
    if current_user.balance >= total_cost:
        current_user.balance -= total_cost
        SHOP_STOCK["iphone"] -= qty
        db.session.commit()
        if qty < 0 or SHOP_STOCK["iphone"] < 0:
            flash(f"Inventory/Price Integrity Violated! Flag: {FLAGS['design_stock']}")
        else:
            flash("Purchased Successfully!")
    else:
        flash("Transaction declined due to insufficient balance.")
    return redirect(url_for('scoreboard'))

@app.route('/statement/<int:account_id>')
@login_required
def view_statement(account_id):
    target_user = User.query.get(account_id)
    if target_user:
        return f"<h3>Procentric Cyber Bank Statement</h3>Owner Account: {target_user.username}<br>Current Balance: INR {target_user.balance}<br>Flag: {FLAGS['idor']}"
    return "Statement Not Found", 404

@app.route('/transfer-funds', methods=['POST'])
@login_required
def transfer_funds():
    to_user = request.form.get('to_user')
    amount = int(request.form.get('amount'))
    recipient = User.query.filter_by(username=to_user).first()
    if recipient and current_user.balance >= amount:
        current_user.balance -= amount
        recipient.balance += amount
        db.session.commit()
        return jsonify({"status": "Success", "flag": FLAGS['csrf']})
    return jsonify({"status": "Failed"}), 400

@app.route('/backup-config.cfg')
def backup_config():
    return f"DB_NAME=procentric_bank.db\nDEBUG=True\nFLAG_CONFIG={FLAGS['config']}\nADMIN_PASSWORD=SuperSecureAdminPassword2026"

@app.route('/submit-flag', methods=['POST'])
@login_required
def submit_flag():
    challenge_id = request.form.get('challenge_id')
    submitted_flag = request.form.get('flag').strip()
    solved_list = current_user.solved_challenges.split(",") if current_user.solved_challenges else []
    
    if challenge_id in solved_list:
        flash("You have already claimed points for this challenge!")
    elif FLAGS.get(challenge_id) == submitted_flag:
        current_user.score += 100
        solved_list.append(challenge_id)
        current_user.solved_challenges = ",".join(solved_list)
        db.session.commit()
        flash("Brilliant! Correct Flag. +100 Points added to your rank.")
    else:
        flash("Invalid Flag format or payload. Keep auditing!")
    return redirect(url_for('scoreboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password="SuperSecureAdminPassword2026"))
            db.session.commit()
    app.run(debug=True)