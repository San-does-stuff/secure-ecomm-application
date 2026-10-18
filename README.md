# Secure Juice & Smoothie E-Commerce

A Django-based juice and smoothie store developed as an OWASP Top 10-focused secure software development project. The application includes a product catalog, account registration and login, a session-based shopping cart, checkout, and customer order history.

> **Project status:** Educational/local-development project. Do not deploy this repository as a production e-commerce service without completing the security review and resolving the outstanding items documented below.

## Features

- Product catalog and product detail pages
- Registration and login using Django's built-in authentication forms
- Session-based cart with server-side quantity and stock checks
- Checkout that calculates prices from database records and creates orders
- Order history and customer-scoped order detail views
- Django ORM and SQLite for local development
- CSRF middleware and CSRF tokens in the forms inspected
- Environment-based Django secret key and debug/host settings
- Security tooling used during review: Bandit, Semgrep, `pip-audit`, and OWASP ZAP

## Technology

- Python (the supplied environment appears to use Python 3.13)
- Django (the supplied `requirements.txt` pins Django 6.1.2)
- Django Templates, HTML, CSS, and JavaScript
- SQLite for local development
- `python-dotenv`
- Git

## Prerequisites

- Python compatible with the versions pinned in `requirements.txt`
- Windows PowerShell or another terminal
- Git (optional, for version control)

## Setup on Windows PowerShell

Run these commands from the repository root, where `manage.py` is located.

### 1. Create and activate a virtual environment

```powershell
py -3.13 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If Python 3.13 is not installed, use a Python version supported by the pinned dependencies and replace `py -3.13` accordingly.

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

The current `requirements.txt` appears to contain a broad environment snapshot, including security-scanning and unrelated transitive packages, rather than only the minimum runtime dependencies. It also contains `mcp==1.29.0`, which was reported by the supplied `pip-audit` screenshot. Review and remediate this before treating dependency installation as security-clean. See [Security testing](docs/SECURITY_TESTING.md).

### 3. Configure environment variables

Copy the example file and edit it:

```powershell
Copy-Item .env.example .env
```

Generate a Django secret key:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Paste the generated value into `.env` as `DJANGO_SECRET_KEY`. Do not use the placeholder value. Do not commit or share `.env`.

Example local configuration:

```dotenv
DJANGO_SECRET_KEY=replace-this-with-a-newly-generated-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

`DJANGO_DEBUG=True` is for local development only. Use `False` and explicitly configured hosts for any deployment. Never reuse a development secret in production.

### 4. Apply migrations

```powershell
python manage.py migrate
```

### 5. Create an administrator (optional)

```powershell
python manage.py createsuperuser
```

### 6. Run Django checks and tests

```powershell
python manage.py check
python manage.py test
```

Expected successful check output includes `System check identified no issues (0 silenced).` The test command should report the number of tests run and `OK`. These are expected outputs, not claims that the commands have already passed in every environment. Record the actual output when you run them.

### 7. Start the development server

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

The Django development server is for local development only, not production hosting.

## Project layout

```text
config/                 Django settings and root URL configuration
core/                   Store application, models, views, URLs, tests, templates
core/migrations/        Database migrations
templates/base.html     Shared template layout
static/css/             Shared stylesheets
static/js/              Shared JavaScript
static/images/          Static images
documents/              Project/course supporting documents
manage.py               Django management entry point
requirements.txt        Pinned Python dependencies
.env.example            Environment variable template (safe placeholders only)
docs/SECURITY_TESTING.md Security review notes and evidence
```

## Security controls currently visible in the source review

- **Authentication:** Django `UserCreationForm` and `AuthenticationForm` are used; passwords are managed by Django rather than stored manually by application code.
- **CSRF:** `CsrfViewMiddleware` is enabled, and the inspected cart/checkout forms include `{% csrf_token %}`.
- **Authorization:** Checkout, order history, and order detail require login. Order detail filters by both order ID and `request.user`.
- **Input validation:** Cart quantities are parsed and checked server-side, with limits of 1–100 and stock checks.
- **Price integrity:** Cart and checkout totals are calculated from `Product.price` in the database; checkout does not use a browser-submitted price.
- **Order consistency:** Checkout uses `transaction.atomic()` while creating the order and reducing stock.
- **Secret handling:** Django settings read `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS` from environment variables; startup fails if the secret key is absent.
- **Template output:** Django templates provide automatic HTML escaping by default unless explicitly bypassed.

These are source-review observations, not proof that all security requirements are satisfied. See the outstanding issues and scan evidence in `docs/SECURITY_TESTING.md`.

## Known limitations and items to resolve

1. The supplied `pip-audit` screenshot reports a known vulnerability in `mcp==1.29.0` (CVE-2026-59951). Confirm which fixed version is compatible, update the dependency or remove it if unnecessary, then rerun the audit.
2. The supplied Semgrep scan did not complete: Windows error 1455 reported that the paging file was too small. This is an incomplete scan, not a clean result.
3. Bandit reported four low-severity, medium-confidence hardcoded-password findings in `core/tests.py`. They appear to be test-only credentials, but can be replaced with a shared test fixture/helper to reduce scanner noise. Never reuse them outside tests.
4. The provided evidence does not include a completed OWASP ZAP report.
5. The tests inspected cover catalog and basic authentication behavior, but the evidence reviewed does not establish coverage for cart validation, checkout stock handling, transaction behavior, or order ownership. Add tests for these cases.
6. The supplied `core/templates/core/order_detail.html` appears to contain order-history markup and references `orders`, while the detail view passes a single `order`. Correct and test this template before release.
7. Review `requirements.txt` and produce a minimal, intentional dependency set. Do not blindly upgrade all packages; validate compatible versions and rerun tests and scans.
8. SQLite is suitable for local development, but row-locking behavior differs from databases such as PostgreSQL. Reassess checkout concurrency and stock consistency before production use.
9. Production deployment settings, HTTPS, secure cookies, HSTS, logging/alerting, backups, operational monitoring, and deployment-specific host/origin settings need a deployment-focused review.
10. The supplied ZIP contains `.env`, `db.sqlite3`, and `.git/` even though `.env` and the database are ignored by the provided `.gitignore`. They were not listed as tracked files in the supplied Git index, but the ZIP itself includes them. Do not publish that ZIP. Review local `.env` contents privately, remove local secrets/data from any release archive, and never publish Git history or local database contents unintentionally.

## Security testing

See [`docs/SECURITY_TESTING.md`](docs/SECURITY_TESTING.md) for the observed scanner results, reproducible commands, evidence status, and remediation checklist.

## License

No license has been specified. Add an appropriate license before inviting reuse or contributions.
