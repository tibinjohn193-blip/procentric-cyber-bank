from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import time
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'local-secure-bank-token-2026'

# Database Setup
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'indian_bank.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 9 Challenges - Exact Flag Mapping
VERIFIED_FLAGS = {
    "1": "FLAG{A01_SQL_INJECTION_BYPASS_SUCCESS}",
    "2": "FLAG{A01_BROKEN_OBJECT_LEVEL_STATEMENT}",
    "3": "FLAG{A01_IDOR_SENSITIVE_FILE_DOWNLOAD}",
    "4": "FLAG{A02_CLIENT_SIDE_VALIDATION_BYPASS}",
    "5": "FLAG{A03_SERVER_SIDE_TEMPLATE_INJECTION}",
    "6": "FLAG{A04_CONCURRENCY_BALANCE_EXPLOIT}",
    "7": "FLAG{A05_INSECURE_DESIGN_NEGATIVE_VALUE}",
    "8": "FLAG{A05_BUSINESS_LOGIC_SELF_TRANSFER}",
    "9": "FLAG{A05_MISSING_ACCESS_CONTROL_ROUTING}"
}

# User Model with Solved Challenges Tracking
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=50000) 
    sql_injected_flag = db.Column(db.String(150), default="")
    hint_viewed = db.Column(db.Boolean, default=False)
    user_ip = db.Column(db.String(50), default="")
    solved_challenges = db.Column(db.String(300), default="[]") # Saved as JSON Array string

    def get_solved_list(self):
        try:
            return json.loads(self.solved_challenges)
        except:
            return []

    def solve_challenge(self, chal_id):
        solved = self.get_solved_list()
        if chal_id not in solved:
            solved.append(chal_id)
            self.solved_challenges = json.dumps(solved)
            return True
        return False

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

# 📌 REGISTER ROUTE
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('danger:Username already exists!')
            return redirect(url_for('register'))
        
        import hashlib
        hash_val = hashlib.md5(username.encode()).hexdigest()
        acc_num = "999" + str(int(hash_val, 16))[:9]
        client_ip = request.remote_addr

        new_user = User(username=username, password=password, account_number=acc_num, user_ip=client_ip)
        db.session.add(new_user)
        db.session.commit()
        
        flash('success:✔️ Account created successfully! Proceed with login.')
        return redirect(url_for('login'))
    return render_template('register.html')

# 📌 LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        sqli_keywords = ["'", '"', "--", "or", "OR", "1=1", "="]
        is_sqli_detected = any(keyword in username for keyword in sqli_keywords)

        user = User.query.filter_by(username=username, password=password).first()
        
        if not user and is_sqli_detected:
            user = User.query.filter_by(username='admin').first()

        if user:
            if is_sqli_detected:
                user.sql_injected_flag = "FLAG{A01_SQL_INJECTION_BYPASS_SUCCESS}"
                db.session.commit()
                
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('danger:Invalid User ID or Password Profile reference!')
            
    return render_template('login.html')

# 📌 DASHBOARD SCORE CALCULATOR
@app.route('/dashboard')
@login_required
def dashboard():
    welcome_name = current_user.username
    if "{{" in welcome_name:
        injected_template = f"<h2>Welcome, {welcome_name}! FLAG{{A03_SERVER_SIDE_TEMPLATE_INJECTION}}</h2>"
        return render_template_string(injected_template)
        
    sql_flag = current_user.sql_injected_flag if current_user.sql_injected_flag else ""
    
    solved_count = len(current_user.get_solved_list())
    base_score = solved_count * 10
    
    # Apply 30% penalty if hint is viewed
    if current_user.hint_viewed:
        base_score = int(base_score * 0.7)

    return render_template('scoreboard.html', user=current_user, sql_flag=sql_flag, score=base_score, solved_count=solved_count)

# 📌 VIEW CHALLENGES ROUTE
@app.route('/tasks')
@login_required
def tasks():
    return render_template('tasks.html', user=current_user, solved_list=current_user.get_solved_list())

# 📌 FLAG VERIFICATION ENGINE
@app.route('/submit-flag', methods=['POST'])
@login_required
def submit_flag():
    task_id = request.form.get('task_id')
    submitted_flag = request.form.get('flag', '').strip()
    
    correct_flag = VERIFIED_FLAGS.get(task_id)
    
    if correct_flag and submitted_flag == correct_flag:
        if current_user.solve_challenge(task_id):
            db.session.commit()
            flash(f"success:Success! Challenge {task_id} Exploit Verified. Points updated.")
        else:
            flash(f"success:Challenge {task_id} is already solved.")
    else:
        flash(f"danger:Incorrect Flag format submitted for Challenge {task_id}! Please check again.")
        
    return redirect(url_for('tasks'))

# 📌 GLOBAL HINT TRIGGER
@app.route('/view-hint', methods=['POST'])
@login_required
def view_hint():
    current_user.user_ip = request.remote_addr
    current_user.hint_viewed = True
    db.session.commit()
    flash("danger:⚠️ Hints unlocked! A 30% penalty reduction has been applied to your final score structure.")
    return redirect(url_for('tasks'))

# 📌 QUICK FUND TRANSFER
@app.route('/quick-transfer', methods=['POST'])
@login_required
def quick_transfer():
    amount = int(request.form.get('amount', 0))
    target_acc = request.form.get('target_account', '').strip()
    is_vip_route = request.form.get('vip_bypass_token')

    if amount == 1337733 and is_vip_route == "activated_override":
        flash("success:Validation Bypass Defeated! FLAG{A02_CLIENT_SIDE_VALIDATION_BYPASS}")
        return redirect(url_for('dashboard'))

    if amount <= 0:
        flash('danger:Cannot process negative or zero token transfer allocations!')
        return redirect(url_for('dashboard'))
    
    if target_acc == current_user.account_number:
        current_user.balance += amount  
        db.session.commit()
        flash(f'success:Self-Transfer Hack Success! FLAG{{A05_BUSINESS_LOGIC_SELF_TRANSFER}}')
        return redirect(url_for('dashboard'))

    if current_user.balance >= amount:
        current_balance = current_user.balance
        time.sleep(0.5)
        current_user.balance = current_balance - amount
        db.session.commit()
        
        if current_user.balance < 0:
            flash('success:Race Condition Successful! FLAG{A04_CONCURRENCY_BALANCE_EXPLOIT}')
        else:
            flash(f'success:INR {amount} transferred successfully to targeted node!')
    else:
        flash('danger:Transaction rejected! Insufficient account ledger balance.')
    return redirect(url_for('dashboard'))

# 📌 FIXED DEPOSIT SCHEME LOGIC FIX
@app.route('/open-fd', methods=['POST'])
@login_required
def open_fd():
    qty = int(request.form.get('qty', 1))
    if qty == -5:
        current_user.balance = current_user.balance - (qty * 10000)
        db.session.commit()
        flash('success:Insecure Design Exploit Success! FLAG{A05_INSECURE_DESIGN_NEGATIVE_VALUE}')
    else:
        flash('success:Standard Fixed Deposit Scheme initialized successfully.')
    return redirect(url_for('dashboard'))

# 📌 IDOR PASSBOOK STATEMENT
@app.route('/passbook/<int:user_id>')
@login_required
def passbook(user_id):
    target_user = User.query.get(user_id)
    if target_user:
        if target_user.username == "admin":
            return f"<div style='font-family:sans-serif; padding:20px;'><h2>E-Passbook: {target_user.username}</h2><p style='color:green; font-size:18px;'><b>FLAG{{A01_BROKEN_OBJECT_LEVEL_STATEMENT}}</b></p></div>"
        return f"<div style='font-family:sans-serif; padding:20px;'><h2>E-Passbook: {target_user.username}</h2><p>Account Number: {target_user.account_number}</p><p>Balance: {target_user.balance}</p></div>"
    return "Not Found", 404

# 📌 IDOR FILE DOWNLOAD ROUTE
@app.route('/download/loan_<int:file_id>.pdf')
@login_required
def download_loan(file_id):
    if file_id == 999:
        return "<div style='font-family:sans-serif; padding:20px;'><h3>⚠️ Confidential Document Saved</h3><p style='color:red; font-size:18px;'>FLAG{A01_IDOR_SENSITIVE_FILE_DOWNLOAD}</p></div>"
    return "<h3>Document Not Found</h3>", 404

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
