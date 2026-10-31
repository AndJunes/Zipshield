# Contributing

Issues and pull requests are welcome.

## Setup

Each side has its own README with the full setup: [`backend/`](backend/README.md)
(FastAPI + uv + Postgres) and [`frontend/`](frontend/README.md) (Angular + pnpm).
`docker compose up -d --build` from the root brings up the whole stack.

## Before opening a PR

Backend, from `backend/`:

```bash
uv run pytest -q --cov=app      # coverage floor is 80%
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Frontend, from `frontend/`:

```bash
pnpm exec ng test --watch=false
pnpm exec ng build
```

Guidelines:

- One change per PR, with commit messages in the `type(scope): summary` style
  used in the history.
- Changes to access control come with a test that fails without the change —
  see the `backend/tests/test_*_authz.py` suites for the pattern.
- If you add a command or endpoint, match real-world insurance semantics and
  say in the PR how you checked the behavior.
