# System Architecture

This document explains how the portfolio prototype is structured, how data moves through it and where its safety boundaries sit.

## 1. High-level architecture

```mermaid
flowchart LR
    U[User / simulated sensor input] --> V[Input validation]
    V --> D[Severity detector]
    D --> W[Flask web application]
    W --> I[(SQLite incidents table)]
    W --> A[(SQLite alerts table)]
    I --> UI[Incident dashboard]
    A --> UI
    W --> API[/JSON API/]
    W --> H[/Health endpoint/]
```

The design deliberately separates severity classification from the web layer. `detector.py` contains the classification rule engine, while `app.py` coordinates HTTP requests, persistence and presentation.

## 2. Component responsibilities

| Component | Responsibility |
|---|---|
| `app.py` | Flask routes, validation, database lifecycle, persistence, API and dashboard orchestration |
| `detector.py` | Severity classification and simulated alert-message construction |
| `schema.sql` | Relational schema, constraints, foreign keys and indexes |
| `seed.sql` | Deterministic demonstration records |
| `templates/index.html` | Server-rendered operator/dashboard UI |
| `static/style.css` | Presentation styling |
| `tests/test_app.py` | Automated route, validation, API and rule tests |
| `docs/` | Architecture, database, testing, deployment and report documentation |

## 3. Incident processing sequence

```mermaid
sequenceDiagram
    actor User
    participant Flask as Flask app
    participant Detector as detector.py
    participant DB as SQLite
    participant UI as Dashboard

    User->>Flask: Submit latitude, longitude, impact, motion
    Flask->>Flask: Validate input bounds
    Flask->>Detector: classify_severity()
    Detector-->>Flask: LOW / MEDIUM / HIGH / CRITICAL
    Flask->>DB: Insert incident
    Flask->>Detector: build_alert_message()
    Detector-->>Flask: Simulated notification text
    Flask->>DB: Insert alert audit row
    Flask-->>User: Redirect to dashboard
    User->>UI: View incident state
    User->>Flask: Mark incident resolved
    Flask->>DB: Update status = RESOLVED
```

## 4. Severity decision flow

```mermaid
flowchart TD
    S[Start] --> A{Impact >= 6g?}
    A -- Yes --> B{Motion after impact?}
    B -- No --> C[CRITICAL]
    B -- Yes --> D[HIGH]
    A -- No --> E{Impact >= 4g?}
    E -- Yes --> D
    E -- No --> F{Impact >= 2g?}
    F -- Yes --> G[MEDIUM]
    F -- No --> H[LOW]
```

These thresholds are intentionally illustrative and are not validated medical, automotive or emergency-response thresholds.

## 5. Deployment architecture

```mermaid
flowchart LR
    Dev[Developer] --> GH[GitHub repository]
    GH --> CI[GitHub Actions CI]
    CI --> Tests[Python compile + unittest]
    GH --> Pages[GitHub Pages workflow]
    Pages --> Docs[Static docs/demo under /docs]
    Local[Local Python runtime] --> Flask[Flask application]
    Flask --> SQLite[(Local emergency.db)]
```

The Flask app is intended for local/demo execution. The static `docs/index.html` site is separate and can be published through GitHub Pages.

## 6. Design choices

- SQLite keeps setup friction low and makes the project easy to review.
- Parameterised SQL is used for application writes.
- Database constraints enforce valid coordinates, non-negative impact values, known severity values and known incident states.
- Foreign-key cascading keeps alert rows tied to their incident lifecycle.
- Separate JSON and health endpoints make the system easier to test and integrate.

## 7. Safety boundary

This is an educational software prototype. It does not perform certified crash detection, call emergency services, diagnose injuries or guarantee responder notification.
