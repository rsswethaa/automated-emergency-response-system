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

The application CI is independent from GitHub Pages. A Pages configuration problem therefore does not mean the Flask application or automated tests are failing.

## 5. GitHub Pages static demo

The static portfolio/demo site is stored under `docs/`. The deployment workflow uploads that directory only when GitHub Pages is already enabled for the repository.

### One-time repository setting

GitHub does not allow the connected automation integration to create/enable the Pages site on the owner's behalf. The repository owner must perform this one-time setting in the GitHub interface:

1. Open the repository.
2. Open **Settings**.
3. Select **Pages**.
4. Under **Build and deployment**, set **Source** to **GitHub Actions**.
5. Save if GitHub presents a save control.
6. Open **Actions → Deploy GitHub Pages demo** and choose **Run workflow**, or make a later change under `docs/`.

Until Pages is enabled, the workflow performs a preflight check, reports a notice and exits successfully instead of generating a misleading failed-build notification.

Expected URL after the one-time Pages setting and a successful deployment:

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
