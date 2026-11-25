# Testing and quality assurance

## Automated suite

Run from the project root:

```powershell
.\.venv\Scripts\python.exe manage.py test
```

The suite uses Django's test framework and an isolated in-memory SQLite database. Test
settings activate automatically when `test` is present in `sys.argv`:

- plain static-file storage, avoiding a dependency on `collectstatic`;
- MD5 password hashing for speed (production hashing is unchanged).

Latest verified result: **112 tests, 0 failures, 0 errors**.

```text
Found 112 test(s).
System check identified no issues (0 silenced).
Ran 112 tests in 2.885s
OK
```

## Coverage map

| Module | Tests | What is verified |
| --- | --- | --- |
| `tests/test_accounts.py` | 19 | Registration transaction, duplicate email/name, short description, login/logout, protected redirects, profile updates, password change, admin user search, role changes, self-protection, hashing, admin profile promotion |
| `tests/test_universities.py` | 19 | Public listing visibility, search, country filter, approved/pending detail access, owner/admin access, registration, editing, duplicate names, approval, rejection, name-confirmed deletion, admin edits |
| `tests/test_assessments.py` | 20 | 24-question bank, 0/50/100 scoring, per-dimension maths, missing/out-of-range answers, category boundaries, canonical ordering, recommendations, submission flow, pending/unlinked blocking, ownership, admin detail access, delta, history, management, deletion cascade |
| `tests/test_analytics.py` | 15 | Latest-per-university selection, consortium totals, dimension order/averages, category distribution, country statistics, monthly buckets, public coverage, comparison rows, login protection, comparison limits, JSON API |
| `tests/test_resources.py` | 12 | Published-only listing, search/category filters, draft visibility, related resources, unique slugs, admin CRUD, role protection |
| `tests/test_core.py` | 13 | Landing/about/contact pages, contact persistence and validation, CSRF rejection, health JSON, custom 404, security headers, admin message management, POST-only toggle |

Additional checks performed manually in Chrome:

- Responsive public pages at desktop and mobile widths.
- Representative registration and sign-in.
- Assessment submission through the rendered form.
- Representative dashboard, history and result charts.
- Administrator dashboard, approvals, resources, messages and analytics.
- No uncaught JavaScript console errors on the main pages.

## Manual QA checklist

1. **Public**
   - Open `/`, `/about/`, `/universities/`, `/resources/`, `/contact/`.
   - Submit a valid contact message; confirm the success message.
   - Submit an invalid message; confirm validation errors and no record created.
   - Confirm a draft resource returns 404 without administrator sign-in.
2. **Representative**
   - Register a new representative and confirm the university is pending.
   - Confirm assessment submission is blocked while pending.
   - Sign in as an approved representative and complete all 24 questions.
   - Confirm the result page, score category, recommendations and history.
   - Edit the institutional profile and change the password.
   - Attempt to open another institution's result URL; expect 404.
3. **Administrator**
   - Approve and reject pending universities, including a review note.
   - Create, edit and delete a resource.
   - Filter users, toggle activation, change a role.
   - Open any assessment result and confirm the admin view.
   - Resolve a contact message.
   - Confirm deletion requires the exact university name.
4. **Security**
   - Confirm state-changing endpoints reject GET (405).
   - Confirm unauthenticated dashboard access redirects to sign-in.
   - Confirm a representative receives 403 on administrator pages.

## Limitations of the automated suite

- No live PostgreSQL integration test is run locally; production uses Render PostgreSQL and
  is verified after deployment through `/health/` and the deployed UI.
- Email is console-backed locally; the contact form persists messages instead of sending.
- Browser visuals are verified manually rather than through a headless visual-regression
  service.
