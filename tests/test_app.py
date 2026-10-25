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
            {"TESTING": True, "DATABASE": self.database, "SECRET_KEY": "test-secret"}
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_home_bootstraps_database(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Automated Emergency Response System", response.data)
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0], 2)

    def test_severity_rules_and_boundaries(self):
        self.assertEqual(classify_severity(1.99, True), "LOW")
        self.assertEqual(classify_severity(2.0, True), "MEDIUM")
        self.assertEqual(classify_severity(3.99, True), "MEDIUM")
        self.assertEqual(classify_severity(4.0, True), "HIGH")
        self.assertEqual(classify_severity(6.0, False), "CRITICAL")
        self.assertEqual(classify_severity(6.0, True), "HIGH")
        with self.assertRaises(ValueError):
            classify_severity(float("inf"), True)

    def test_create_and_resolve_incident(self):
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

        with sqlite3.connect(self.database) as db:
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
        with sqlite3.connect(self.database) as db:
            status = db.execute(
                "SELECT status FROM incidents WHERE id = ?", (incident[0],)
            ).fetchone()[0]
        self.assertEqual(status, "RESOLVED")

    def test_invalid_form_shows_feedback_and_is_not_written(self):
        with sqlite3.connect(self.database) as db:
            before = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        response = self.client.post(
            "/incident",
            data={
                "latitude": 120,
                "longitude": 174.7,
                "impact_g": -1,
                "motion_after_impact": "unknown",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Latitude must be between -90 and 90", response.data)
        with sqlite3.connect(self.database) as db:
            after = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        self.assertEqual(before, after)

    def test_json_api_rejects_nan_inf_and_out_of_range(self):
        cases = [
            {"latitude": float("nan"), "longitude": 174.7, "impact_g": 3, "motion_after_impact": "yes"},
            {"latitude": -36.8, "longitude": float("inf"), "impact_g": 3, "motion_after_impact": "yes"},
            {"latitude": -36.8, "longitude": 174.7, "impact_g": float("inf"), "motion_after_impact": "yes"},
            {"latitude": -36.8, "longitude": 174.7, "impact_g": 100.1, "motion_after_impact": "yes"},
        ]
        for payload in cases:
            response = self.client.post("/api/incidents", json=payload)
            self.assertEqual(response.status_code, 400)
            self.assertIn("error", response.get_json())

    def test_json_incident_creation(self):
        response = self.client.post(
            "/api/incidents",
            json={
                "latitude": -36.8485,
                "longitude": 174.7633,
                "impact_g": 4.2,
                "motion_after_impact": "yes",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["severity"], "HIGH")

    def test_accelerometer_detector_finds_spike(self):
        samples = simulate_accelerometer(impact_g=5.0, seed=11)
        result = detect_impact(samples, spike_threshold_g=1.5)
        self.assertTrue(result["triggered"])
        self.assertGreater(result["impact_delta_g"], 4.5)
        api_response = self.client.post(
            "/api/detect",
            json={"samples": samples, "motion_after_impact": "no"},
        )
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(api_response.get_json()["severity"], "HIGH")

    def test_detector_rejects_bad_samples(self):
        for samples in ([1.0, 1.0], [1.0, math.inf, 2.0], [{"x": 0, "y": 0}]*3):
            response = self.client.post("/api/detect", json={"samples": samples})
            self.assertEqual(response.status_code, 400)

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
