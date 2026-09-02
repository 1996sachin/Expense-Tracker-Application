# Pocketly Expense Tracker

A Dockerized personal-finance application with Django REST Framework, MySQL, Redis/Celery, JWT authentication, and a React dashboard.

## Run locally

1. Copy `.env.example` to `.env` and replace the secret and database credentials as needed: `cp .env.example .env`.
2. Run `docker compose up --build`.
3. Open the frontend at `http://localhost:5173`; API documentation is at `http://localhost:8000/api/docs/`.

The backend creates development migrations when the container starts, then runs them against MySQL. For a production deployment, generate and commit these migrations during CI/release preparation.

MySQL is exposed to the host on port `3307` to avoid clashes with an existing local MySQL service; containers use the internal `db:3306` connection.

## API highlights

- `POST /api/auth/register/`, `/login/`, `/refresh/`, `/google/`, and `GET/PATCH /me/`
- CRUD routes for `/api/accounts/`, `/api/categories/`, `/api/transactions/`, and `/api/budgets/`
- `GET /api/accounts/summary/` for net worth and `GET /api/transactions/insights/?period=month` for dashboard data

Transfers enforce ownership and currency compatibility. Transaction creates, edits, and deletes adjust account balances automatically. Celery Beat invokes recurring-transaction generation daily.

## Authentication configuration

Set `GOOGLE_CLIENT_ID` in `.env` to the OAuth **Web application client ID** from Google Cloud Console. Add `http://localhost:5173` to its authorized JavaScript origins for local development. This identifier is intentionally provided to Vite as `VITE_GOOGLE_CLIENT_ID`; it is public and is not a client secret. The Django API independently validates every credential's audience and Google `sub` identifier before issuing Pocketly JWTs.

## Gmail SMTP configuration

Enable 2-Step Verification on the sending Google account, then create a Google **App Password**. Never use the account's normal password and never commit `.env`. Configure SMTP in `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-google-app-password
SMTP_USE_TLS=true
EMAIL_FROM_NAME=Pocketly
EMAIL_FROM_ADDRESS=your-email@gmail.com
FRONTEND_URL=http://localhost:5173
```

`MFA_ENCRYPTION_KEY` should be a Fernet key generated and held as a deployment secret (for example, `Fernet.generate_key()` in a secure local console). If it is not set, development derives an encryption key from Django's secret key; production should always set an independent value.

After changing `.env`, run `docker compose up -d --build` to recreate the frontend with the Google client ID and reload backend configuration.
