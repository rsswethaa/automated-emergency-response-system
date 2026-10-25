import math
import sqlite3
import tempfile
import unittest
from pathlib import Path

import app as emergency_app
from detector import build_alert_message, classify_severity, detect_impact, simulate_accelerometer


class EmergencyAppTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "emergency-test.db"
        self.app = emergency_app.create_app(
            {
                "TESTING": True,
                "DATABASE": self.database,
                "SECRET_KEY": "test-secret",
                "API_KEY": "test-api-key",
                "DEMO_ADMIN_PASSWORD": "admin-test",
                "DEMO_RESPONDER_PASSWORD": "responder-test",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.tempdir.cleanup()

    def set_csrf(self):
        with self.client.session_transaction() as session:
            session["_csrf_token"] = "test-csrf"
        return "test-csrf"

    def login(self, username="responder", password="responder-test"):
        token = self.set_csrf()
        return self.client.post(
            "/login",
            data={"username": username, "password": password, "csrf_token": token},
            follow_redirects=True,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])
        logged_in = self.login()
        self.assertEqual(logged_in.status_code, 200)
        self.assertIn(b"Automated Emergency Response System", logged_in.data)

    def test_home_bootstraps_database_and_users(self):
        self.login()
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 2)

    def test_severity_rules_and_boundaries(self):
        self.assertEqual(classify_severity(1.99, True), "LOW")
        self.assertEqual(classify_severity(2.0, True), "MEDIUM")
        self.assertEqual(classify_severity(4.0, True), "HIGH")
        self.assertEqual(classify_severity(6.0, False), "CRITICAL")
        with self.assertRaises(ValueError):
            classify_severity(float("inf"), True)

    def test_csrf_required_for_browser_mutations(self):
        self.login()
        response = self.client.post(
            "/incident",
            data={"latitude": -36.8, "longitude": 174.7, "impact_g": 3, "motion_after_impact": "yes"},
        )
        self.assertEqual(response.status_code, 400)

    def test_create_and_resolve_incident(self):
        self.login()
        token = self.set_csrf()
        response = self.client.post(
            "/incident",
            data={"latitude": -36.8485, "longitude": 174.7633, "impact_g": 6.5, "motion_after_impact": "no", "csrf_token": token},
        )
        self.assertEqual(response.status_code, 302)
        with sqlite3.connect(self.database) as db:
            incident = db.execute("SELECT id, severity, status FROM incidents ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(incident[1], "CRITICAL")
        token = self.set_csrf()
        self.client.post(f"/incident/{incident[0]}/resolve", data={"csrf_token": token})
        with sqlite3.connect(self.database) as db:
            status = db.execute("SELECT status FROM incidents WHERE id = ?", (incident[0],)).fetchone()[0]
        self.assertEqual(status, "RESOLVED")

    def test_invalid_form_shows_feedback(self):
        self.login()
        token = self.set_csrf()
        response = self.client.post(
            "/incident",
            data={"latitude": 120, "longitude": 174.7, "impact_g": -1, "motion_after_impact": "unknown", "csrf_token": token},
            follow_redirects=True,
        )
        self.assertIn(b"Latitude must be between -90 and 90", response.data)

    def test_json_api_requires_api_key_and_rejects_nan_inf(self):
        good = {"latitude": -36.8, "longitude": 174.7, "impact_g": 4.2, "motion_after_impact": "yes"}
        self.assertEqual(self.client.post("/api/incidents", json=good).status_code, 401)
        created = self.client.post("/api/incidents", json=good, headers={"X-API-Key": "test-api-key"})
        self.assertEqual(created.status_code, 201)
        for payload in [
            {"latitude": float("nan"), "longitude": 174.7, "impact_g": 3, "motion_after_impact": "yes"},
            {"latitude": -36.8, "longitude": float("inf"), "impact_g": 3, "motion_after_impact": "yes"},
            {"latitude": -36.8, "longitude": 174.7, "impact_g": 100.1, "motion_after_impact": "yes"},
        ]:
            response = self.client.post("/api/incidents", json=payload, headers={"X-API-Key": "test-api-key"})
            self.assertEqual(response.status_code, 400)

    def test_accelerometer_detector_finds_spike(self):
        samples = simulate_accelerometer(impact_g=5.0, seed=11)
        result = detect_impact(samples, spike_threshold_g=1.5)
        self.assertTrue(result["triggered"])
        response = self.client.post("/api/detect", json={"samples": samples, "motion_after_impact": "no"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["severity"], "HIGH")

    def test_detector_rejects_bad_samples(self):
        for samples in ([1.0, 1.0], [1.0, math.inf, 2.0], [{"x": 0, "y": 0}] * 3):
            response = self.client.post("/api/detect", json={"samples": samples})
            self.assertEqual(response.status_code, 400)

    def test_incident_api_requires_login_for_read(self):
        self.assertEqual(self.client.get("/api/incidents").status_code, 302)
        self.login()
        response = self.client.get("/api/incidents")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["count"], 2)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_alert_message(self):
        message = build_alert_message(7, "HIGH", -36.8, 174.7)
        self.assertIn("#7", message)


if __name__ == "__main__":
    unittest.main()
