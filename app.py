from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'local-secure-bank-token-2026'

# Database Directory Configuration
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'indian_bank.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Account Database Architecture
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

# Provisions baseline administrator reference record on launch
def create_default_admin():
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        new_admin = User(username='admin', password='admin_vault_secure_pass_2026', account_number='999123456789', balance=50000)
        db.session.add(new_admin)
        db.session.commit()

with app.app_context():
    db.create_all()
    create_default_admin()

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
        
        import hashlib
        hash_val = hashlib.md5(username.encode()).hexdigest()
        acc_num = "999" + str(int(hash_val, 16))[:9]

        new_user = User(username=username, password=password, account_number=acc_num)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')


# 📌 Challenge 1: SQL INJECTION AUTH BYPASS
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Explicit evaluation window flags common injection keywords and structures safely
        is_sqli_attempt = any(char in username for char in ["'", '"', "-", "=", "or", "OR"])
        raw_query = f"SELECT id FROM user WHERE username = '{username}' AND password = '{password}'"
        
        try:
            result = db.session.execute(db.text(raw_query)).first()
            if result or is_sqli_attempt:
                user = User.query.get(1) # Automatically authenticates the session as Admin
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid User ID or Password!')
        except Exception as e:
            # If complex runtime payloads trigger DB parser issues, reward execution with Admin access
            user = User.query.get(1)
            login_user(user)
            return redirect(url_for('dashboard'))
            
    return render_template('login.html')


# 📌 Challenge 1 (Admin Source Leak) & Challenge 8 (SSTI Hub)
@app.route('/dashboard')
@login_required
def dashboard():
    welcome_name = current_user.username
    
    # Challenge 8 Execution Trace
    if "{{" in welcome_name:
        injected_template = f"<h2>Welcome, {welcome_name}! FLAG{{A03_SERVER_SIDE_TEMPLATE_INJECTION}}</h2>"
        return render_template_string(injected_template)
        
    # Challenge 1 Payload Delivery: Injects the flag strictly within the Admin view source markup.
    if current_user.username == 'admin':
        admin_dashboard_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Core Control Panel</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        </head>
        <body class="bg-dark text-white">
            <div class="container mt-5">
                <div class="card bg-secondary text-white shadow">
                    <div class="card-header bg-danger text-center">
                        <h3>⚠️ SYSTEM ADMINISTRATOR CONTROL PANEL</h3>
                    </div>
                    <div class="card-body text-center">
                        <h5>Welcome back, System Admin!</h5>
                        <p class="mt-3">All application services and relational backend layers are operational.</p>
                        <p>To audit score progress, review the lab task tracker overview page.</p>
                        <a href="/logout" class="btn btn-danger mt-3">Secure Terminal Logout</a>
                    </div>
                </div>
            </div>
            
            </body>
        </html>
        """
        return render_template_string(admin_dashboard_html)

    return render_template('scoreboard.html', user=current_user, sql_flag="")


# 📌 Challenges 2, 7 & 9: RACE CONDITION, CLIENT BYPASS & BUSINESS LOGIC
@app.route('/quick-transfer', methods=['POST'])
@login_required
def quick_transfer():
    amount = int(request.form.get('amount', 0))
    target_acc = request.form.get('target_account', '').strip()
    is_vip_route = request.form.get('vip_bypass_token')

    # Challenge 7 Check
    if amount == 1337733 and is_vip_route == "activated_override":
        flash("Validation Bypass Defeated! FLAG{A02_CLIENT_SIDE_VALIDATION_BYPASS}")
        return redirect(url_for('dashboard'))

    if amount <= 0:
        flash('Cannot process invalid transaction amount!')
        return redirect(url_for('dashboard'))
    
    # Challenge 9 Check
    if target_acc == current_user.account_number:
        current_user.balance += amount  
        db.session.commit()
        flash(f'Self-Transfer Hack Success! FLAG{{A05_BUSINESS_LOGIC_SELF_TRANSFER}}')
        return redirect(url_for('dashboard'))

    # Challenge 2 Check
    if current_user.balance >= amount:
        current_balance = current_user.balance
        time.sleep(0.5)
        current_user.balance = current_balance - amount
        db.session.commit()
        
        if current_user.balance < 0:
            flash('Race Condition Successful! FLAG{A04_CONCURRENCY_BALANCE_EXPLOIT}')
        else:
            flash(f'INR {amount} transferred successfully!')
    else:
        flash('Insufficient balance!')
    return redirect(url_for('dashboard'))


# 📌 Challenge 3: Insecure Design Math
@app.route('/open-fd', methods=['POST'])
@login_required
def open_fd():
    qty = int(request.form.get('qty', 1))
    if qty == -5:
        current_user.balance -= (qty * 10000)
        db.session.commit()
        flash('Insecure Design Exploit Success! FLAG{A05_INSECURE_DESIGN_NEGATIVE_VALUE}')
        return redirect(url_for('dashboard'))
    return redirect(url_for('dashboard'))


# 📌 Challenge 4: Object Access Traversal IDOR
@app.route('/passbook/<int:user_id>')
@login_required
def passbook(user_id):
    target_user = User.query.get(user_id)
    if target_user:
        if target_user.username == "admin":
            return f"<h2>E-Passbook: {target_user.username}</h2><p><b>FLAG{{A01_BROKEN_OBJECT_LEVEL_STATEMENT}}</b></p>"
        return f"<h2>E-Passbook: {target_user.username}</h2>"
    return "Not Found", 404


# 📌 Challenge 5: Direct Path Resource Fetch IDOR
@app.route('/download/loan_<int:file_id>.pdf')
@login_required
def download_loan(file_id):
    if file_id == 999:
        return "<h3>⚠️ Confidential Document</h3><p>FLAG{A01_IDOR_SENSITIVE_FILE_DOWNLOAD}</p>"
    return "<h3>Document Not Found</h3>", 404


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
