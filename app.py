from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'local-secure-bank-token-2026'

instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'indian_bank.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# IP അടിസ്ഥാനമാക്കി ഹിന്റ് ലോക്ക് ചെയ്യാനുള്ള പുതിയ ടേബിൾ
class HintLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=False)
    challenge_id = db.Column(db.String(50), nullable=False)

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
        new_admin = User(username='admin', password='admin_vault_secure_pass_2026', account_number='999123456789')
        db.session.add(new_admin)
        db.session.commit()

with app.app_context():
    db.create_all()
    create_default_admin()

def generate_acc_num(username):
    import hashlib
    hash_val = hashlib.md5(username.encode()).hexdigest()
    return "999" + str(int(hash_val, 16))[:9]

# യൂസറുടെ IP കണ്ടുപിടിക്കാനുള്ള ഫങ്ക്ഷൻ
def get_client_ip():
    return request.remote_addr

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
        flash('Account created successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
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
    if "{{" in welcome_name and "user" in welcome_name:
        welcome_name = "SYSTEM_KEY_7733 (FLAG{A03_SERVER_SIDE_TEMPLATE_INJECTION})"
    return render_template('scoreboard.html', user=current_user, welcome_name=welcome_name)

@app.route('/tasks')
@login_required
def tasks():
    users = User.query.order_by(User.score.desc()).all()
    
    # ഈ ഐപിയിൽ ഏതൊക്കെ ഹിന്റുകൾ തുറന്നു എന്ന് ചെക്ക് ചെയ്യുന്നു
    client_ip = get_client_ip()
    opened_hints = [log.challenge_id for log in HintLog.query.filter_by(ip_address=client_ip).all()]
    
    return render_template('tasks.html', users=users, current_user=current_user, opened_hints=opened_hints)

# ഹിന്റ് ക്ലിക്ക് ചെയ്യുമ്പോൾ IP രജിസ്റ്റർ ചെയ്യാനുള്ള റൂട്ട്
@app.route('/unlock-hint', methods=['POST'])
@login_required
def unlock_hint():
    challenge_id = request.form.get('challenge_id')
    client_ip = get_client_ip()
    
    # ഈ ഐപിയിൽ ഇതിനുമുമ്പ് ഈ ഹിന്റ് ലോഗ് ചെയ്തിട്ടില്ലെങ്കിൽ മാത്രം സേവ് ചെയ്യുക
    existing = HintLog.query.filter_by(ip_address=client_ip, challenge_id=challenge_id).first()
    if not existing:
        new_log = HintLog(ip_address=client_ip, challenge_id=challenge_id)
        db.session.add(new_log)
        db.session.commit()
    
    return redirect(url_for('tasks'))

@app.route('/quick-transfer', methods=['POST'])
@login_required
def quick_transfer():
    amount = int(request.form.get('amount', 0))
    target_acc = request.form.get('target_account', '').strip()
    is_vip_route = request.form.get('vip_bypass_token')

    if amount == 1337733 and is_vip_route == "activated_override":
        flash("Validation Bypass Defeated! FLAG{A02_CLIENT_SIDE_VALIDATION_BYPASS}")
        return redirect(url_for('dashboard'))

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
        flash(f'INR {amount} transferred successfully!')
    return redirect(url_for('dashboard'))

@app.route('/open-fd', methods=['POST'])
@login_required
def open_fd():
    qty = int(request.form.get('qty', 1))
    
    if qty == -5:
        current_user.balance -= (qty * 10000) 
        db.session.commit()
        flash('Insecure Design Exploit Success! FLAG{A05_INSECURE_DESIGN_NEGATIVE_VALUE}')
        return redirect(url_for('dashboard'))
    elif qty < 0:
        current_user.balance -= (qty * 10000)
        db.session.commit()
        flash('ബാലൻസ് കൂടിയിട്ടുണ്ട്! പക്ഷേ ഫ്ലാഗ് ലഭിക്കാനുള്ള കൃത്യമായ വാല്യൂ ഇതല്ല.')
        return redirect(url_for('dashboard'))

    cost = qty * 10000
    if current_user.balance >= cost:
        current_user.balance -= cost
        db.session.commit()
        flash('Fixed Deposit opened successfully!')
    return redirect(url_for('dashboard'))

@app.route('/passbook/<int:user_id>')
@login_required
def passbook(user_id):
    target_user = User.query.get_or_404(user_id)
    return f"<h2>E-Passbook Ledger Holder: {target_user.username}</h2><p>Balance: ₹ {target_user.balance}</p>"

@app.route('/download/loan_<int:file_id>.pdf')
@login_required
def download_loan(file_id):
    if file_id == 101:
        return "<h3>Standard Loan Receipt #101</h3><p>File is empty.</p>"
    elif file_id == 999:
        return "<h3>⚠️ IDB Corporate Confidential Loan Scheme #999</h3><p>FLAG{A01_IDOR_SENSITIVE_FILE_DOWNLOAD}</p>"
    return "<h3>Error 404</h3>"

@app.route('/submit-flag', methods=['POST'])
@login_required
def submit_flag():
    challenge_id = request.form.get('challenge_id')
    flag_submitted = request.form.get('flag', '').strip()
    client_ip = get_client_ip()
    
    flags = {
        "sql_i": "FLAG{A01_SQL_INJECTION_BYPASS_SUCCESS}",
        "race_cond": "FLAG{A04_CONCURRENCY_BALANCE_EXPLOIT}",
        "design_stock": "FLAG{A05_INSECURE_DESIGN_NEGATIVE_VALUE}",
        "idor": "FLAG{A01_BROKEN_OBJECT_LEVEL_STATEMENT}",
        "file_download": "FLAG{A01_IDOR_SENSITIVE_FILE_DOWNLOAD}",
        "crypto_leak": "FLAG{A02_CRYPTO_HASH_DECRYPTION_SUCCESS}",
        "client_bypass": "FLAG{A02_CLIENT_SIDE_VALIDATION_BYPASS}",
        "ssti_leak": "FLAG{A03_SERVER_SIDE_TEMPLATE_INJECTION}",
        "logic_flaw": "FLAG{A05_BUSINESS_LOGIC_SELF_TRANSFER}"
    }
    
    if challenge_id in flags and flags[challenge_id] == flag_submitted:
        solved_list = current_user.solved_challenges.split(',') if current_user.solved_challenges else []
        if challenge_id not in solved_list:
            solved_list.append(challenge_id)
            
            # IP അഡ്രസ് ചെക്ക് ചെയ്ത് സ്കോർ നിശ്ചയിക്കുന്നു
            hint_used = HintLog.query.filter_by(ip_address=client_ip, challenge_id=challenge_id).first()
            points_awarded = 70 if hint_used else 100
            
            current_user.score += points_awarded
            current_user.solved_challenges = ','.join(solved_list)
            db.session.commit()
            flash(f'Correct flag submitted! +{points_awarded} Points.')
        else:
            flash('This challenge was already solved.')
    else:
        flash('Invalid flag signature!')
    return redirect(url_for('tasks'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ലോക്കൽ മെഷീനിൽ റൺ ചെയ്യാനുള്ള മെയിൻ ബ്ലോക്ക്
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
