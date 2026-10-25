# Setup and Deployment

## 1. Local setup

Requirements:

- Python 3.10+
- pip
- Git

Commands:

```bash
git clone https://github.com/rsswethaa/automated-emergency-response-system.git
cd automated-emergency-response-system
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app run
```

Open `http://127.0.0.1:5000`.

The SQLite database is created and seeded automatically on first use.

## 2. Useful development commands

```bash
make install
make run
make test
make init-db
make clean
```

## 3. Database reset

```bash
flask --app app init-db
```

This recreates the demonstration schema and seed records. Do not use that reset pattern for a production database.

## 4. GitHub Actions CI

The CI workflow runs Python compilation and automated tests on pushes and pull requests to `main`.

## 5. GitHub Pages static demo

The separate static site under `docs/` can be deployed through GitHub Pages. The repository workflow uploads `./docs` as the Pages artifact.

Expected URL after Pages is enabled for the repository:

`https://rsswethaa.github.io/automated-emergency-response-system/`

The Pages site is a presentation/demo surface; it does not execute the Flask backend or SQLite database.

## 6. Hosting the Flask backend

For a public backend demonstration, use a Python-capable hosting platform and configure a production WSGI server. A real system would also need:

- HTTPS
- secrets/environment configuration
- managed database service
- authentication and authorisation
- logging and monitoring
- backups
- rate limiting
- CSRF protection
- privacy and retention controls

Those controls are not included in this academic prototype.
