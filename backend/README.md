# Zipshield API

FastAPI + SQLAlchemy + PostgreSQL backend: supervisors, agents, clients (with
claim history), policies with a priced coverage catalog, claims with AI review,
and JWT authentication with role-scoped queries.

## Setup

Requirements: Python 3.13+, [uv](https://docs.astral.sh/uv/) and Docker (for
Postgres).

```bash
# 1. Start Postgres (the compose file lives at the repo root)
docker compose -f ../docker-compose.yml up -d postgres

# 2. Install dependencies
uv sync

# 3. Configure the environment
cp .env.example .env     # add OPENROUTER_API_KEY to try the real AI review

# 4. Apply migrations (Alembic owns the schema)
uv run alembic upgrade head

# 5. Seed demo data (~130 clients, 44 policies, 50 claims)
uv run python -m scripts.seed

# 6. Run the API
uv run uvicorn app.main:app --reload
```

API at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.

## Checks

```bash
uv run pytest -q                 # 90+ tests, SQLite, no Docker needed
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

## Demo accounts

- Admin: `admin@zipshield.io` / `admin1234`
- Supervisor (any): `<first>.<last>@zipshield.io` / `super1234` — e.g. `maria.fernandez@zipshield.io`
- Agent (any): `<first>.<last>@zipshield.io` / `agent1234` — e.g. `mateo.aguirre@zipshield.io`

Passwords hash with Argon2; pre-existing bcrypt hashes still verify.

## Role scoping (server-side)

| Endpoint | admin | supervisor | agent |
|---|---|---|---|
| `GET /supervisors` | all | themselves | `[]` |
| `GET /agents` | all | their agents | themselves |
| `GET /clients` | all | their agents' clients | their clients |
| `GET /policies` | all | their agents' policies | their clients' policies |
| `GET /claims` | all | their agents' claims | their clients' claims |

Writes re-check ownership: creating a claim requires a policy inside the
actor's scope, and the claimant is derived from that policy on the server.
Mutations carry explicit guards: `/supervisors` is admin-only, `/agents` is
admin+supervisor, the rest any authenticated role within its scope.
