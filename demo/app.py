import os
import uuid

from datetime import datetime, timedelta

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session
)

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from evocrypt import EvoCrypt
from evocrypt.middleware.flask import init_flask


# ============================================================
# APPLICATION PATHS
# ============================================================

BASE = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    template_folder=os.path.join(BASE, "templates"),
    static_folder=os.path.join(BASE, "static")
)


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app.secret_key = os.environ.get(
    "EVOCRYPT_SECRET_KEY",
    "local-demo-change-me"
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(BASE, "demo.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


CORS(
    app,
    supports_credentials=True
)


db = SQLAlchemy(app)


# ============================================================
# EVOCRYPT FRAMEWORK
# ============================================================
#
# IMPORTANT:
#
# EvoCrypt is imported as a reusable security framework.
#
# The demo application does not implement:
#
#   - trust scoring
#   - RL decisions
#   - key rotation
#   - adaptive security
#
# Those are handled by the package.
# ============================================================

security = EvoCrypt(
    adaptive=True,

    # Set EVOCRYPT_PQC=true when a validated PQC
    # provider has been connected.
    pqc_enabled=(
        os.environ
        .get("EVOCRYPT_PQC", "false")
        .lower() == "true"
    )
)


# Register EvoCrypt with Flask
init_flask(
    app,
    security
)


# Temporary in-memory behavioral collection
session_buffer = {}


# ============================================================
# DATABASE MODELS
# ============================================================

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )


class BehaviorLog(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        nullable=False
    )

    session_id = db.Column(
        db.String(255),
        nullable=False
    )

    typing_speed = db.Column(
        db.Float
    )

    avg_key_hold = db.Column(
        db.Float
    )

    mouse_speed = db.Column(
        db.Float
    )

    mouse_distance = db.Column(
        db.Float
    )

    click_count = db.Column(
        db.Float
    )

    scroll_distance = db.Column(
        db.Float
    )

    idle_time = db.Column(
        db.Float
    )

    screen_width = db.Column(
        db.Integer
    )

    screen_height = db.Column(
        db.Integer
    )

    browser = db.Column(
        db.String(255)
    )

    operating_system = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def avg(values):

    values = [
        float(value)
        for value in values
        if value is not None
    ]

    if not values:
        return 0.0

    return sum(values) / len(values)


def new_account_state():

    now = datetime.now()

    return {
        "account_number": "**** **** **** 4471",

        "balance": 24318.52,

        "available_credit": 12500.00,

        "transactions": [

            {
                "id": 1,
                "merchant": "Payroll Deposit",
                "amount": 4200,
                "type": "credit",
                "date": (
                    now - timedelta(days=1)
                ).strftime("%b %d")
            },

            {
                "id": 2,
                "merchant": "Green Leaf Grocers",
                "amount": -86.42,
                "type": "debit",
                "date": (
                    now - timedelta(days=1)
                ).strftime("%b %d")
            },

            {
                "id": 3,
                "merchant": "Transit Authority",
                "amount": -32,
                "type": "debit",
                "date": (
                    now - timedelta(days=2)
                ).strftime("%b %d")
            },

            {
                "id": 4,
                "merchant": "Northwind Electric",
                "amount": -142.19,
                "type": "debit",
                "date": (
                    now - timedelta(days=3)
                ).strftime("%b %d")
            },

            {
                "id": 5,
                "merchant": "Interest Earned",
                "amount": 6.11,
                "type": "credit",
                "date": (
                    now - timedelta(days=5)
                ).strftime("%b %d")
            }
        ]
    }


def start_buffer(username):

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


def save_completed_session(username):

    buffer = session_buffer.get(
        username
    )

    session_id = session.get(
        "session_id"
    )

    if not buffer or not session_id:
        return

    log = BehaviorLog(

        username=username,

        session_id=session_id,

        typing_speed=avg(
            buffer["typing_speed"]
        ),

        avg_key_hold=avg(
            buffer["avg_key_hold"]
        ),

        mouse_speed=avg(
            buffer["mouse_speed"]
        ),

        mouse_distance=avg(
            buffer["mouse_distance"]
        ),

        click_count=avg(
            buffer["click_count"]
        ),

        scroll_distance=avg(
            buffer["scroll_distance"]
        ),

        idle_time=avg(
            buffer["idle_time"]
        ),

        screen_width=buffer[
            "screen_width"
        ],

        screen_height=buffer[
            "screen_height"
        ],

        browser=buffer[
            "browser"
        ],

        operating_system=buffer[
            "operating_system"
        ]
    )

    db.session.add(log)

    db.session.commit()

    session_buffer.pop(
        username,
        None
    )


# ============================================================
# WEB PAGES
# ============================================================

@app.get("/")
def home():

    if "user" in session:
        return redirect(
            "/dashboard"
        )

    return render_template(
        "login.html"
    )


@app.get("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return render_template(
        "dashboard.html",
        user=session["user"]
    )


# ============================================================
# REGISTRATION
# ============================================================

@app.post("/api/register")
def register():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    username = (
        data.get("username")
        or ""
    ).strip()

    email = (
        data.get("email")
        or ""
    ).strip()

    password = (
        data.get("password")
        or ""
    )

    if not username or not email or not password:

        return jsonify(
            success=False,
            message="All fields are required."
        ), 400

    if len(password) < 6:

        return jsonify(
            success=False,
            message=(
                "Password must contain "
                "at least 6 characters."
            )
        ), 400

    existing_user = User.query.filter(
        (User.username == username)
        |
        (User.email == email)
    ).first()

    if existing_user:

        return jsonify(
            success=False,
            message=(
                "Username or email "
                "already exists."
            )
        ), 400

    user = User(

        username=username,

        email=email,

        password=generate_password_hash(
            password
        )
    )

    db.session.add(user)

    db.session.commit()

    return jsonify(
        success=True,
        message="Registration successful."
    )


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/login")
def login():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    username = (
        data.get("username")
        or ""
    ).strip()

    password = (
        data.get("password")
        or ""
    )

    user = User.query.filter_by(
        username=username
    ).first()

    if (
        not user
        or not check_password_hash(
            user.password,
            password
        )
    ):

        return jsonify(
            success=False,
            message=(
                "Invalid username "
                "or password."
            )
        ), 401

    # Generate a unique application session ID
    session_id = str(
        uuid.uuid4()
    )

    session.clear()

    session["user"] = user.username

    session["session_id"] = session_id

    session["account"] = (
        new_account_state()
    )

    # Start collecting behavioral data
    start_buffer(
        user.username
    )

    # Start EvoCrypt protection
    security_status = (
        security.start_session(
            user.username,
            session_id
        )
    )

    return jsonify(

        success=True,

        message="Login successful.",

        user=user.username,

        security=security_status
    )


# ============================================================
# LOGOUT
# ============================================================

@app.post("/api/logout")
def logout():

    if session.get("user"):

        save_completed_session(
            session["user"]
        )

    session.clear()

    return jsonify(
        success=True
    )


# ============================================================
# ACCOUNT DATA
# ============================================================

@app.get("/api/accounts")
def accounts():

    if "user" not in session:

        return jsonify(
            error="unauthenticated"
        ), 401

    return jsonify(
        session["account"]
    )


# ============================================================
# TRANSFER
# ============================================================

@app.post("/api/transfer")
def transfer():

    if "user" not in session:

        return jsonify(
            error="unauthenticated"
        ), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    try:
        amount = float(
            data.get(
                "amount",
                0
            )
            or 0
        )

    except (TypeError, ValueError):

        return jsonify(
            success=False,
            message="Invalid amount."
        ), 400

    recipient = (
        data.get("recipient")
        or "Unknown"
    ).strip()

    account = session[
        "account"
    ]

    if amount <= 0:

        return jsonify(
            success=False,
            message=(
                "Enter an amount "
                "greater than $0.00"
            )
        ), 400

    if amount > account["balance"]:

        return jsonify(
            success=False,
            message=(
                "Transfer exceeds "
                "available balance"
            )
        ), 400

    # Update demo balance
    account["balance"] = round(
        account["balance"] - amount,
        2
    )

    account["transactions"].insert(

        0,

        {
            "id": len(
                account["transactions"]
            ) + 1,

            "merchant": (
                f"Transfer to {recipient}"
            ),

            "amount": -amount,

            "type": "debit",

            "date": datetime.now().strftime(
                "%b %d"
            )
        }
    )

    session["account"] = account

    # Inform EvoCrypt about transaction risk
    if amount > 1000:

        result = (
            security.apply_external_risk(
                session["session_id"],
                -12,
                "High-value transfer"
            )
        )

    else:

        result = (
            security.apply_external_risk(
                session["session_id"],
                -3,
                "Transfer activity"
            )
        )

    return jsonify(

        success=True,

        account=account,

        security=result
    )


# ============================================================
# TRUST STATUS
# ============================================================

@app.get("/api/trust-score")
def trust_score():

    if "user" not in session:

        return jsonify(
            error="unauthenticated"
        ), 401

    status = security.get_status(
        session["session_id"]
    )

    return jsonify(
        status
    )


# ============================================================
# DEMO ATTACK SIMULATION
# ============================================================

@app.post("/api/update-behavior")
def update_behavior():

    if "user" not in session:

        return jsonify(
            error="unauthenticated"
        ), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    try:

        change = float(
            data.get(
                "change",
                -25
            )
        )

    except (TypeError, ValueError):

        change = -25

    result = (
        security.apply_external_risk(

            session["session_id"],

            change,

            "Simulated session anomaly"
        )
    )

    return jsonify(
        result
    )


# ============================================================
# BEHAVIOR COLLECTION
# ============================================================

@app.post("/api/behavior")
def behavior():

    if "user" not in session:

        return jsonify(
            error="unauthenticated"
        ), 401

    username = session[
        "user"
    ]

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if username not in session_buffer:

        start_buffer(
            username
        )

    buffer = session_buffer[
        username
    ]

    fields = [

        "typing_speed",
        "avg_key_hold",
        "mouse_speed",
        "mouse_distance",
        "click_count",
        "scroll_distance",
        "idle_time"

    ]

    # Store behavioral measurements
    for field in fields:

        value = data.get(
            field
        )

        if value is not None:

            try:

                buffer[field].append(
                    float(value)
                )

            except (TypeError, ValueError):

                pass

    buffer["browser"] = data.get(
        "browser",
        buffer["browser"]
    )

    buffer["operating_system"] = data.get(
        "operating_system",
        buffer["operating_system"]
    )

    buffer["screen_width"] = data.get(
        "screen_width",
        buffer["screen_width"]
    )

    buffer["screen_height"] = data.get(
        "screen_height",
        buffer["screen_height"]
    )

    # Send signals to EvoCrypt
    signals = {
        field: data.get(field)
        for field in fields
    }

    context = {

        "ip_changed": bool(
            data.get("ip_changed")
        ),

        "device_changed": bool(
            data.get("device_changed")
        ),

        "unusual_time": bool(
            data.get("unusual_time")
        ),

        "suspicious": bool(
            data.get("suspicious")
        )
    }

    result = security.record_behavior(

        session["session_id"],

        signals,

        context
    )

    return jsonify(

        success=True,

        security=result
    )


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(
        debug=True,
        port=5000
    )