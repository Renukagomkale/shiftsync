# ShiftSync

A shift scheduling and shift-swapping web app for small businesses such as cafes, shops and clinics. It replaces the WhatsApp group and the Excel sheet with one weekly schedule that checks the rules for you.

Live demo: add the link here after deploying.

![Weekly schedule](docs/schedule.png)

## Why it exists

Part-time schedules usually live in chat groups and spreadsheets. Double bookings happen, swaps are arranged informally and nobody knows who is covering what. ShiftSync gives managers one place to plan the week and gives workers a clear way to swap shifts, with the manager's approval and without breaking scheduling rules.

## Features

- Two roles. A manager creates a business and shares a join code. Workers join with that code.
- Weekly calendar. Managers create, edit, delete and assign shifts. Workers see the whole schedule and their own shifts.
- Conflict detection when assigning a shift:
  - no overlapping shifts for the same person (back-to-back shifts are not an overlap)
  - a weekly hour limit per person
  - a minimum rest gap between shifts
  - both limits are configurable per business, and weeks follow the business timezone
- Swap flow: a worker asks for a swap, a coworker accepts (or anyone can take an open swap), then the manager approves. The shift only moves after both steps.
- Atomic approval. Approving a swap runs in one database transaction with row locks and re-checks every rule, so two approvals cannot double book a person.
- In-app notifications for every swap event.
- Manager dashboard with shifts that need cover, hours per person this week and swaps waiting for approval.
- Loading, empty and error states, and a layout that works on phones.

![Swap requests](docs/swaps.png)
![Manager dashboard](docs/dashboard.png)

## Tech stack

| Part | Choice |
|---|---|
| Backend | Django 5, Django REST Framework |
| Auth | djangorestframework-simplejwt (access and refresh tokens), custom user model with email login |
| Frontend | React 18 (Vite), Tailwind CSS 4, React Router, Axios, date-fns, Lucide icons |
| Database | SQLite in development, PostgreSQL in production |
| Tests | Django TestCase and APITestCase |

## Architecture

```
React (Vite)  --JWT over HTTPS-->  Django REST API  -->  SQLite / PostgreSQL
                                        |
                  accounts/    users, businesses, join codes
                  scheduling/  shifts, swaps, notifications, dashboard
                    services/
                      conflicts.py       overlap, weekly hours, rest gap
                      swaps.py           swap state machine, atomic approval
                      notifications.py   notification text and fan-out
                      summary.py         dashboard numbers
```

Swap states:

```
pending_peer --accept--> pending_manager --approve--> approved
     |                         |
     |--decline--> rejected    |--reject--> rejected
     |--cancel (requester)--> cancelled
```

Business rules live in `scheduling/services`, not in views or serializers, so they can be tested directly and reused. The swap approval and the shift assignment call the same conflict check.

## Run it on Windows

You need Python 3.12 or newer and Node.js 20 or newer.

Backend:

```powershell
cd backend
python -m venv venv
Set-ExecutionPolicy -Scope Process Bypass
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Paste the generated value after `SECRET_KEY=` in `backend\.env`, then:

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Frontend, in a second terminal:

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open http://localhost:5173. Vite reads `.env` only at startup, so restart `npm run dev` after editing it.

`seed_demo` creates a cafe with a manager, four workers, two weeks of shifts and three swap requests in different states. Password for every demo account is `Demo-pass-2026`.

| Role | Email |
|---|---|
| Manager | priya@shiftsync.test |
| Worker | maya@shiftsync.test, arjun@shiftsync.test, sana@shiftsync.test, dev@shiftsync.test |

Run `python manage.py seed_demo --reset` to rebuild the demo data.

## Environment variables

Backend (`backend/.env`):

| Name | Purpose |
|---|---|
| SECRET_KEY | Required. Signs sessions and tokens. |
| DEBUG | `True` for local development. |
| ALLOWED_HOSTS | Comma separated hostnames. |
| CORS_ALLOWED_ORIGINS | Comma separated frontend URLs allowed to call the API. |
| DATABASE_URL | Optional. A PostgreSQL URL. SQLite is used when empty. |
| CSRF_TRUSTED_ORIGINS | Comma separated https origins, needed for the admin in production. |
| HTTPS_ONLY | `True` in production. Redirects to https and marks cookies secure. |

Frontend (`frontend/.env`):

| Name | Purpose |
|---|---|
| VITE_API_URL | Base URL of the API, for example `http://localhost:8000/api`. |

## API reference

All paths are under `/api/`. Everything except register, login and refresh needs `Authorization: Bearer <access token>`. Errors look like `{"message": "...", "errors": {...}}`. Lists are paginated.

| Method and path | Who | What |
|---|---|---|
| POST `/auth/register/` | anyone | Create an account, returns user and tokens |
| POST `/auth/login/` | anyone | Email and password, returns tokens |
| POST `/auth/refresh/` | anyone | New access token from a refresh token |
| GET `/auth/me/` | signed in | Current user and business |
| POST `/business/` | manager | Create the business |
| GET, PATCH `/business/` | member, manager | Read, or change name and scheduling rules |
| POST `/business/join/` | worker | Join with a join code |
| GET `/business/members/` | member | Names and roles of the team |
| GET `/shifts/?from=&to=` | member | Shifts in a date range |
| POST `/shifts/` | manager | Create a shift, optionally assigned |
| PATCH, DELETE `/shifts/:id/` | manager | Edit or delete a shift |
| GET `/shifts/mine/` | member | The current user's shifts |
| POST `/swaps/` | shift owner | Request a swap, with a target or open to anyone |
| GET `/swaps/?status=` | member | Swaps visible to the user |
| PATCH `/swaps/:id/` | varies | Body `{"action": "accept\|decline\|approve\|reject\|cancel"}` |
| GET `/notifications/` | signed in | Own notifications, `?unread=true` to filter |
| PATCH `/notifications/:id/` | owner | Mark one as read |
| POST `/notifications/read-all/` | signed in | Mark all as read |
| GET `/notifications/unread-count/` | signed in | Number of unread notifications |
| GET `/dashboard/summary/?week=` | manager | Gaps, hours per person, pending swaps |

## Tests

```powershell
cd backend
python manage.py test
```

The tests cover the conflict rules including edge cases (back-to-back shifts, rest gap boundaries, week boundaries in another timezone), every transition of the swap state machine, permission and business isolation checks, notifications, the dashboard numbers and the seed data.

## Deployment

Frontend on Vercel, backend on Render, database on a hosted PostgreSQL (for example Neon). Free tiers change, so check their current limits.

1. Create a PostgreSQL database and copy its connection string.
2. Backend on Render: root directory `backend`, build command `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`, start command `gunicorn config.wsgi`. Set `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `DATABASE_URL`, `CORS_ALLOWED_ORIGINS` (your Vercel URL), `CSRF_TRUSTED_ORIGINS` (your Render URL) and `HTTPS_ONLY=True`.
3. Frontend on Vercel: root directory `frontend`, set `VITE_API_URL` to your Render URL plus `/api`. `vercel.json` makes page refreshes work.
4. Optional demo data: from your own machine run `$env:DATABASE_URL="<connection string>"; python manage.py seed_demo`.

## Limitations

- Notifications are in-app and fetched by polling every 30 seconds. There are no WebSockets, email or push.
- The row locking used for approvals only takes effect on PostgreSQL. SQLite ignores `select_for_update`, so concurrent approvals are only protected in production. The tests check the double-booking scenario one request after another, not truly in parallel.
- Access and refresh tokens are kept in `localStorage`, which is simple but exposed to XSS. An httpOnly cookie would be safer.
- Managers cannot override a conflict, and a shift belongs to the week in which it starts.
- One business per account and no worker availability or time-off requests.

## Future work

- Worker availability and time-off requests
- Recurring shift templates and copying a week
- Email or push notifications
- A manager override for conflicts, with a reason
- Concurrency tests against PostgreSQL
