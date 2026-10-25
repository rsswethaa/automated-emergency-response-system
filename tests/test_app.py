import math
import sqlite3

import pytest

import app as emergency_app
from detector import build_alert_message, classify_severity, detect_impact, simulate_accelerometer


@pytest.fixture
def app(tmp_path):
    database = tmp_path / "emergency-test.db"
    app = emergency_app.create_app(
        {
            "TESTING": True,
            "DATABASE": database,
            "SECRET_KEY": "test-secret",
            "API_KEY": "test-api-key",
            "DEMO_ADMIN_PASSWORD": "admin-test",
            "DEMO_RESPONDER_PASSWORD": "responder-test",
        }
    )
    app.config["TEST_DATABASE"] = database
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def database_path(app):
    return app.config["TEST_DATABASE"]


def set_csrf(client):
    with client.session_transaction() as session:
        session["_csrf_token"] = "test-csrf"
    return "test-csrf"


def login(client, username="responder", password="responder-test"):
    token = set_csrf(client)
    return client.post(
        "/login",
        data={"username": username, "password": password, "csrf_token": token},
        follow_redirects=True,
    )


def test_dashboard_requires_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    logged_in = login(client)
    assert logged_in.status_code == 200
    assert b"Automated Emergency Response System" in logged_in.data


def test_home_bootstraps_database_and_users(app, client):
    login(client)
    with sqlite3.connect(database_path(app)) as db:
        assert db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2


def test_severity_rules_and_boundaries():
    assert classify_severity(1.99, True) == "LOW"
    assert classify_severity(2.0, True) == "MEDIUM"
    assert classify_severity(4.0, True) == "HIGH"
    assert classify_severity(6.0, False) == "CRITICAL"
    with pytest.raises(ValueError):
        classify_severity(float("inf"), True)


def test_csrf_required_for_browser_mutations(client):
    login(client)
    response = client.post(
        "/incident",
        data={
            "latitude": -36.8,
            "longitude": 174.7,
            "impact_g": 3,
            "motion_after_impact": "yes",
        },
    )
    assert response.status_code == 400


def test_create_and_resolve_incident(app, client):
    login(client)
    token = set_csrf(client)
    response = client.post(
        "/incident",
        data={
            "latitude": -36.8485,
            "longitude": 174.7633,
            "impact_g": 6.5,
            "motion_after_impact": "no",
            "csrf_token": token,
        },
    )
    assert response.status_code == 302

    with sqlite3.connect(database_path(app)) as db:
        incident = db.execute(
            "SELECT id, severity, status FROM incidents ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert incident[1] == "CRITICAL"

    token = set_csrf(client)
    client.post(f"/incident/{incident[0]}/resolve", data={"csrf_token": token})
    with sqlite3.connect(database_path(app)) as db:
        status = db.execute("SELECT status FROM incidents WHERE id = ?", (incident[0],)).fetchone()[0]
    assert status == "RESOLVED"


def test_invalid_form_shows_feedback(client):
    login(client)
    token = set_csrf(client)
    response = client.post(
        "/incident",
        data={
            "latitude": 120,
            "longitude": 174.7,
            "impact_g": -1,
            "motion_after_impact": "unknown",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert b"Latitude must be between -90 and 90" in response.data


def test_json_api_requires_api_key_and_rejects_nan_inf(client):
    good = {
        "latitude": -36.8,
        "longitude": 174.7,
        "impact_g": 4.2,
        "motion_after_impact": "yes",
    }
    assert client.post("/api/incidents", json=good).status_code == 401

    created = client.post("/api/incidents", json=good, headers={"X-API-Key": "test-api-key"})
    assert created.status_code == 201

    bad_payloads = [
        {"latitude": float("nan"), "longitude": 174.7, "impact_g": 3, "motion_after_impact": "yes"},
        {"latitude": -36.8, "longitude": float("inf"), "impact_g": 3, "motion_after_impact": "yes"},
        {"latitude": -36.8, "longitude": 174.7, "impact_g": 100.1, "motion_after_impact": "yes"},
    ]
    for payload in bad_payloads:
        response = client.post(
            "/api/incidents",
            json=payload,
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == 400


def test_accelerometer_detector_finds_spike(client):
    samples = simulate_accelerometer(impact_g=5.0, seed=11)
    result = detect_impact(samples, spike_threshold_g=1.5)
    assert result["triggered"] is True

    response = client.post(
        "/api/detect",
        json={"samples": samples, "motion_after_impact": "no"},
    )
    assert response.status_code == 200
    assert response.get_json()["severity"] == "HIGH"


def test_detector_rejects_bad_samples(client):
    bad_samples = ([1.0, 1.0], [1.0, math.inf, 2.0], [{"x": 0, "y": 0}] * 3)
    for samples in bad_samples:
        response = client.post("/api/detect", json={"samples": samples})
        assert response.status_code == 400


def test_incident_api_requires_login_for_read(client):
    assert client.get("/api/incidents").status_code == 302
    login(client)
    response = client.get("/api/incidents")
    assert response.status_code == 200
    assert response.get_json()["count"] == 2


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_alert_message():
    message = build_alert_message(7, "HIGH", -36.8, 174.7)
    assert "#7" in message
