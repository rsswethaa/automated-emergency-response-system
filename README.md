# Automated Emergency Response System

> **Portfolio reconstruction:** This repository is a modern rebuild based on the verified academic project description in my CV. It is not presented as the exact archived source code from the original submission.

A prototype emergency-response platform designed to detect and register accident events, classify urgency, store incident records and simulate rapid notification to emergency contacts/responders.

![Automated Emergency Response System browser demo](docs/assets/emergency-demo.png)

## Verified status
- GitHub Actions CI: **passing**
- Fresh-clone database setup: **automatic**
- Severity classification rules: **tested**
- Incident creation/resolution workflow: **tested**
- Browser demo: **rendered and visually checked in Chromium**
- Static GitHub Pages demo: available in `docs/index.html` and ready to publish

## Core features
- Create and track emergency incidents
- Automatic severity scoring from sensor-style inputs
- Store location, status and timestamps
- Simulate responder/contact alerts
- Incident dashboard and status updates
- SQLite-backed audit trail

## Technology
Python · Flask · SQLite · HTML · CSS · JavaScript · GitHub Actions

## Repository contents
- `app.py` — web application and response workflow
- `detector.py` — rule-based incident severity engine
- `schema.sql` — database schema
- `seed.sql` — demonstration incidents
- `tests/` — automated workflow and rule tests
- `templates/` — Flask incident dashboard and reporting form
- `static/` — Flask interface styling
- `docs/index.html` — standalone interactive portfolio demo for GitHub Pages
- `docs/assets/emergency-demo.png` — real Chromium browser capture
- `docs/ARCHITECTURE.md` — system architecture and workflow diagram
- `docs/REPORT.md` — technical project report
- `docs/TESTING.md` — testing and validation plan

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app run
```

The app now creates its SQLite schema and demonstration data automatically on first run. Use `flask --app app init-db` only when you deliberately want to reset the demo database.

Open `http://127.0.0.1:5000`.

## Publish the static demo
GitHub Pages cannot be enabled by the connected GitHub App, but the deployable site is already prepared. In this repository open **Settings → Pages**, choose **Deploy from a branch**, select **main** and **/docs**, then save. The expected public URL is:

`https://rsswethaa.github.io/automated-emergency-response-system/`

## Safety note
This is an educational software prototype only. It is not a certified emergency, medical, automotive or public-safety system and must not be relied on for real emergency response.

## Author
Swethaa Sri Ravi Sankar — B.Tech Computer Science and Business Systems; Master of Applied Finance candidate, University of Auckland.
