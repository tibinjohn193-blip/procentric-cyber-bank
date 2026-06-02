from flask import Flask, render_template, request, redirect, url_for, flash, make_response
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
    balance = db.Column(db.Integer, default=50000) # ₹50,000 initial balance
    score = db.Column(db.Integer, default=0)
    solved_challenges = db.Column(db.String(500), default="")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

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
        # Vulnerable SQL Injection Query Context
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
    is_admin = request.cookies.get('role') == 'admin'
    return render_template('scoreboard.html', user=current_user, fd_count=fd_count, is_admin=is_admin)

@app.route('/tasks')
@login_required
def tasks():
    users = User.query.order_by(User.score.desc()).all()
    return render_template('tasks.html', users=users, current_user=current_user)

@app.route('/quick-transfer', methods=['POST'])
@login_required
def quick_transfer():
    amount = int(request.form.get('amount', 0))
    if amount <= 0:
        flash('Cannot process invalid transaction amount!')
        return redirect(url_for('dashboard'))
    if current_user.balance >= amount:
        import time
        current_balance = current_user.balance
        time.sleep(0.4) # Race Condition window
        current_user.balance = current_balance - amount
        db.session.commit()
        flash(f'INR {amount} transferred successfully via IMPS Transfer!')
    else:
        flash('Insufficient liquidity in current bank account!')
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
    # IDOR Vulnerability
    target_user = User.query.get_or_400(user_id)
    return f"<div style='font-family:sans-serif; padding:20px;'><h2>Indian Digital Bank - Official E-Passbook Ledger</h2><hr><p><b>Account Holder:</b> {target_user.username}</p><p><b>Account Number:</b> {target_user.account_number}</p><p><b>Available Liquidity:</b> ₹ {target_user.balance}</p></div>"

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
        "integrity": "FLAG{A08_INSECURE_COOKIE_DESERIALIZATION_ADMIN}"
    }
    
    if challenge_id in flags and flags[challenge_id] == flag_submitted:
        solved_list = current_user.solved_challenges.split(',') if current_user.solved_challenges else []
        if challenge_id not in solved_list:
            solved_list.append(challenge_id)
            current_user.solved_challenges = ','.join(solved_list)
            current_user.score += 100
            db.session.commit()
            flash('Congratulations! Correct flag submitted. +100 Points added.')
        else:
            flash('This challenge was already solved by your profile.')
    else:
        flash('Invalid flag signature payload! Try again.')
    return redirect(url_for('tasks'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
