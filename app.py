import logging
import math
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from detector import build_alert_message, classify_severity, detect_impact

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = BASE_DIR / "emergency.db"
LOGGER = logging.getLogger("emergency_response")


def _connect(path: Path | str):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def bootstrap_database(db):
    """Reset the demonstration schema and load deterministic seed data."""
    for filename in ("schema.sql", "seed.sql"):
        path = BASE_DIR / filename
        if path.exists():
            db.executescript(path.read_text(encoding="utf-8"))
    db.commit()


def ensure_demo_users(db, admin_password: str, responder_password: str):
    users = [
        ("admin", admin_password, "ADMIN"),
        ("responder", responder_password, "RESPONDER"),
    ]
    with db:
        for username, password, role in users:
            password_hash = generate_password_hash(password)
            existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing is None:
                db.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash, role),
                )
            else:
                db.execute(
                    "UPDATE users SET password_hash = ?, role = ?, active = 1 WHERE username = ?",
                    (password_hash, role, username),
                )


def get_db():
    if "db" not in g:
        g.db = _connect(current_app.config["DATABASE"])
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_database(app):
    path = Path(app.config["DATABASE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as db:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='incidents'"
        ).fetchone()
        if exists is None:
            bootstrap_database(db)
        ensure_demo_users(
            db,
            app.config["DEMO_ADMIN_PASSWORD"],
            app.config["DEMO_RESPONDER_PASSWORD"],
        )


def validate_incident_input(latitude, longitude, impact_g, motion_value):
    if any(value is None for value in (latitude, longitude, impact_g)):
        return "Latitude, longitude and impact are required."
    if not all(math.isfinite(float(value)) for value in (latitude, longitude, impact_g)):
        return "Latitude, longitude and impact must be finite numbers."
    if not -90 <= float(latitude) <= 90:
        return "Latitude must be between -90 and 90."
    if not -180 <= float(longitude) <= 180:
        return "Longitude must be between -180 and 180."
    if not 0 <= float(impact_g) <= 100:
        return "Impact must be between 0 and 100 g."
    if motion_value not in {"yes", "no"}:
        return "Motion must be either yes or no."
    return None


def _coerce_incident(payload):
    try:
        latitude = float(payload.get("latitude"))
        longitude = float(payload.get("longitude"))
        impact_g = float(payload.get("impact_g"))
    except (TypeError, ValueError):
        return (
            None,
            None,
            None,
            payload.get("motion_after_impact"),
            "Latitude, longitude and impact must be numbers.",
        )
    motion_value = str(payload.get("motion_after_impact", "yes")).lower()
    return latitude, longitude, impact_g, motion_value, validate_incident_input(
        latitude, longitude, impact_g, motion_value
    )


def insert_incident(db, latitude, longitude, impact_g, motion_value):
    motion_after_impact = motion_value == "yes"
    severity = classify_severity(impact_g, motion_after_impact)
    with db:
        cursor = db.execute(
            """
            INSERT INTO incidents (latitude, longitude, impact_g, motion_after_impact, severity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (latitude, longitude, impact_g, int(motion_after_impact), severity),
        )
        incident_id = cursor.lastrowid
        message = build_alert_message(incident_id, severity, latitude, longitude)
        db.execute(
            "INSERT INTO alerts (incident_id, recipient, channel, message) VALUES (?, ?, ?, ?)",
            (incident_id, "demo-responder", "SIMULATED", message),
        )
    LOGGER.info("incident_created incident_id=%s severity=%s", incident_id, severity)
    LOGGER.info("alert_created incident_id=%s channel=SIMULATED", incident_id)
    return incident_id, severity


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=Path(os.getenv("EMERGENCY_DATABASE", DEFAULT_DATABASE)),
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-emergency-secret"),
        API_KEY=os.getenv("EMERGENCY_API_KEY", "demo-emergency-api-key"),
        DEMO_ADMIN_PASSWORD=os.getenv("DEMO_ADMIN_PASSWORD", "admin-demo"),
        DEMO_RESPONDER_PASSWORD=os.getenv("DEMO_RESPONDER_PASSWORD", "responder-demo"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)

    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    LOGGER.setLevel(log_level)

    app.teardown_appcontext(close_db)
    ensure_database(app)

    def current_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        return get_db().execute(
            "SELECT id, username, role FROM users WHERE id = ? AND active = 1", (user_id,)
        ).fetchone()

    def csrf_token():
        token = session.get("_csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["_csrf_token"] = token
        return token

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_user() is None:
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)

        return wrapped

    def role_required(*roles):
        def decorator(view):
            @wraps(view)
            def wrapped(*args, **kwargs):
                user = current_user()
                if user is None:
                    return redirect(url_for("login", next=request.path))
                if user["role"] not in roles:
                    abort(403)
                return view(*args, **kwargs)

            return wrapped

        return decorator

    @app.before_request
    def protect_form_posts():
        # Login is intentionally exempt for the public portfolio demo. This avoids
        # stale CSRF/session cookies causing a 400 immediately after a Render
        # redeploy. Authenticated state-changing routes remain CSRF protected.
        if request.endpoint == "login":
            return None
        if request.method == "POST" and not request.is_json:
            expected = session.get("_csrf_token")
            supplied = request.form.get("csrf_token")
            if not expected or not supplied or not secrets.compare_digest(expected, supplied):
                abort(400, description="Invalid CSRF token")
        return None

    @app.context_processor
    def inject_security_context():
        return {"csrf_token": csrf_token, "current_user": current_user()}

    @app.cli.command("init-db")
    def init_db_command():
        db = get_db()
        bootstrap_database(db)
        ensure_demo_users(
            db,
            current_app.config["DEMO_ADMIN_PASSWORD"],
            current_app.config["DEMO_RESPONDER_PASSWORD"],
        )
        print("Emergency response database reset and initialised.")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip().lower()
            password = request.form.get("password", "")
            user = get_db().execute(
                "SELECT * FROM users WHERE username = ? AND active = 1", (username,)
            ).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                csrf_token()
                next_url = request.args.get("next")
                if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect(url_for("index"))
            flash("Invalid username or password.", "error")
        csrf_token()
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def index():
        db = get_db()
        incidents = db.execute(
            "SELECT * FROM incidents ORDER BY created_at DESC, id DESC"
        ).fetchall()
        summary = db.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) AS open_count,
                   SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved_count,
                   SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count
            FROM incidents
            """
        ).fetchone()
        return render_template("index.html", incidents=incidents, summary=summary)

    @app.post("/incident")
    @role_required("ADMIN", "RESPONDER")
    def create_incident():
        latitude, longitude, impact_g, motion_value, error = _coerce_incident(request.form)
        if error:
            flash(error, "error")
            return redirect(url_for("index"))
        incident_id, severity = insert_incident(
            get_db(), latitude, longitude, impact_g, motion_value
        )
        flash(f"Incident #{incident_id} recorded as {severity}.", "success")
        return redirect(url_for("index"))

    @app.post("/incident/<int:incident_id>/resolve")
    @role_required("ADMIN", "RESPONDER")
    def resolve_incident(incident_id):
        db = get_db()
        with db:
            cursor = db.execute(
                "UPDATE incidents SET status = 'RESOLVED' WHERE id = ? AND status != 'RESOLVED'",
                (incident_id,),
            )
        if cursor.rowcount == 0:
            flash("Incident was not found or was already resolved.", "error")
        else:
            LOGGER.info("incident_resolved incident_id=%s", incident_id)
            flash(f"Incident #{incident_id} marked resolved.", "success")
        return redirect(url_for("index"))

    @app.get("/api/incidents")
    @login_required
    def api_incidents():
        rows = get_db().execute(
            "SELECT * FROM incidents ORDER BY created_at DESC, id DESC"
        ).fetchall()
        incidents = []
        for row in rows:
            item = dict(row)
            item["motion_after_impact"] = bool(item["motion_after_impact"])
            incidents.append(item)
        return jsonify({"count": len(incidents), "incidents": incidents})

    @app.post("/api/incidents")
    def api_create_incident():
        user = current_user()
        supplied_api_key = request.headers.get("X-API-Key", "")
        valid_api_key = secrets.compare_digest(supplied_api_key, current_app.config["API_KEY"])
        if not valid_api_key and not (user and user["role"] == "ADMIN"):
            return jsonify({"error": "authentication required"}), 401
        payload = request.get_json(silent=True) or {}
        latitude, longitude, impact_g, motion_value, error = _coerce_incident(payload)
        if error:
            return jsonify({"error": error}), 400
        incident_id, severity = insert_incident(
            get_db(), latitude, longitude, impact_g, motion_value
        )
        return jsonify({"id": incident_id, "severity": severity, "status": "OPEN"}), 201

    @app.post("/api/detect")
    def api_detect():
        payload = request.get_json(silent=True) or {}
        try:
            result = detect_impact(
                payload.get("samples", []),
                spike_threshold_g=payload.get("spike_threshold_g", 1.5),
            )
        except (TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        if result["triggered"]:
            motion = str(payload.get("motion_after_impact", "yes")).lower()
            if motion not in {"yes", "no"}:
                return jsonify({"error": "motion_after_impact must be yes or no"}), 400
            result["severity"] = classify_severity(result["impact_delta_g"], motion == "yes")
        else:
            result["severity"] = "NONE"
        return jsonify(result)

    @app.get("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return jsonify({"status": "ok", "service": "automated-emergency-response-system"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
