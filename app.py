from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'local-secure-bank-token-2026'

instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'indian_bank.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Clean database model definition to prevent Render deployment crashes
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
        # Sets up the target administrator account with standard balance parameters
        new_admin = User(username='admin', password='admin_vault_secure_pass_2026', account_number='999123456789', balance=9999999)
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
        return redirect(url_for('login'))
    return render_template('register.html')

# 📌 Challenge 1: SQL INJECTION ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        is_sqli_pattern = any(trigger in username for trigger in ["', '"', "-", "=", "or", "OR", "admin"])
        
        raw_query = f"SELECT id FROM user WHERE username = '{username}' AND password = '{password}'"
        try:
            result = db.session.execute(db.text(raw_query)).first()
            if result or is_sqli_pattern:
                # 🛠️ Set session flag to explicitly force administrative access tracking
                session['sqli_exploited'] = True
                admin_account = User.query.filter_by(username='admin').first()
                login_user(admin_account)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid Credentials')
        except Exception as e:
            session['sqli_exploited'] = True
            admin_account = User.query.filter_by(username='admin').first()
            login_user(admin_account)
            return redirect(url_for('dashboard'))
            
    return render_template('login.html')

# 📌 Challenge 8 & Core Dashboard Output (FORCED INLINE RENDER)
@app.route('/dashboard')
@login_required
def dashboard():
    welcome_name = current_user.username
    
    # Challenge 8: SSTI Check
    if "{{" in welcome_name:
        injected_template = f"<html><body><h2>Welcome, {welcome_name}! FLAG{{A03_SERVER_SIDE_TEMPLATE_INJECTION}}</h2></body></html>"
        return render_template_string(injected_template)
        
    # 💥 Dynamic verification to force display the flag container block
    sql_flag_alert = ""
    if current_user.username == 'admin' or session.get('sqli_exploited') == True:
        sql_flag_alert = """
        <div class="alert alert-success shadow-sm p-4 mb-4" style="border-left: 5px solid #198754;">
            <h4 class="alert-heading fw-bold">🎯 SQL Injection Successful!</h4>
            <p class="mb-0">You successfully bypassed the login screen using authentication manipulation.</p>
            <hr>
            <p class="mb-0 fw-bold">FLAG: <code class="bg-white p-2 border rounded text-danger">FLAG{A01_SQL_INJECTION_BYPASS_SUCCESS}</code></p>
        </div>
        """
        
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>IDB NetBanking - Dashboard</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{ background-color: #f8f9fa; font-family: sans-serif; }}
            .bank-header {{ background: linear-gradient(135deg, #003366, #0055a5); color: white; padding: 25px 0; }}
            .balance-card {{ background-color: #ffffff; border-left: 5px solid #003366; }}
        </style>
    </head>
    <body>
        <div class="bank-header shadow-sm">
            <div class="container d-flex justify-content-between align-items-center">
                <div>
                    <h2 class="mb-0 fw-bold">🏛️ Indian Digital Bank</h2>
                    <h5 class="text-warning my-1">Welcome, {current_user.username}</h5>
                </div>
                <div>
                    <a href="/tasks" class="btn btn-warning fw-bold me-2">🎯 View Lab Challenges</a>
                    <a href="/logout" class="btn btn-outline-light btn-sm">Secure Logout</a>
                </div>
            </div>
        </div>

        <div class="container mt-4">
            
            {sql_flag_alert}

            <div class="row g-3 mb-4">
                <div class="col-md-6">
                    <div class="card balance-card shadow-sm p-4 h-100">
                        <span class="text-muted text-uppercase small fw-bold">Available Balance Ledger</span>
                        <h1 class="display-5 my-2 text-success fw-bold">₹ {current_user.balance}</h1>
                        <p class="mb-0 text-muted">Account Number: <b>{current_user.account_number}</b></p>
                        <div class="mt-3"><a href="/passbook/1" target="_blank" class="btn btn-sm btn-outline-primary">Check Digital E-Passbook</a></div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card shadow-sm p-4 h-100">
                        <h5 class="text-primary mb-3">⚡ Instant IMPS Funds Transfer</h5>
                        <form action="/quick-transfer" method="POST">
                            <div class="input-group mb-3">
                                <span class="input-group-text">₹</span>
                                <input type="number" name="amount" class="form-control" placeholder="Enter remittance amount" required>
                            </div>
                            <div class="mb-3">
                                <input type="text" name="target_account" class="form-control form-control-sm" placeholder="Beneficiary Account Number" required>
                            </div>
                            <button type="submit" class="btn btn-primary btn-sm w-100">Instant Pay</button>
                        </form>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <div class="card shadow-sm p-4 mb-4">
                        <h5 class="text-success mb-3">📈 Instant Fixed Deposit (FD) Allocation</h5>
                        <form action="/open-fd" method="POST">
                            <div class="d-flex align-items-center mb-3">
                                <label class="me-3 mb-0">Quantity:</label>
                                <input type="number" name="qty" class="form-control form-control-sm w-25" value="1" required>
                            </div>
                            <button type="submit" class="btn btn-success btn-sm">Create New FD Scheme</button>
                        </form>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card shadow-sm p-4">
                        <h5 class="text-info mb-3">📄 Personal Loan Services</h5>
                        <p class="text-muted small">Download your digitally signed active home/car loan documentation forms directly from the cloud repository system.</p>
                        <div class="bg-light p-3 rounded border text-center">
                            <a href="/download/loan_101.pdf" target="_blank" class="btn btn-sm btn-info text-white fw-bold">📥 Download My Loan Receipt (.PDF)</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(dashboard_html)

# 📌 Challenges 2, 7 & 9: RACE CONDITION & BUSINESS LOGIC
@app.route('/quick-transfer', methods=['POST'])
@login_required
def quick_transfer():
    amount = int(request.form.get('amount', 0))
    target_acc = request.form.get('target_account', '').strip()
    is_vip_route = request.form.get('vip_bypass_token')

    if amount == 1337733 and is_vip_route == "activated_override":
        return "<h3>Validation Bypass Defeated! FLAG{A02_CLIENT_SIDE_VALIDATION_BYPASS}</h3>"

    if amount <= 0:
        return redirect(url_for('dashboard'))
    
    if target_acc == current_user.account_number:
        current_user.balance += amount  
        db.session.commit()
        return f"<h3>Self-Transfer Hack Success! FLAG{{A05_BUSINESS_LOGIC_SELF_TRANSFER}}</h3><a href='/dashboard'>Back</a>"

    if current_user.balance >= amount:
        current_balance = current_user.balance
        time.sleep(0.5) 
        current_user.balance = current_balance - amount
        db.session.commit()
        
        if current_user.balance < 0:
            return f"<h3>Race Condition Successful! FLAG{{A04_CONCURRENCY_BALANCE_EXPLOIT}}</h3><a href='/dashboard'>Back</a>"
    return redirect(url_for('dashboard'))

# 📌 Challenge 3: Insecure Design Math
@app.route('/open-fd', methods=['POST'])
@login_required
def open_fd():
    qty = int(request.form.get('qty', 1))
    if qty == -5:
        current_user.balance -= (qty * 10000)
        db.session.commit()
        return f"<h3>Insecure Design Exploit Success! FLAG{{A05_INSECURE_DESIGN_NEGATIVE_VALUE}}</h3>"
    return redirect(url_for('dashboard'))

# 📌 Challenge 4: IDOR Passbook
@app.route('/passbook/<int:user_id>')
@login_required
def passbook(user_id):
    target_user = User.query.get(user_id)
    if target_user and target_user.username == "admin":
        return f"<h2>E-Passbook: {target_user.username}</h2><p><b>FLAG{{A01_BROKEN_OBJECT_LEVEL_STATEMENT}}</b></p>"
    return "Authorized Ledger Access Only", 403

# 📌 Challenge 5: IDOR Download
@app.route('/download/loan_<int:file_id>.pdf')
@login_required
def download_loan(file_id):
    if file_id == 999:
        return "<h3>⚠️ Confidential Document</h3><p>FLAG{A01_IDOR_SENSITIVE_FILE_DOWNLOAD}</p>"
    return "Document Not Found", 404

@app.route('/logout')
@login_required
def logout():
    session.pop('sqli_exploited', None)
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
