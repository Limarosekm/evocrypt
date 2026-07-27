from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

# Temporary storage for current login sessions
session_buffer = {}
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
    "postgresql+psycopg://postgres:Lima%402005@localhost:5432/evocrypt"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Whether Firebase auth is wired up. Flip this (or drive it from an env var)
# once Firebase is actually configured; the frontend reads it from /api/session.
import statistics


def avg(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else 0


def create_session_buffer(username):

    session_buffer[username] = {

        "typing_speed": [],

        "avg_key_hold": [],

        "mouse_speed": [],

        "mouse_distance": [],

        "click_count": [],

        "scroll_distance": [],

        "idle_time": [],

        "browser": "",

        "operating_system": "",

        "screen_width": 0,

        "screen_height": 0,

        "login_time": datetime.utcnow()
    }

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"
class BehaviorLog(db.Model):
    __tablename__ = "behavior_logs"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), nullable=False)
    session_id = db.Column(db.String(255), nullable=False)

    typing_speed = db.Column(db.Float)
    avg_key_hold = db.Column(db.Float)

    mouse_speed = db.Column(db.Float)
    mouse_distance = db.Column(db.Float)

    click_count = db.Column(db.Integer)
    scroll_distance = db.Column(db.Float)

    idle_time = db.Column(db.Float)

    screen_width = db.Column(db.Integer)
    screen_height = db.Column(db.Integer)

    browser = db.Column(db.String(255))
    operating_system = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
class UserBehaviorProfile(db.Model):
    __tablename__ = "user_behavior_profile"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    # Learning progress
    sessions_completed = db.Column(db.Integer, default=0)
    profile_status = db.Column(db.String(20), default="LEARNING")
    learning_complete = db.Column(db.Boolean, default=False)

    # Average behavioral values
    avg_typing_speed = db.Column(db.Float)
    avg_key_hold = db.Column(db.Float)
    avg_mouse_speed = db.Column(db.Float)
    avg_mouse_distance = db.Column(db.Float)
    avg_click_count = db.Column(db.Float)
    avg_scroll_distance = db.Column(db.Float)
    avg_idle_time = db.Column(db.Float)

    # Usual contextual data
    usual_browser = db.Column(db.String(100))
    usual_operating_system = db.Column(db.String(100))
    usual_screen_width = db.Column(db.Integer)
    usual_screen_height = db.Column(db.Integer)

    # We will add these later
    usual_device_fingerprint = db.Column(db.String(255))
    usual_ip = db.Column(db.String(100))
    usual_city = db.Column(db.String(100))
    usual_country = db.Column(db.String(100))
    usual_login_hour = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
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

    profile = UserBehaviorProfile(
        username=username,
        sessions_completed=0,
        profile_status="LEARNING",
        learning_complete=False
    )

    db.session.add(user)
    db.session.add(profile)
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

        session['session_id'] = str(uuid.uuid4())

        session['trust_score'] = 88

        session['account'] = new_account_state()
        create_session_buffer(user.username)

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "user": user.username
        })

    return jsonify({
        "success": False,
        "message": "Invalid username or password."
    }), 401


@app.route("/api/logout", methods=["POST"])
def logout():

    if "user" in session:
        save_completed_session(session["user"])

    session.clear()

    return jsonify({
        "success": True
    })


@app.route('/api/session', methods=['GET'])
def session_check():
    if 'user' not in session:
        return jsonify({"authenticated": False}), 401
    return jsonify({
    "authenticated": True,
    "user": session['user']
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
@app.route("/api/behavior", methods=["POST"])
def save_behavior():

    if "user" not in session:
        return jsonify({"error": "unauthenticated"}), 401

    username = session["user"]

    if username not in session_buffer:
        create_session_buffer(username)

    data = request.get_json(force=True)

    buffer = session_buffer[username]

    if data.get("typing_speed") is not None:
        buffer["typing_speed"].append(float(data["typing_speed"]))

    if data.get("avg_key_hold") is not None:
        buffer["avg_key_hold"].append(float(data["avg_key_hold"]))

    if data.get("mouse_speed") is not None:
        buffer["mouse_speed"].append(float(data["mouse_speed"]))

    if data.get("mouse_distance") is not None:
        buffer["mouse_distance"].append(float(data["mouse_distance"]))

    if data.get("click_count") is not None:
        buffer["click_count"].append(float(data["click_count"]))

    if data.get("scroll_distance") is not None:
        buffer["scroll_distance"].append(float(data["scroll_distance"]))

    if data.get("idle_time") is not None:
        buffer["idle_time"].append(float(data["idle_time"]))

    buffer["browser"] = data.get("browser")

    buffer["operating_system"] = data.get("operating_system")

    buffer["screen_width"] = data.get("screen_width")

    buffer["screen_height"] = data.get("screen_height")

    return jsonify({"success": True})
@app.route("/api/behavior", methods=["GET"])
def get_behavior():

    if 'user' not in session:
        return jsonify({"error": "unauthenticated"}), 401

    logs = BehaviorLog.query.filter_by(
        username=session["user"]
    ).order_by(
        BehaviorLog.created_at.desc()
    ).limit(20).all()

    result = []

    for log in logs:

        result.append({

            "typing_speed": log.typing_speed,

            "mouse_speed": log.mouse_speed,

            "click_count": log.click_count,

            "idle_time": log.idle_time,

            "browser": log.browser,

            "time": log.created_at.strftime("%H:%M:%S")

        })

    return jsonify(result)
def save_completed_session(username):

    if username not in session_buffer:
        return

    buffer = session_buffer[username]

    duration = (
        datetime.utcnow() -
        buffer["login_time"]
    ).total_seconds()

    behavior = BehaviorLog(

        username=username,

        session_id=session["session_id"],

        typing_speed=avg(buffer["typing_speed"]),

        avg_key_hold=avg(buffer["avg_key_hold"]),

        mouse_speed=avg(buffer["mouse_speed"]),

        mouse_distance=avg(buffer["mouse_distance"]),

        click_count=int(avg(buffer["click_count"])),

        scroll_distance=avg(buffer["scroll_distance"]),

        idle_time=avg(buffer["idle_time"]),

        screen_width=buffer["screen_width"],

        screen_height=buffer["screen_height"],

        browser=buffer["browser"],

        operating_system=buffer["operating_system"]

    )

    db.session.add(behavior)
    db.session.commit()

    # Count this completed login session
    increment_learning(username)

    # Clear temporary buffer
    if username in session_buffer:
        del session_buffer[username]
def get_profile(username):

    profile = UserBehaviorProfile.query.filter_by(
        username=username
    ).first()

    if profile is None:

        profile = UserBehaviorProfile(
            username=username,
            sessions_completed=0,
            profile_status="LEARNING",
            learning_complete=False
        )

        db.session.add(profile)
        db.session.commit()

    return profile


def increment_learning(username):

    profile = get_profile(username)

    profile.sessions_completed += 1

    db.session.commit()

    if profile.sessions_completed >= 10:
        generate_profile(username)
def generate_profile(username):

    logs = BehaviorLog.query.filter_by(
        username=username
    ).all()

    if len(logs) < 10:
        return

    profile = get_profile(username)

    profile.avg_typing_speed = avg([x.typing_speed for x in logs])
    profile.avg_key_hold = avg([x.avg_key_hold for x in logs])
    profile.avg_mouse_speed = avg([x.mouse_speed for x in logs])
    profile.avg_mouse_distance = avg([x.mouse_distance for x in logs])
    profile.avg_click_count = avg([x.click_count for x in logs])
    profile.avg_scroll_distance = avg([x.scroll_distance for x in logs])
    profile.avg_idle_time = avg([x.idle_time for x in logs])

    latest = logs[-1]

    profile.usual_browser = latest.browser
    profile.usual_operating_system = latest.operating_system
    profile.usual_screen_width = latest.screen_width
    profile.usual_screen_height = latest.screen_height

    profile.learning_complete = True
    profile.profile_status = "READY"

    db.session.commit()
if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # Creates tables if they don't exist

    app.run(debug=True, port=5000)