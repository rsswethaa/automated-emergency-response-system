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

    def test_severity_rules_and_boundaries(self):
        self.assertEqual(classify_severity(1.99, True), "LOW")
        self.assertEqual(classify_severity(2.0, True), "MEDIUM")
        self.assertEqual(classify_severity(3.99, True), "MEDIUM")
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

    def test_invalid_incident_is_not_written(self):
        self.client.get("/")
        with sqlite3.connect(emergency_app.DATABASE) as db:
            before = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]

        response = self.client.post(
            "/incident",
            data={
                "latitude": 120,
                "longitude": 174.7,
                "impact_g": -1,
                "motion_after_impact": "unknown",
            },
        )
        self.assertEqual(response.status_code, 302)

        with sqlite3.connect(emergency_app.DATABASE) as db:
            after = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        self.assertEqual(before, after)

    def test_incident_api(self):
        response = self.client.get("/api/incidents")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["count"], 2)
        self.assertEqual(len(payload["incidents"]), 2)
        self.assertIn("severity", payload["incidents"][0])

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_alert_message(self):
        message = build_alert_message(7, "HIGH", -36.8, 174.7)
        self.assertIn("#7", message)
        self.assertIn("HIGH", message)


if __name__ == "__main__":
    unittest.main()
