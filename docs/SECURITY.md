# Security and Safety Considerations

This project is intentionally scoped as an educational prototype. The following controls are present or deliberately documented as gaps.

## Implemented safeguards

- parameterised SQL for application writes
- database CHECK constraints for core input domains
- foreign-key enforcement enabled on application connections
- local database and `.env` files excluded from version control
- no real emergency-service integration
- explicit prototype warning in the interface and documentation

## Known limitations

- no user authentication
- no role-based authorisation
- no CSRF protection
- no rate limiting
- no encryption-at-rest controls beyond the host filesystem
- no secrets manager
- no tamper-resistant audit log
- no signed sensor/device messages
- no privacy consent workflow
- no production monitoring or incident response process

## Threat-model examples

| Risk | Example mitigation for a production system |
|---|---|
| False incident injection | Authenticated/signed device messages and anomaly detection |
| Unauthorised incident access | Strong identity, RBAC and least privilege |
| Alert tampering | Append-only audited event pipeline |
| Location-data exposure | Encryption, minimisation, retention limits and access logging |
| Denial of service | Rate limiting, queues, autoscaling and circuit breakers |
| Notification failure | Retry queues, delivery receipts and multi-channel fallbacks |

## Safety statement

The severity thresholds in this repository are illustrative rules only. They are not evidence-based injury predictors and must not be used to make real emergency decisions.
