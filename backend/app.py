from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import os
import random
from datetime import datetime, timedelta

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.secret_key = os.environ.get('EVOCRYPT_SECRET_KEY', 'dev-secret-change-in-production')
CORS(app, supports_credentials=True)

# ---------------------------------------------------------------------------
# Firebase Admin setup
#
# To connect real Firebase Authentication:
#   1. In the Firebase console, go to Project settings > Service accounts
#      and generate a new private key. Save it as:
#      backend/serviceAccountKey.json
#   2. pip install -r requirements.txt
#   3. Fill in frontend/static/js/firebase-config.js with your web app config.
#
# Until serviceAccountKey.json exists, the app falls back to a local demo
# account (admin / password123) so the project still runs out of the box.
# ---------------------------------------------------------------------------
FIREBASE_ENABLED = False
try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth

    cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        FIREBASE_ENABLED = True
        print("[EvoCrypt] Firebase Admin initialized - Firebase auth is LIVE.")
    else:
        print("[EvoCrypt] No serviceAccountKey.json found - running in DEMO auth mode.")
except ImportError:
    print("[EvoCrypt] firebase-admin not installed - running in DEMO auth mode.")

# Demo fallback credentials (used only when Firebase is not configured)
DEMO_USERS = {
    "admin": "password123"
}

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
    return render_template('login.html', firebase_enabled=FIREBASE_ENABLED)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(force=True)

    # --- Path 1: Firebase ID token verification ---
    id_token = data.get('idToken')
    if id_token and FIREBASE_ENABLED:
        try:
            decoded = firebase_auth.verify_id_token(id_token)
            email = decoded.get('email', decoded.get('uid'))
            session['user'] = email
            session['trust_score'] = 88
            session['account'] = new_account_state()
            return jsonify({"success": True, "message": "Login successful", "user": email})
        except Exception as e:
            return jsonify({"success": False, "message": f"Token verification failed: {e}"}), 401

    # --- Path 2: Demo fallback (username/password) ---
    username = data.get('username')
    password = data.get('password')
    if username in DEMO_USERS and DEMO_USERS[username] == password:
        session['user'] = username
        session['trust_score'] = 88
        session['account'] = new_account_state()
        return jsonify({"success": True, "message": "Login successful", "user": username})

    return jsonify({"success": False, "message": "Invalid credentials"}), 401


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
    app.run(debug=True, port=5000)
