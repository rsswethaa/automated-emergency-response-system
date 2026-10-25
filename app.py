from pathlib import Path
import sqlite3

from flask import Flask, g, jsonify, redirect, render_template, request, url_for

from detector import build_alert_message, classify_severity

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "emergency.db"

app = Flask(__name__)


def bootstrap_database(db):
    """Create the schema and load deterministic demonstration data."""
    for filename in ("schema.sql", "seed.sql"):
        path = BASE_DIR / filename
        if path.exists():
            db.executescript(path.read_text(encoding="utf-8"))
    db.commit()


def get_db():
    """Return one SQLite connection per Flask application context."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        table_exists = g.db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='incidents'"
        ).fetchone()
        if table_exists is None:
            bootstrap_database(g.db)
    return g.db


def validate_incident_input(latitude, longitude, impact_g, motion_value):
    """Validate browser/API style incident inputs before writing to SQLite."""
    if latitude is None or longitude is None or impact_g is None:
        return False
    if not -90 <= latitude <= 90:
        return False
    if not -180 <= longitude <= 180:
        return False
    if impact_g < 0:
        return False
    return motion_value in {"yes", "no"}


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.cli.command("init-db")
def init_db_command():
    """Reset the local demonstration database from schema.sql and seed.sql."""
    bootstrap_database(get_db())
    print("Emergency response database initialised.")


@app.route("/")
def index():
    db = get_db()
    incidents = db.execute(
        "SELECT * FROM incidents ORDER BY created_at DESC, id DESC"
    ).fetchall()
    summary = db.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) AS open_count,
            SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved_count,
            SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count
        FROM incidents
        """
    ).fetchone()
    return render_template("index.html", incidents=incidents, summary=summary)


@app.post("/incident")
def create_incident():
    latitude = request.form.get("latitude", type=float)
    longitude = request.form.get("longitude", type=float)
    impact_g = request.form.get("impact_g", type=float)
    motion_value = request.form.get("motion_after_impact", "yes")

    if not validate_incident_input(latitude, longitude, impact_g, motion_value):
        return redirect(url_for("index"))

    motion_after_impact = motion_value == "yes"
    severity = classify_severity(impact_g, motion_after_impact)
    db = get_db()
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
    db.commit()
    return redirect(url_for("index"))


@app.post("/incident/<int:incident_id>/resolve")
def resolve_incident(incident_id):
    db = get_db()
    db.execute(
        "UPDATE incidents SET status = 'RESOLVED' WHERE id = ?",
        (incident_id,),
    )
    db.commit()
    return redirect(url_for("index"))


@app.get("/api/incidents")
def api_incidents():
    """Return incident records for demonstration/integration testing."""
    rows = get_db().execute(
        "SELECT * FROM incidents ORDER BY created_at DESC, id DESC"
    ).fetchall()
    incidents = []
    for row in rows:
        item = dict(row)
        item["motion_after_impact"] = bool(item["motion_after_impact"])
        incidents.append(item)
    return jsonify({"count": len(incidents), "incidents": incidents})


@app.get("/health")
def health():
    """Lightweight service-health endpoint for deployment checks."""
    get_db().execute("SELECT 1").fetchone()
    return jsonify({"status": "ok", "service": "automated-emergency-response-system"})


if __name__ == "__main__":
    app.run(debug=True)
