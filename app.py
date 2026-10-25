from pathlib import Path
import sqlite3
from flask import Flask, g, redirect, render_template, request, url_for
from detector import build_alert_message, classify_severity

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "emergency.db"

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.cli.command("init-db")
def init_db_command():
    db = get_db()
    for filename in ("schema.sql", "seed.sql"):
        path = BASE_DIR / filename
        if path.exists():
            db.executescript(path.read_text(encoding="utf-8"))
    db.commit()
    print("Emergency response database initialised.")


@app.route("/")
def index():
    incidents = get_db().execute(
        "SELECT * FROM incidents ORDER BY created_at DESC, id DESC"
    ).fetchall()
    return render_template("index.html", incidents=incidents)


@app.post("/incident")
def create_incident():
    latitude = request.form.get("latitude", type=float)
    longitude = request.form.get("longitude", type=float)
    impact_g = request.form.get("impact_g", type=float)
    motion_after_impact = request.form.get("motion_after_impact") == "yes"

    if latitude is None or longitude is None or impact_g is None:
        return redirect(url_for("index"))

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
    db.execute("UPDATE incidents SET status = 'RESOLVED' WHERE id = ?", (incident_id,))
    db.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
