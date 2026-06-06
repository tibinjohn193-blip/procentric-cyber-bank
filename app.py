from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'local-secure-bank-token-2026'

# Database Configuration
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'indian_bank.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Schema
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=50000) 
    score = db.Column(db.Integer, default=0)
    solved_challenges = db.Column(db.String(500), default="")
    # 💡 പുതിയ ഫീൽഡ്: SQL Injection പേലോഡ് വഴി കേറിയാൽ ഫ്ലാഗ് ഇവിടെ സേവ് ചെയ്യും
    sql_injected_flag = db.Column(db.String(150), default="")

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
        flash('Account created successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')


# 📌 ചലഞ്ച് 1: SQL INJECTION DETECTION (നിങ്ങൾ പറഞ്ഞ പുതിയ സജഷൻ)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 1. കുട്ടികൾ അക്കൗണ്ട് ഉണ്ടാക്കിയ ശേഷം ലോഗിൻ ചെയ്യാൻ നോക്കുമ്പോൾ 
        # ലോഗിൻ ബോക്സിൽ SQL Injection ക്യാരക്ടറുകൾ ഉണ്ടോ എന്ന് സിസ്റ്റം ബാക്കിൽ നോക്കുന്നു.
        sqli_keywords = ["'", '"', "--", "or", "OR", "1=1", "="]
        is_sqli_detected = any(keyword in username for keyword in sqli_keywords)

        # 2. നോർമൽ ലോഗിൻ രീതി (ഇതിനാൽ ഒരിക്കലും ക്രാഷ് ആകില്ല, എറർ വരില്ല)
        user = User.query.filter_by(username=username, password=password).first()
        
        # എറർ വരാതിരിക്കാൻ ഒരു ബാക്കപ്പ് യൂസർ (കുട്ടികൾ സ്വന്തം യൂസർ ഉണ്ടാക്കാതെ പേലോഡ് അടിച്ചാൽ)
        if not user and is_sqli_detected:
            user = User.query.filter_by(username='admin').first()

        if user:
            # 3. 💡 കുട്ടികൾ SQL Injection ട്രൈ ചെയ്തിട്ടുണ്ടെങ്കിൽ ലോഗിൻ ചെയ്യുന്ന യൂസറിന്റെ 
            # പ്രൊഫൈലിലേക്ക് ഓട്ടോമാറ്റിക്കായി ഫ്ലാഗ് ബാക്കെൻഡ് പേസ്റ്റ് ചെയ്തു നൽകുന്നു!
            if is_sqli_detected:
                user.sql_injected_flag = "FLAG{A01_SQL_INJECTION_BYPASS_SUCCESS}"
                db.session.commit()
                
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid User ID or Password!')
            
    return render_template('login.html')


# 📌 ഡാഷ്‌ബോർഡ് & ചലഞ്ച് 8 (SSTI)
@app.route('/dashboard')
@login_required
def dashboard():
    welcome_name = current_user.username
    
    # ചലഞ്ച് 8: SSTI
    if "{{" in welcome_name:
        injected_template = f"<h2>Welcome, {welcome_name}! FLAG{{A03_SERVER_SIDE_TEMPLATE_INJECTION}}</h2>"
        return render_template_string(injected_template)
        
    # ലോഗിൻ ബോക്സിൽ SQL injection പരീക്ഷിച്ച കുട്ടിയാണെങ്കിൽ ഡാഷ്‌ബോർഡിലേക്ക് ഫ്ലാഗ് പാസ്സ് ചെയ്യുന്നു
    sql_flag = current_user.sql_injected_flag if current_user.sql_injected_flag else ""
        
    return render_template('scoreboard.html', user=current_user, sql_flag=sql_flag)


# 📌 ചലഞ്ച് 2, 7 & 9: RACE CONDITION, CLIENT BYPASS & BUSINESS LOGIC
@app.route('/quick-transfer', methods=['POST'])
@login_required
def quick_transfer():
    amount = int(request.form.get('amount', 0))
    target_acc = request.form.get('target_account', '').strip()
    is_vip_route = request.form.get('vip_bypass_token')

    # ചലഞ്ച് 7: ക്ലയന്റ് സൈഡ് വാലിഡേഷൻ ബൈപാസ്സ്
    if amount == 1337733 and is_vip_route == "activated_override":
        flash("Validation Bypass Defeated! FLAG{A02_CLIENT_SIDE_VALIDATION_BYPASS}")
        return redirect(url_for('dashboard'))

    if amount <= 0:
        flash('Cannot process invalid transaction amount!')
        return redirect(url_for('dashboard'))
    
    # ചലഞ്ച് 9: സെൽഫ് ട്രാൻസ്ഫർ ബിസിനസ്സ് ലോജിക് ബഗ്
    if target_acc == current_user.account_number:
        current_user.balance += amount  
        db.session.commit()
        flash(f'Self-Transfer Hack Success! FLAG{{A05_BUSINESS_LOGIC_SELF_TRANSFER}}')
        return redirect(url_for('dashboard'))

    # ചലഞ്ച് 2: റേസ് കണ്ടീഷൻ (Burp Suite റിക്വസ്റ്റ്)
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


# 📌 ചലഞ്ച് 3: ഇൻസെക്യൂർ ഡിസൈൻ (നെഗറ്റീവ് വാല്യൂ കൊടുക്കുമ്പോൾ)
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


# 📌 ചലഞ്ച് 4: IDOR (പാസ്ബുക്ക് ഹാർവെസ്റ്റിംഗ്)
@app.route('/passbook/<int:user_id>')
@login_required
def passbook(user_id):
    target_user = User.query.get(user_id)
    if target_user:
        if target_user.username == "admin":
            return f"<h2>E-Passbook: {target_user.username}</h2><p><b>FLAG{{A01_BROKEN_OBJECT_LEVEL_STATEMENT}}</b></p>"
        return f"<h2>E-Passbook: {target_user.username}</h2>"
    return "Not Found", 404


# 📌 ചലഞ്ച് 5: ഇൻസെക്യൂർ ഫയൽ ഡൗൺലോഡ് IDOR
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
