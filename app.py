from flask import Flask, render_template, request, redirect, url_for, flash, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secure-indian-digital-bank-token-9988'

# Database Setup
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'indian_bank.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

fd_count = 5

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=50000) 
    score = db.Column(db.Integer, default=0)
    solved_challenges = db.Column(db.String(500), default="")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_default_admin():
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        new_admin = User(username='admin', password='admin123', account_number='999123456789')
        db.session.add(new_admin)
        db.session.commit()

with app.app_context():
    db.create_all()
    create_default_admin()

def generate_acc_num(username):
    import hashlib
    hash_val = hashlib.md5(username.encode()).hexdigest()
    return "999" + str(int(hash_val, 16))[:9]

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))
        acc_num = generate_acc_num(username)
        new_user = User(username=username, password=password, account_number=acc_num)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Vulnerable SQL Query Simulation
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid User ID or Password!')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    welcome_name = current_user.username
    ssti_triggered = False
    if "{{" in welcome_name and "user" in welcome_name:
        ssti_triggered = True
        welcome_name = "SYSTEM_KEY_7733 (FLAG{A03_SERVER_SIDE_TEMPLATE_INJECTION})"

    return render_template('scoreboard.html', user=current_user, fd_count=fd_count, welcome_name=welcome_name, ssti_triggered=ssti_triggered)

@app.route('/tasks')
@login_required
def tasks():
    users = User.query.order_by(User.score.desc()).all()
    return render_template('tasks.html', users=users, current_user=current_user)

@app.route('/quick-transfer', methods=['POST'])
@login_required
def quick_transfer():
    amount = int(request.form.get('amount', 0))
    target_acc = request.form.get('target_account', '').strip()

    if amount <= 0:
        flash('Cannot process invalid transaction amount!')
        return redirect(url_for('dashboard'))
    
    if target_acc == current_user.account_number:
        current_user.balance += amount  
        db.session.commit()
        flash(f'Self-Transfer Hack Success! FLAG{{A05_BUSINESS_LOGIC_SELF_TRANSFER}}')
        return redirect(url_for('dashboard'))

    if current_user.balance >= amount:
        import time
        current_balance = current_user.balance
        time.sleep(0.4) 
        current_user.balance = current_balance - amount
        db.session.commit()
        flash(f'INR {amount} transferred successfully via IMPS Transfer!')
    else:
        flash('Insufficient liquidity in bank account!')
    return redirect(url_for('dashboard'))

@app.route('/open-fd', methods=['POST'])
@login_required
def open_fd():
    global fd_count
    qty = int(request.form.get('qty', 1))
    cost = qty * 10000
    if current_user.balance >= cost and fd_count >= qty:
        current_user.balance -= cost
        fd_count -= qty
        db.session.commit()
        flash('Fixed Deposit (FD) account opened successfully!')
    else:
        flash('FD procurement rejected. Verify balance limits.')
    return redirect(url_for('dashboard'))

@app.route('/passbook/<int:user_id>')
@login_required
def passbook(user_id):
    target_user = User.query.get_or_404(user_id)
    return f"<div style='font-family:sans-serif; padding:20px;'><h2>Indian Digital Bank - Official E-Passbook Ledger</h2><hr><p><b>Account Holder:</b> {target_user.username}</p><p><b>Account Number:</b> {target_user.account_number}</p><p><b>Available Liquidity:</b> ₹ {target_user.balance}</p></div>"

# Challenge 5: IDOR File Download
@app.route('/download/loan_<int:file_id>.pdf')
@login_required
def download_loan(file_id):
    if file_id == 101:
        return f"<div style='font-family:sans-serif; padding:20px;'><h3>IDB Loan Receipt - Account #101</h3><p>Your basic standard loan statement file is empty.</p></div>"
    elif file_id == 999:
        return f"<div style='font-family:sans-serif; padding:20px; background:#e0f2fe;'><h3>⚠️ IDB Corporate Confidential Loan Scheme #999</h3><p><b>Privileged Document Unlocked!</b></p><p>FLAG{{A01_IDOR_SENSITIVE_FILE_DOWNLOAD}}</p></div>"
    else:
        return f"<div style='font-family:sans-serif; padding:20px;'><h3>Error 404</h3><p>Loan statement sequence not found.</p></div>"

@app.route('/admin-portal')
@login_required
def admin_portal():
    return "<div style='font-family:sans-serif; padding:40px; text-align:center;'><h2>⚠️ Unauthorized Internal Bank Portal ⚠️</h2><p>You found the hidden admin login endpoint!</p><br><span style='background:#f8d7da; padding:10px; border-radius:5px; font-weight:bold; color:#721c24;'>FLAG{A01_FORCED_BROWSING_HIDDEN_ENDPOINT}</span></div>"

@app.route('/submit-flag', methods=['POST'])
@login_required
def submit_flag():
    challenge_id = request.form.get('challenge_id')
    flag_submitted = request.form.get('flag', '').strip()
    
    flags = {
        "sql_i": "FLAG{A01_SQL_INJECTION_BYPASS_SUCCESS}",
        "race_cond": "FLAG{A04_CONCURRENCY_BALANCE_EXPLOIT}",
        "design_stock": "FLAG{A05_INSECURE_DESIGN_NEGATIVE_VALUE}",
        "idor": "FLAG{A01_BROKEN_OBJECT_LEVEL_STATEMENT}",
        "file_download": "FLAG{A01_IDOR_SENSITIVE_FILE_DOWNLOAD}",
        "forced_browse": "FLAG{A01_FORCED_BROWSING_HIDDEN_ENDPOINT}",
        "weak_auth": "FLAG{A02_WEAK_ADMIN_CREDENTIALS_LEAK}",
        "ssti_leak": "FLAG{A03_SERVER_SIDE_TEMPLATE_INJECTION}",
        "logic_flaw": "FLAG{A05_BUSINESS_LOGIC_SELF_TRANSFER}"
    }
    
    if challenge_id in flags and flags[challenge_id] == flag_submitted:
        solved_list = current_user.solved_challenges.split(',') if current_user.solved_challenges else []
        if challenge_id not in solved_list:
            solved_list.append(challenge_id)
            current_user.score += 100
            current_user.solved_challenges = ','.join(solved_list)
            db.session.commit()
            flash('Congratulations! Correct flag submitted. +100 Points.')
        else:
            flash('This challenge was already solved.')
    else:
        flash('Invalid flag signature payload!')
    return redirect(url_for('tasks'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
