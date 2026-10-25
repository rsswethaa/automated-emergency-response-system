# Automated Emergency Response System

> **Portfolio reconstruction:** This repository is a modern rebuild based on the verified academic project description in my CV. It is not presented as the exact archived source code from the original submission.

A prototype emergency-response platform designed to detect and register accident events, classify urgency, store incident records and simulate rapid notification to emergency contacts/responders.

## Core features
- Create and track emergency incidents
- Automatic severity scoring from sensor-style inputs
- Store location, status and timestamps
- Simulate responder/contact alerts
- Incident dashboard and status updates
- SQLite-backed audit trail

## Technology
Python · Flask · SQLite · HTML · CSS

## Repository contents
- `app.py` — web application and response workflow
- `detector.py` — rule-based incident severity engine
- `schema.sql` — database schema
- `seed.sql` — demonstration incidents
- `templates/` — incident dashboard and reporting form
- `static/` — interface styling
- `docs/ARCHITECTURE.md` — system architecture and workflow diagram
- `docs/REPORT.md` — technical project report
- `docs/TESTING.md` — testing and validation plan

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run
```

Open `http://127.0.0.1:5000`.

## Safety note
This is an educational software prototype only. It is not a certified emergency, medical, automotive or public-safety system and must not be relied on for real emergency response.

## Author
Swethaa Sri Ravi Sankar — B.Tech Computer Science and Business Systems; Master of Applied Finance candidate, University of Auckland.
