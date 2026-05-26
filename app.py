from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-12345'

instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'bank.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

stock = 5

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    balance = db.Column(db.Integer, default=5000)
    score = db.Column(db.Integer, default=0)
    solved_challenges = db.Column(db.String(500), default="")
    feedback = db.Column(db.String(500), default="No feedback submitted yet.") # XSS ഒളിപ്പിക്കാൻ

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- Routes ---
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/robots.txt')
def robots():
    # Challenge 8: Sensitive Data Exposure via robots.txt
    return "User-agent: *\nDisallow: /secret-audit-vault-backup/\n"

@app.route('/secret-audit-vault-backup/')
def secret_vault():
    return "<h1>🔒 Secure Audit Vault</h1><p>FLAG{A05_SENSITIVE_DATA_ROBOTS_TXT_EXPOSURE}</p>"

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
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # SQLi Vulnerability
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('scoreboard'))
        else:
            flash('Invalid professional credentials.')
            
    return render_template('login.html')

@app.route('/scoreboard', methods=['GET', 'POST'])
@login_required
def scoreboard():
    # Challenge 6: Stored XSS (Feedback Form)
    if request.method == 'POST' and request.form.get('feedback_text'):
        current_user.feedback = request.form.get('feedback_text')
        db.session.commit()
        flash('Feedback submitted successfully!')

    users = User.query.order_by(User.score.desc()).all()
    is_admin = request.cookies.get('role') == 'admin'
    return render_template('scoreboard.html', users=users, stock=stock, is_admin=is_admin)

@app.route('/instant-withdraw', methods=['POST'])
@login_required
def instant_withdraw():
    amount = int(request.form.get('amount', 0))
    if amount <= 0:
        flash('Invalid transaction capital value.')
        return redirect(url_for('scoreboard'))
        
    if current_user.balance >= amount:
        import time
        current_balance = current_user.balance
        time.sleep(0.5) 
        current_user.balance = current_balance - amount
        db.session.commit()
        flash(f'Settlement of INR {amount} completed successfully!')
    else:
        flash('Insufficient liquidity in current corporate profile.')
        
    return redirect(url_for('scoreboard'))

@app.route('/buy-gift', methods=['POST'])
@login_required
def buy_gift():
    global stock
    qty = int(request.form.get('qty', 1))
    cost = qty * 10000
    
    if current_user.balance >= cost and stock >= qty:
        current_user.balance -= cost
        stock -= qty
        db.session.commit()
        flash('Asset procurement order successful!')
    else:
        flash('Order rejected: Asset valuation limits or stock failure.')
        
    return redirect(url_for('scoreboard'))

@app.route('/statement/<int:user_id>')
@login_required
def statement(user_id):
    target_user = User.query.get_or_400(user_id)
    return f"<h1>Official Statement Profile Ledger</h1><p>Client: {target_user.username}</p><p>Liquidity: INR {target_user.balance}</p>"

@app.route('/ping-server', methods=['POST'])
@login_required
def ping_server():
    # Challenge 7: OS Command Injection
    ip_address = request.form.get('ip_address', '')
    if ip_address:
        try:
            # Intentional vulnerable execution (shell=True)
            command = f"ping -c 1 {ip_address}"
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            return f"<h3>Network Diagnostics Result:</h3><pre>{output}</pre><a href='/scoreboard'>Back to Dashboard</a>"
        except Exception as e:
            return f"<h3>Execution Failure:</h3><pre>{str(e)}</pre><a href='/scoreboard'>Back to Dashboard</a>"
    return redirect(url_for('scoreboard'))

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
        "integrity": "FLAG{A08_INSECURE_COOKIE_DESERIALIZATION_ADMIN}",
        "xss": "FLAG{A03_STORED_CROSS_SITE_SCRIPTING_ALERT}",
        "cmd_i": "FLAG{A03_COMMAND_INJECTION_SERVER_TAKEOVER}",
        "robots": "FLAG{A05_SENSITIVE_DATA_ROBOTS_TXT_EXPOSURE}"
    }
    
    if challenge_id in flags and flags[challenge_id] == flag_submitted:
        solved_list = current_user.solved_challenges.split(',') if current_user.solved_challenges else []
        if challenge_id not in solved_list:
            solved_list.append(challenge_id)
            current_user.solved_challenges = ','.join(solved_list)
            current_user.score += 100
            db.session.commit()
            flash('Flag validated successfully! +100 Points added.')
        else:
            flash('This flag was already submitted by your profile.')
    else:
        flash('Invalid flag signature payload.')
        
    return redirect(url_for('scoreboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
