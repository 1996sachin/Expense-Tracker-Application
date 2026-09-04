# Pocketly

> A secure, full-stack personal finance workspace for tracking money, planning budgets, and understanding spending habits.

![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![Django](https://img.shields.io/badge/Django-5-092E20?logo=django&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

Pocketly brings accounts, transactions, budgets, recurring payments, and spending insights into one clean dashboard. It is built as a Dockerized React and Django REST Framework application, with background processing powered by Celery and Redis.

## What you can do

- Track income, expenses, and transfers across multiple accounts
- Organize transactions with custom income and expense categories
- See net-worth, monthly trends, and category-level spending insights
- Create and monitor budgets
- Schedule recurring transactions that are generated automatically
- Sign in securely with email/password or Google OAuth
- Protect accounts with JWT authentication, optional MFA, password resets, and login notifications

## Preview

<!-- Add a real dashboard capture here after signing in locally.
     Recommended file: assets/dashboard.png -->

![Pocketly dashboard preview](assets/dashboard.png)

> To refresh this image, sign in at `http://localhost:5175` and save a dashboard screenshot as `assets/dashboard.png`.

## Tech stack

| Layer | Technologies |
| --- | --- |
| Frontend | React, Vite, React Router, TanStack Query, Recharts |
| Backend | Django, Django REST Framework, Simple JWT, drf-spectacular |
| Data & jobs | MySQL, Redis, Celery, Celery Beat |
| Infrastructure | Docker, Docker Compose |
| Authentication | Email/password, Google OAuth, MFA |

## Getting started

### Prerequisites

- Docker Desktop or Docker Engine with Docker Compose

### Run locally

1. Clone the repository and enter the project directory.

   ```bash
   git clone https://github.com/1996sachin/Expense-Tracker-Application.git
   cd Expense-Tracker-Application
   ```

2. Create your local environment file.

   ```bash
   cp .env.example .env
   ```

3. Update `.env` with your own secrets and database credentials. Never commit this file.

4. Start the application.

   ```bash
   docker compose up --build
   ```

5. Open the app and API documentation.

   - App: `http://localhost:5175`
   - API docs: `http://localhost:8001/api/docs/`

MySQL is available on host port `3307`; services within Docker use `db:3306`.

### Access from another device on your network

Set `FRONTEND_ORIGIN` and `VITE_API_URL` in `.env` to the Docker host's LAN address, then restart the services:

```bash
docker compose up -d --build
```

Open `http://<HOST-LAN-IP>:5175` on the other device. The API is available at `http://<HOST-LAN-IP>:8001/api/`. Both devices must be on the same network, and the host firewall must allow TCP ports `5175` and `8001`.

## API overview

| Area | Endpoints |
| --- | --- |
| Authentication | `POST /api/auth/register/`, `/login/`, `/refresh/`, `/google/` |
| Profile | `GET` / `PATCH /api/auth/me/` |
| Finance | CRUD for `/api/accounts/`, `/api/categories/`, `/api/transactions/`, and `/api/budgets/` |
| Insights | `/api/accounts/summary/` and `/api/transactions/insights/?period=month` |

Transfers validate account ownership and currency compatibility. Creating, editing, or deleting a transaction updates the related account balance automatically. Celery Beat checks for recurring transactions daily.

## Environment notes

Google sign-in requires a **Web application** OAuth client (not an Android, iOS, or desktop client). Set its ID as `GOOGLE_CLIENT_ID`, then in the same client in Google Cloud Console add the exact browser origin `http://localhost:5175` under **Authorized JavaScript origins**. Do not add a path or a trailing slash. The client ID in `.env` and the one configured for that origin must be the same. If you use another hostname or port, add that exact origin too.

`FRONTEND_ORIGIN` must match the app URL; the Docker default is `http://localhost:5175`. Restart the frontend after changing either Google variable. A browser message saying “The given origin is not allowed for the given client ID” is enforced by Google before this app receives a credential, so it can only be resolved by correcting that OAuth Console allowlist.

Database migrations are versioned in `backend/*/migrations`. Startup applies those committed migrations with retries while MySQL is becoming available; do not run `makemigrations` automatically in a long-running container.

For email delivery, use a Gmail App Password—not your normal Google password—and configure the SMTP values in `.env`. In production, set an independent `MFA_ENCRYPTION_KEY` (a Fernet key) rather than relying on the development fallback.

After changing `.env`, rebuild the services:

```bash
docker compose up -d --build
```

## Security

- `.env` is excluded from version control; use `.env.example` as the configuration template.
- JWTs secure API access.
- Google credentials are validated server-side before Pocketly issues tokens.
- MFA secrets are encrypted, and sensitive account events can trigger email notifications.

## License

This project is available for personal and educational use.
