# SecureVault

A Zero Trust API Key Manager built on the principles of NIST SP 800-207. Demonstrates production-grade implementation of three-zone API microsegmentation, JWT-based authentication, replay-attack detection using cryptographic nonces, and a real-time security operations dashboard.

**Live demo:** https://securevaultte.netlify.app
**API:** https://securevault-api-s6i9.onrender.com

> Note: the backend runs on Render's free tier and spins down after 15 minutes of inactivity. The first request after a quiet period takes ~30 seconds to wake up. Subsequent requests are fast.

## Architecture

Three-zone Zero Trust enforcement model, every request flowing through the appropriate zone gate as a FastAPI dependency:

- **Zone 1 — Public.** Registration and login. No auth required.
- **Zone 2 — Authenticated.** JWT-required CRUD on API keys and audit logs.
- **Zone 3 — Privileged.** Rotation and revocation. Requires JWT plus a fresh single-use nonce validated against a 30-second replay-detection window.

Zone enforcement is decoupled from business logic — adding security to any endpoint is a single dependency injection.

## Stack

**Backend:** FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, bcrypt, python-jose
**Frontend:** Angular 21 (standalone components), TypeScript, RxJS
**Infrastructure:** Render (API + DB), Netlify (SPA), GitHub Actions

## Security Features

- Bcrypt password hashing (12 rounds)
- JWT access + refresh token pattern with `jti` for future per-token revocation
- API keys stored as bcrypt hashes — raw key returned exactly once at creation, never persisted
- UUID4 primary keys throughout — no sequential ID enumeration
- Cryptographic nonces for replay detection (NIST SP 800-207 §3.3)
- Full audit trail with structured event types and JSONB metadata
- Admin telemetry dashboard with system-wide event aggregation
- IPv6-safe IP logging via X-Forwarded-For
- Production Swagger docs disabled to avoid schema disclosure

## Run locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in DATABASE_URL and JWT_SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
ng serve
```

## References

- NIST SP 800-207 — Zero Trust Architecture
- OWASP IoT Top 10 — mitigates #2 (Insecure Network Services) and #7 (Insecure Data Transfer)