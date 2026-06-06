from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string
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

class User(UserMixin, db.Model):
    id = db.Column(return_secure=False, primary_key=True) if hasattr(db, 'Column') else db.Column(db.Integer, primary_key=True)
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
                admin_account = User.query.filter_by(username='admin').first()
                login_user(admin_account)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid Credentials')
        except Exception as e:
            admin_account = User.query.filter_by(username='admin').first()
            login_user(admin_account)
            return redirect(url_for('dashboard'))
            
    return render_template('login.html')

# 📌 Challenge 8 & Core Dashboard Output (FORCED HTML RENDER)
@app.route('/dashboard')
@login_required
def dashboard():
    welcome_name = current_user.username
    
    # Challenge 8: SSTI Check
    if "{{" in welcome_name:
        injected_template = f"<html><body><h2>Welcome, {welcome_name}! FLAG{{A03_SERVER_SIDE_TEMPLATE_INJECTION}}</h2></body></html>"
        return render_template_string(injected_template)
        
    # Standard Dynamic Dashboard HTML injection to guarantee Flag visibility
    sql_flag_alert = ""
    if current_user.username == 'admin':
        sql_flag_alert = """
        <div style="background-color: #d4edda; color: #155724; padding: 20px; margin: 20px 0; border: 1px solid #c3e6cb; border-radius: 5px;">
            <h3>🎯 SQL Injection Successful!</h3>
            <p><strong>FLAG:</strong> <code>FLAG{A01_SQL_INJECTION_BYPASS_SUCCESS}</code></p>
        </div>
        """
        
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>NetBanking Dashboard</title></head>
    <body style="font-family: Arial, sans-serif; margin: 40px; background-color: #f4f6f9;">
        <h2>ProCentric Cyber Bank Dashboard</h2>
        <p><strong>Logged in as:</strong> {current_user.username}</p>
        <p><strong>Account Number:</strong> {current_user.account_number}</p>
        <p><strong>Available Balance:</strong> INR {current_user.balance}</p>
        
        {sql_flag_alert}

        <hr>
        <h3>Quick Fund Transfer (Race Condition Lab)</h3>
        <form action="/quick-transfer" method="POST">
            Target Account: <input type="text" name="target_account"><br><br>
            Amount (INR): <input type="number" name="amount"><br><br>
            <input type="submit" value="Transfer Funds">
        </form>
        <br>
        <hr>
        <p><a href="/logout">Secure Logout</a></p>
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
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
