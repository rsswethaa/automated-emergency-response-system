import sqlite3
import tempfile
import unittest
from pathlib import Path

import app as emergency_app
from detector import build_alert_message, classify_severity


class EmergencyAppTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        emergency_app.DATABASE = Path(self.tempdir.name) / "emergency-test.db"
        emergency_app.app.config.update(TESTING=True)
        self.client = emergency_app.app.test_client()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_home_bootstraps_database(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Automated Emergency Response System", response.data)
        with sqlite3.connect(emergency_app.DATABASE) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0], 2)

    def test_severity_rules(self):
        self.assertEqual(classify_severity(1.0, True), "LOW")
        self.assertEqual(classify_severity(2.0, True), "MEDIUM")
        self.assertEqual(classify_severity(4.0, True), "HIGH")
        self.assertEqual(classify_severity(6.0, False), "CRITICAL")
        self.assertEqual(classify_severity(6.0, True), "HIGH")

    def test_create_and_resolve_incident(self):
        self.client.get("/")
        response = self.client.post(
            "/incident",
            data={
                "latitude": -36.8485,
                "longitude": 174.7633,
                "impact_g": 6.5,
                "motion_after_impact": "no",
            },
        )
        self.assertEqual(response.status_code, 302)

        with sqlite3.connect(emergency_app.DATABASE) as db:
            incident = db.execute(
                "SELECT id, severity, status FROM incidents ORDER BY id DESC LIMIT 1"
            ).fetchone()
            alert_count = db.execute(
                "SELECT COUNT(*) FROM alerts WHERE incident_id = ?", (incident[0],)
            ).fetchone()[0]

        self.assertEqual(incident[1], "CRITICAL")
        self.assertEqual(incident[2], "OPEN")
        self.assertEqual(alert_count, 1)

        self.client.post(f"/incident/{incident[0]}/resolve")
        with sqlite3.connect(emergency_app.DATABASE) as db:
            status = db.execute(
                "SELECT status FROM incidents WHERE id = ?", (incident[0],)
            ).fetchone()[0]
        self.assertEqual(status, "RESOLVED")

    def test_alert_message(self):
        message = build_alert_message(7, "HIGH", -36.8, 174.7)
        self.assertIn("#7", message)
        self.assertIn("HIGH", message)


if __name__ == "__main__":
    unittest.main()
