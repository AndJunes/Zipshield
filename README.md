# Zipshield

Plataforma de gestión de reclamos de seguros con control de acceso por rol
(admin, supervisor, agente). Monorepo con dos proyectos:

- **`frontend/`** — SPA en Angular (dashboard, autenticación, gestión de
  supervisores, agentes, clientes y reclamos).
- **`backend/`** — API en FastAPI + SQLAlchemy + PostgreSQL (auth con JWT,
  filtrado por rol server-side y datos de demo).

## Estructura

```
Zipshield/
├── frontend/   # Angular SPA  (ver frontend/README.md)
└── backend/    # FastAPI API  (ver backend/README.md)
```

Cada subproyecto tiene su propio README con instrucciones de instalación y
ejecución.

## Puesta en marcha rápida

```bash
# Backend
cd backend
docker compose up -d
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload

# Frontend (en otra terminal)
cd frontend
pnpm install
pnpm start
```
