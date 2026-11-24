# GUCAIR — Global University Consortium of AI Readiness

GUCAIR is a server-rendered Django web application for assessing, comparing and improving
university AI readiness. Institutions register a representative account, submit a
24-question self-assessment across six dimensions, receive a normalised 0–100 score with
category and recommendations, and explore consortium-wide analytics and a curated resource
hub.

The assessment is **indicative and self-reported**. It is not an accreditation decision.

## Live application

| Item | Location |
| --- | --- |
| Public web application | _To be added after the verified Render deployment_ |
| Health check | `https://<render-service>.onrender.com/health/` |
| Source repository | _To be added after the GitHub push_ |

> The final submitted source archive is created only after the live URL above has been
> verified in a browser.

## Features

### Public website
- Landing page with live consortium statistics drawn from database records.
- Framework and methodology pages describing the six dimensions and scoring bands.
- Approved university directory with search, country filter and pagination.
- Public university profiles (scores require sign-in).
- AI Resource Hub with categories, search and related resources.
- Contact form persisted to the database and managed by administrators.
- Responsive Bootstrap 5 interface, accessible navigation, reduced-motion support.

### Accounts and roles
- Two roles: **Administrator** and **University Representative**.
- Combined representative registration creates the user account, profile and a
  **pending** university record in one transaction.
- Django authentication, password validation, CSRF protection, session expiry and
  role-based access control.
- Profile editing and secure password change.
- Administrator user management: search, role changes and account activation.

### Universities
- Representative creates and edits only their own institutional profile.
- Administrator approval workflow with review notes and approval timestamps.
- Pending/rejected institutions are hidden from public pages.
- Administrator CRUD, filters, name-confirmed deletion and cascade of assessment data.

### AI readiness assessment
- Six dimensions, four questions each, 24 indicators in a fixed framework order.
- Five-point maturity scale from 0 (Not implemented) to 4 (Fully implemented).
- Dimension score = raw points ÷ (4 × questions) × 100; overall score uses all 24 items.
- Bands: **Initial 0–39**, **Developing 40–59**, **Advanced 60–79**, **Leading 80–100**.
- Server-side validation: every question is required and every answer must be 0–4.
- Immutable assessment records with response-level evidence, history and trend charts.
- Lowest-scoring dimensions receive targeted improvement recommendations.
- Ownership checks prevent representatives from viewing another institution's results.
- Administrators can review and filter all assessments and open any result.

### Dashboards and analytics
- Representative dashboard: latest score, best score, trend, category, dimension profile,
  profile completion, recommendations and history.
- Administrator dashboard: pending approvals, totals, average score, recent activity.
- Analytics from real database records: latest-per-university scores, dimension averages,
  category distribution, country statistics, monthly submission counts and top institutions.
- Up to five universities can be compared in a radar chart and table.
- Read-only JSON summary endpoint for verification and Postman.

### Resource hub
- Eight seeded reference resources across learning, implementation, responsible AI,
  governance, research and integration.
- Administrator create, edit, publish/unpublish and delete.
- Draft resources are hidden from public visitors.

## Technology stack

| Layer | Technology |
| --- | --- |
| Backend | Python, Django 5.2 |
| Templates | Django Templates, Django Forms |
| Database | SQLite locally, Neon PostgreSQL in production |
| Frontend | HTML5, CSS3, Bootstrap 5, ES6 JavaScript |
| Icons and charts | Font Awesome 6, Chart.js 4 |
| Auth and ORM | Django authentication, Django ORM |
| Static files | WhiteNoise |
| Production server | Gunicorn |
| Deployment | Render |
| Version control | Git and GitHub |
| Testing | Django Test Framework |
| API checks | Postman collection included |

No React, Next.js, Node.js, MongoDB or Firebase is used.

## Project structure

```text
GUCAIR/
├── accounts/            # Roles, profiles, registration, user management
├── analytics/           # Aggregate services, comparison, JSON summary
├── assessments/         # Question bank, scoring, forms, assessment views
├── config/              # Settings, root URLs, WSGI/ASGI
├── core/                # Landing, about, contact, health, error pages
├── dashboard/           # Representative and administrator dashboards
├── docs/                # Deployment, testing and API documentation
├── postman/             # Postman collection
├── resources/           # AI Resource Hub
├── static/              # Design system CSS, JavaScript, favicon
├── templates/           # All server-rendered templates
├── tests/               # 112 automated Django tests
├── universities/        # Institution profiles and approval workflow
├── build.sh             # Render build script
├── render.yaml          # Render Blueprint
├── Procfile             # Gunicorn process definition
└── manage.py
```

## Local setup (Windows PowerShell)

```powershell
cd GUCAIR
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
# Edit .env if needed; SQLite is used when DATABASE_URL is unset.

python manage.py migrate
python manage.py seed_data --demo
python manage.py createsuperuser   # or use create_admin with environment variables
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The seeded question bank and resource library are required
for the assessment to work. `--demo` additionally creates six **clearly labelled**
fictional institutions for analytics demonstration.

### Local quality-assurance accounts

These accounts exist only in the local SQLite database and are not created in production:

| Role | Username | Password |
| --- | --- | --- |
| Administrator | `gucair_admin` | `DevPass!2026` |
| Representative | `rep_demo` | `RepPass!2026` |

Production administrators are created from `ADMIN_USERNAME`, `ADMIN_PASSWORD` and
`ADMIN_EMAIL` during the Render build.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Production | Long random Django secret |
| `DEBUG` | Production | Must be `False` |
| `DATABASE_URL` | Production | Neon PostgreSQL URL with `sslmode=require` |
| `ALLOWED_HOSTS` | Production | Comma-separated allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | Production | Comma-separated trusted HTTPS origins |
| `RENDER_EXTERNAL_HOSTNAME` | Auto on Render | Added to hosts and CSRF origins automatically |
| `ADMIN_USERNAME` | Production | Bootstrap administrator username |
| `ADMIN_PASSWORD` | Production | Bootstrap administrator password |
| `ADMIN_EMAIL` | Optional | Bootstrap administrator email |
| `SEED_DEMO` | Optional | `True` seeds labelled demonstration institutions |
| `SECURE_SSL_REDIRECT` | Optional | Defaults to `True` when `DEBUG=False` |

See [`.env.example`](.env.example) and [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Automated tests

The project includes **112 Django tests** covering authentication, roles, permissions,
registration, university approval, assessment validation and scoring, analytics, resource
management, CSRF enforcement, health checks and error pages.

```powershell
.\.venv\Scripts\python.exe manage.py test
```

Latest local run:

```text
Ran 112 tests in 4.880s
OK
```

Test-only settings automatically use plain static-file storage and a fast password hasher,
so the suite does not depend on a collected `staticfiles` manifest. See
[`docs/TESTING.md`](docs/TESTING.md) for the full coverage map and manual QA checklist.

## Scoring example

If an institution selects 3 for all four questions in a dimension:

```text
raw points       = 3 + 3 + 3 + 3 = 12
maximum points   = 4 × 4 = 16
dimension score  = 12 ÷ 16 × 100 = 75.0  → Advanced
```

If every question across all 24 indicators is answered 4, the overall score is 100 and the
category is Leading. The overall score is not an average of rounded dimension scores; it is
computed from all raw responses, so every question carries equal weight.

## API and health endpoints

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health/` | Public | Database connectivity and record counts |
| `GET` | `/analytics/api/summary/` | Public | Aggregate consortium summary JSON |

The Postman collection in [`postman/`](postman/) documents these endpoints and the main
HTML routes.

## Security and data protection

- Passwords are hashed with Django's password hashers and validated on registration/change.
- CSRF middleware protects every state-changing request; POST-only destructive actions.
- All form input is validated server-side, not only in the browser.
- Role decorators and per-object ownership checks protect dashboards and results.
- Secrets and database credentials come from environment variables; `.env` is ignored.
- Production forces HTTPS, secure and HttpOnly cookies, HSTS, `X-Frame-Options: DENY`
  and content-type sniffing protection.
- `DEBUG=False` and explicit `ALLOWED_HOSTS` are required in production.
- Administrator deletion of a university requires typing the exact institution name.

## Demonstration data

`seed_data --demo` creates six fictional universities whose names begin with `Demo —`.
They are flagged `is_demo=True` and labelled “Demo record” in listings, profiles and
analytics, with a visible disclaimer. They exist only to demonstrate charts and comparison
features and must not be presented as real consortium members.

## Limitations

- Readiness results are self-reported and indicative, not audited or accreditation-grade.
- The free Render instance may cold-start after inactivity.
- Email delivery is not configured; the contact form stores messages for administrator review.
- Charts require the Chart.js CDN; core content remains usable without JavaScript.

## Author and course details

Student name, student ID, section and course details are recorded in the final submission
email and can be added here before submission.

## Licence and attribution

Built as an academic coursework project. Third-party libraries retain their respective
licences: Django (BSD), Bootstrap (MIT), Font Awesome (CC BY 4.0 / SIL OFL / MIT),
Chart.js (MIT).
