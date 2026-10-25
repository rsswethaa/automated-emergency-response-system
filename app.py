import math
import os
from pathlib import Path
import sqlite3

from flask import Flask, current_app, flash, g, jsonify, redirect, render_template, request, url_for

from detector import build_alert_message, classify_severity, detect_impact

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = BASE_DIR / "emergency.db"


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


def get_db():
    """Return one SQLite connection per Flask application context."""
    if "db" not in g:
        g.db = _connect(current_app.config["DATABASE"])
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_database(app):
    """Initialise once at application startup rather than seeding on requests."""
    path = Path(app.config["DATABASE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as db:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='incidents'"
        ).fetchone()
        if exists is None:
            bootstrap_database(db)


def validate_incident_input(latitude, longitude, impact_g, motion_value):
    """Return an error message for invalid incident data, otherwise ``None``."""
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
        return None, None, None, payload.get("motion_after_impact"), "Latitude, longitude and impact must be numbers."
    motion_value = str(payload.get("motion_after_impact", "yes")).lower()
    return latitude, longitude, impact_g, motion_value, validate_incident_input(
        latitude, longitude, impact_g, motion_value
    )


def insert_incident(db, latitude, longitude, impact_g, motion_value):
    """Insert one incident and its alert atomically and return the record id/severity."""
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
    return incident_id, severity


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=Path(os.getenv("EMERGENCY_DATABASE", DEFAULT_DATABASE)),
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-emergency-secret"),
    )
    if config:
        app.config.update(config)

    app.teardown_appcontext(close_db)
    ensure_database(app)

    @app.cli.command("init-db")
    def init_db_command():
        """Explicitly reset schema and deterministic seed data."""
        db = get_db()
        bootstrap_database(db)
        print("Emergency response database reset and initialised.")

    @app.get("/")
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
            flash(f"Incident #{incident_id} marked resolved.", "success")
        return redirect(url_for("index"))

    @app.get("/api/incidents")
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
