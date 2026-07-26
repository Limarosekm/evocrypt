from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# NOTE: set EVOCRYPT_SECRET_KEY in your environment for anything beyond local dev.
app.secret_key = os.environ.get('EVOCRYPT_SECRET_KEY', 'dev-secret-change-in-production')
CORS(app, supports_credentials=True)

# NOTE: DB credentials should come from the environment, not be hardcoded in source.
# Set DATABASE_URL to override; the fallback below is for local dev only.
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:Maya123%23@localhost:5432/evocrypt"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Whether Firebase auth is wired up. Flip this (or drive it from an env var)
# once Firebase is actually configured; the frontend reads it from /api/session.


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

# ---------------------------------------------------------------------------
# Mock banking data (per-session, in-memory only - not persisted anywhere)
# ---------------------------------------------------------------------------
def new_account_state():
    now = datetime.now()
    return {
        "account_number": "**** **** **** 4471",
        "balance": 24318.52,
        "available_credit": 12500.00,
        "transactions": [
            {"id": 1, "merchant": "Payroll Deposit", "amount": 4200.00, "type": "credit",
             "date": (now - timedelta(days=1)).strftime("%b %d")},
            {"id": 2, "merchant": "Green Leaf Grocers", "amount": -86.42, "type": "debit",
             "date": (now - timedelta(days=1)).strftime("%b %d")},
            {"id": 3, "merchant": "Transit Authority", "amount": -32.00, "type": "debit",
             "date": (now - timedelta(days=2)).strftime("%b %d")},
            {"id": 4, "merchant": "Northwind Electric", "amount": -142.19, "type": "debit",
             "date": (now - timedelta(days=3)).strftime("%b %d")},
            {"id": 5, "merchant": "Interest Earned", "amount": 6.11, "type": "credit",
             "date": (now - timedelta(days=5)).strftime("%b %d")},
        ]
    }


@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return render_template('login.html')


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(force=True)

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required."
        }), 400

    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return jsonify({
            "success": False,
            "message": "Username or email already exists."
        }), 400

    hashed_password = generate_password_hash(password)

    user = User(
        username=username,
        email=email,
        password=hashed_password
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Registration successful."
    })


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(force=True)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required."
        }), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        session['user'] = user.username
        session['trust_score'] = 88
        session['account'] = new_account_state()

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "user": user.username
        })

    return jsonify({
        "success": False,
        "message": "Invalid username or password."
    }), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route('/api/session', methods=['GET'])
def session_check():
    if 'user' not in session:
        return jsonify({"authenticated": False}), 401
    return jsonify({
        "authenticated": True,
        "user": session['user'],
        "firebase_enabled": FIREBASE_ENABLED
    })


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('dashboard.html', user=session['user'])


@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    if 'user' not in session:
        return jsonify({"error": "unauthenticated"}), 401
    if 'account' not in session:
        session['account'] = new_account_state()
    return jsonify(session['account'])


@app.route('/api/transfer', methods=['POST'])
def transfer():
    if 'user' not in session:
        return jsonify({"error": "unauthenticated"}), 401

    data = request.get_json(force=True)
    amount = float(data.get('amount', 0))
    recipient = data.get('recipient', 'Unknown')

    if 'account' not in session:
        session['account'] = new_account_state()

    account = session['account']
    if amount <= 0:
        return jsonify({"success": False, "message": "Enter a transfer amount greater than $0.00"}), 400
    if amount > account['balance']:
        return jsonify({"success": False, "message": "Transfer exceeds available balance"}), 400

    account['balance'] = round(account['balance'] - amount, 2)
    account['transactions'].insert(0, {
        "id": len(account['transactions']) + 1,
        "merchant": f"Transfer to {recipient}",
        "amount": -amount,
        "type": "debit",
        "date": datetime.now().strftime("%b %d")
    })
    session['account'] = account

    # Large or unusual transfers nudge the trust score down slightly,
    # simulating a continuous-authentication risk signal.
    trust_delta = -12 if amount > 1000 else -3
    current_score = session.get('trust_score', 88)
    session['trust_score'] = max(10, min(100, current_score + trust_delta))

    return jsonify({"success": True, "account": account, "trust_score": session['trust_score']})


@app.route('/api/trust-score', methods=['GET'])
def get_trust_score():
    if 'user' not in session:
        return jsonify({"error": "unauthenticated"}), 401
    score = session.get('trust_score', 70)
    return jsonify({
        "trust_score": score,
        "status": "High" if score >= 70 else "Medium" if score >= 40 else "Low",
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })


@app.route('/api/update-behavior', methods=['POST'])
def update_behavior():
    if 'user' not in session:
        return jsonify({"error": "unauthenticated"}), 401
    data = request.get_json(force=True)

    current_score = session.get('trust_score', 88)
    change = data.get('change', 0)
    new_score = max(10, min(100, current_score + change))
    session['trust_score'] = new_score

    return jsonify({"new_trust_score": new_score})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # Creates tables if they don't exist

    app.run(debug=True, port=5000)