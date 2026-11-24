# API and smoke-check endpoints

GUCAIR is primarily server-rendered. Two read-only JSON endpoints support operational
verification, and the included Postman collection checks the main public routes.

## `GET /health/`

Public health check used by Render and uptime monitors.

Example response (HTTP 200):

```json
{
  "status": "ok",
  "database": "connected",
  "universities": 6,
  "assessments": 9
}
```

If the database cannot be reached, the endpoint returns HTTP 503:

```json
{"status": "error", "database": "unavailable"}
```

## `GET /analytics/api/summary/`

Public aggregate summary. It intentionally exposes no institution-identifying records.

Example response:

```json
{
  "approved_universities": 6,
  "completed_assessments": 9,
  "average_readiness": 62.5,
  "countries": 6
}
```

## Authentication

- `/accounts/login/` — GET renders the form and sets the `csrftoken` cookie; POST requires
  the CSRF token and valid credentials.
- Session cookies are HttpOnly and expire after 12 hours.
- Role-protected pages redirect anonymous users to sign-in and return HTTP 403 for the
  wrong role.

## Postman

Import `postman/GUCAIR.postman_collection.json`, set `baseUrl` to the local server or the
verified Render URL, and run the collection. The tests assert HTTP 200, health status,
numeric analytics fields, GUCAIR branding and CSRF cookie issuance.

## Main HTML routes

| Route | Access |
| --- | --- |
| `/` | Public |
| `/about/` | Public |
| `/universities/` | Public |
| `/universities/<slug>/` | Public for approved; owner/admin for pending |
| `/resources/` | Public |
| `/contact/` | Public |
| `/accounts/register/` | Public |
| `/accounts/login/` | Public |
| `/dashboard/` | Representative or administrator redirect |
| `/assessments/new/` | Approved representative |
| `/analytics/` | Authenticated |
| `/analytics/compare/` | Authenticated |
| `/universities/manage/` | Administrator |
| `/assessments/manage/` | Administrator |
| `/accounts/manage/users/` | Administrator |
| `/resources/manage/` | Administrator |
| `/manage/messages/` | Administrator |
| `/django-admin/` | Django superuser |
