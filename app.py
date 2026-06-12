from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import time
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secure-local-banking-key-2026'

# Establish database storage path
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'bank_system.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Global Reference Table for validation
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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=50000)
    sql_injected_flag = db.Column(db.String(150), default="")
    solved_challenges = db.Column(db.String(300), default="[]")
    used_hints = db.Column(db.String(300), default="[]") # Tracks penalizations

    def get_solved_list(self):
        try: return json.loads(self.solved_challenges)
        except: return []

    def get_hints_list(self):
        try: return json.loads(self.used_hints)
        except: return []

    def solve_challenge(self, chal_id):
        solved = self.get_solved_list()
        if chal_id not in solved:
            solved.append(chal_id)
            self.solved_challenges = json.dumps(solved)
            return True
        return False

    def use_hint(self, chal_id):
        hints = self.get_hints_list()
        if chal_id not in hints:
            hints.append(chal_id)
            self.used_hints = json.dumps(hints)
            return True
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password='vault_secure_pass_2026', account_number='999123456789', balance=999999))
        db.session.commit()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('danger:Username taken!')
            return redirect(url_for('register'))
        import hashlib
        acc_num = "999" + str(int(hashlib.md5(username.encode()).hexdigest(), 16))[:9]
        db.session.add(User(username=username, password=password, account_number=acc_num))
        db.session.commit()
        flash('success:Account initialized successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        sqli = any(k in username for k in ["'", '"', "--", "or", "OR", "1=1"])
        
        user = User.query.filter_by(username=username, password=password).first()
        if not user and sqli:
            user = User.query.filter_by(username='admin').first()
            
        if user:
            if sqli:
                user.sql_injected_flag = "FLAG{A01_SQL_INJECTION_BYPASS_SUCCESS}"
                db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('danger:Access Denied!')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if "{{" in current_user.username:
        return render_template_string(f"<h2>Welcome back! FLAG{{A03_SERVER_SIDE_TEMPLATE_INJECTION}}</h2>")
    
    solved_list = current_user.get_solved_list()
    hints_list = current_user.get_hints_list()
    
    # 30% Deduction Applied: Normal = 10 pts, Penalty = 7 pts
    total_score = 0
    for chal in solved_list:
        if chal in hints_list:
            total_score += 7
        else:
            total_score += 10

    return render_template('scoreboard.html', user=current_user, sql_flag=current_user.sql_injected_flag, score=total_score, solved_count=len(solved_list))

@app.route('/tasks')
@login_required
def tasks():
    return render_template('tasks.html', user=current_user, solved_list=current_user.get_solved_list(), hints_list=current_user.get_hints_list())

@app.route('/unlock-hint', methods=['POST'])
@login_required
def unlock_hint():
    task_id = request.form.get('task_id')
    if current_user.use_hint(task_id):
        db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/submit-flag', methods=['POST'])
@login_required
def submit_flag():
    task_id = request.form.get('task_id')
    submitted = request.form.get('flag', '').strip()
    if submitted == VERIFIED_FLAGS.get(task_id):
        if current_user.solve_challenge(task_id):
            db.session.commit()
            flash(f"success:Task {task_id} cleared!")
        else:
            flash(f"success:Task already registered.")
    else:
        flash(f"danger:Incorrect flag string for Task {task_id}!")
    return redirect(url_for('tasks'))

@app.route('/quick-transfer', methods=['POST'])
@login_required
def quick_transfer():
    amount = int(request.form.get('amount', 0))
    target_acc = request.form.get('target_account', '').strip()
    if amount == 1337733 and request.form.get('vip_bypass_token') == "activated_override":
        flash("success:Bypass! FLAG{A02_CLIENT_SIDE_VALIDATION_BYPASS}")
    elif amount <= 0:
        flash('danger:Value rejected!')
    elif target_acc == current_user.account_number:
        current_user.balance += amount
        db.session.commit()
        flash(f"success:Loop verified! FLAG{{A05_BUSINESS_LOGIC_SELF_TRANSFER}}")
    elif current_user.balance >= amount:
        time.sleep(0.5)
        current_user.balance -= amount
        db.session.commit()
        if current_user.balance < 0:
            flash('success:Race Condition! FLAG{A04_CONCURRENCY_BALANCE_EXPLOIT}')
    return redirect(url_for('dashboard'))

@app.route('/open-fd', methods=['POST'])
@login_required
def open_fd():
    qty = int(request.form.get('qty', 1))
    if qty == -5:
        current_user.balance -= (qty * 10000)
        db.session.commit()
        flash('success:Vulnerability found! FLAG{A05_INSECURE_DESIGN_NEGATIVE_VALUE}')
    return redirect(url_for('dashboard'))

@app.route('/passbook/<int:user_id>')
@login_required
def passbook(user_id):
    target = User.query.get(user_id)
    if target and target.username == "admin":
        return f"<h2>FLAG{{A01_BROKEN_OBJECT_LEVEL_STATEMENT}}</h2>"
    return "Profile loaded", 200

@app.route('/download/loan_<int:file_id>.pdf')
@login_required
def download_loan(file_id):
    if file_id == 999:
        return "<h3>FLAG{A01_IDOR_SENSITIVE_FILE_DOWNLOAD}</h3>"
    return "Not Found", 404

@app.route('/staging-v1')
@login_required
def staging_v1():
    return f"<h2>FLAG{{A05_MISSING_ACCESS_CONTROL_ROUTING}}</h2>"

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
