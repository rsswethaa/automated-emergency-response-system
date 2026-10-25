# Testing and Validation

## 1. Automated test strategy

The test suite uses Python's standard `unittest` library and Flask's test client. Each test receives a temporary SQLite database so local application data is not modified.

Current automated coverage includes:

- database bootstrap from schema and seed files
- severity decision boundaries
- valid incident creation
- automatic creation of one alert audit row per incident
- incident resolution
- invalid input rejection
- JSON incident API
- health endpoint
- alert-message construction

Run locally with:

```bash
python -m unittest discover -s tests -v
```

or:

```bash
make test
```

## 2. Severity boundary matrix

| Impact | Motion | Expected |
|---:|---|---|
| 1.99g | detected | LOW |
| 2.00g | detected | MEDIUM |
| 3.99g | detected | MEDIUM |
| 4.00g | detected | HIGH |
| 6.00g | detected | HIGH |
| 6.00g | not detected | CRITICAL |

## 3. Input validation cases

The application should not persist an incident when:

- latitude is outside -90 to 90
- longitude is outside -180 to 180
- impact is negative
- a required numeric field is missing
- motion state is not `yes` or `no`

The database schema independently reinforces several of these rules through CHECK constraints.

## 4. Continuous integration

`.github/workflows/ci-pages.yml` runs on pushes and pull requests to `main`. It:

1. checks out the repository
2. installs Python 3.12
3. installs dependencies
4. compiles Python files
5. runs the full unit-test suite

This gives the repository a reproducible automated quality gate.

## 5. Manual browser checks

For a portfolio review, manually verify:

- the home page loads
- the safety warning is visible
- a LOW/MEDIUM/HIGH/CRITICAL incident can be simulated
- a new incident appears in the dashboard
- an open incident can be marked resolved
- `/api/incidents` returns JSON
- `/health` returns an `ok` status

## 6. Safety validation

Documentation and UI wording must consistently state that the system is an educational simulation. No part of the project should imply certified emergency-service, medical or automotive capability.
