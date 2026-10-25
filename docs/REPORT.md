# Project Report — Automated Emergency Response System

## Executive summary

The Automated Emergency Response System is a portfolio reconstruction of an academic safety-technology concept. It demonstrates how simulated accident data can be validated, classified by severity, stored in a relational database and converted into an auditable simulated responder alert.

The project is deliberately presented as an educational software prototype rather than a certified emergency, medical or automotive system.

## 1. Problem statement

Emergency response may be delayed when an accident is not reported quickly or when location and severity information are unavailable. The software problem explored here is how to convert basic simulated impact and motion information into a structured incident workflow that can be reviewed and tracked.

## 2. Project objectives

The prototype aims to:

- accept simulated incident data
- validate basic location and sensor-style values
- classify urgency using transparent rules
- persist incident and alert records
- provide an operator dashboard
- support incident resolution
- expose simple machine-readable status endpoints
- demonstrate automated testing and CI
- document architecture, data design, deployment and limitations

## 3. Functional requirements

| Requirement | Implementation |
|---|---|
| Capture incident location | Latitude and longitude form fields |
| Capture simulated impact | `impact_g` input |
| Capture post-impact motion | Boolean-style detected/not-detected input |
| Classify severity | `detector.py` rule engine |
| Store incident history | SQLite `incidents` table |
| Record notification activity | SQLite `alerts` table |
| Display current incidents | Flask/Jinja dashboard |
| Resolve incidents | POST resolve route |
| Provide integration output | `/api/incidents` JSON route |
| Provide service check | `/health` endpoint |

## 4. Non-functional requirements

The portfolio version prioritises simplicity, reproducibility, auditability and reviewer accessibility. It uses a local database, deterministic seed data, minimal dependencies and automated tests that can run in CI without external services.

## 5. System design

The system uses a modular Flask architecture. The web layer validates requests and manages persistence, while `detector.py` handles classification logic. SQLite stores incident and alert records. Jinja templates render the dashboard. GitHub Actions performs automated compilation and testing.

Detailed diagrams are maintained in `ARCHITECTURE.md` and the relational model is documented in `DATABASE.md`.

## 6. Severity model

The demonstration rules are:

- LOW: impact below 2g
- MEDIUM: impact from 2g to below 4g
- HIGH: impact at or above 4g unless the critical rule applies
- CRITICAL: impact at or above 6g and no motion detected after impact

The logic is intentionally simple and explainable. It is not medically or automotive validated.

## 7. Data model

The system contains two core entities. `incidents` stores location, impact, motion state, severity, workflow status and creation time. `alerts` stores one or more simulated notification records linked to incidents.

Constraints and indexes are defined in `schema.sql`. Demonstration data is defined in `seed.sql`.

## 8. Implementation details

Key implementation choices include:

- Flask for lightweight server-side web development
- SQLite for zero-service local persistence
- parameterised SQL for database writes
- CHECK constraints for key data-quality rules
- Flask application-context database connections
- server-rendered HTML for a simple reviewer-facing UI
- standard-library `unittest` for dependency-light tests

## 9. Testing and quality assurance

The automated suite checks database bootstrap, classification boundaries, incident creation, alert insertion, invalid input handling, resolution, JSON API output and health status. GitHub Actions runs compilation and tests automatically on repository changes.

Testing details are documented in `TESTING.md`.

## 10. Deployment

The Flask application can run locally with a Python virtual environment. A separate static demonstration/documentation site under `docs/` can be published to GitHub Pages. The Pages workflow has been configured to deploy the correct `docs` directory.

Deployment details are documented in `DEPLOYMENT.md`.

## 11. Security and privacy considerations

The demonstration does not implement authentication, authorisation, CSRF protection, rate limiting, a secrets manager or production-grade encryption controls. These omissions are explicitly documented rather than hidden.

A production version would require authenticated devices and responders, encrypted transport and storage, strict location-data governance, delivery guarantees and a formal operational security model.

## 12. Limitations

- no real sensors or IoT hardware
- no verified GPS source
- no SMS, telephony or emergency-service integration
- no medical or crash-science validation
- no authenticated responder accounts
- no high-availability infrastructure
- no production observability
- no regulatory compliance claim

## 13. Future development

A serious research prototype could add signed IoT telemetry, event queues, PostgreSQL, real-time maps, role-based responder workflows, notification-provider adapters, delivery receipts, encrypted audit storage, monitoring, load testing and expert validation.

## 14. Portfolio integrity

This repository is a modern reconstruction based on the project description represented in the author's portfolio/CV. It is designed to demonstrate software engineering capability and is not represented as the exact archived source code from an earlier academic submission.

## Conclusion

The repository now demonstrates more than a README description: it contains a working application, rule engine, constrained relational database, seeded data, automated tests, CI, static demo, architecture diagrams, API documentation, database documentation, security notes, deployment instructions and a formal technical report. Together these components provide a coherent end-to-end project artifact suitable for technical review.
