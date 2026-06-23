# Zipshield API

FastAPI + SQLAlchemy + Postgres backend que replica los datos del frontend
mockeado: supervisores, agentes, clientes (con history), reclamos y
autenticación con bcrypt/JWT y filtrado por rol.

## Setup

```bash
# 1. Levantar Postgres
docker compose up -d postgres

# 2. Crear venv e instalar deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configurar env
cp .env.example .env

# 4. Aplicar migraciones
alembic upgrade head

# 5. Poblar con los datos del frontend mockeado
python -m scripts.seed

# 6. Levantar la API
uvicorn app.main:app --reload
```

API en `http://localhost:8000`, docs en `http://localhost:8000/docs`.

## Cuentas de demo

- Admin: `admin@zipshield.io` / `admin1234`
- Supervisor (cualquiera): `<nombre>.<apellido>@zipshield.io` / `super1234`
  - p.ej. `maria.fernandez@zipshield.io`
- Agente (cualquiera): `<nombre>.<apellido>@zipshield.io` / `agent1234`
  - p.ej. `mateo.aguirre@zipshield.io`

## Filtros por rol (server-side)

| Endpoint | admin | supervisor | agent |
|---|---|---|---|
| `GET /supervisors` | todos | solo él | `[]` |
| `GET /agents` | todos | sus agentes | solo él |
| `GET /clients` | todos | clientes de sus agentes | solo sus clientes |
| `GET /claims` | todos | claims de sus clientes (vía agentes) | claims de sus clientes |

Mutaciones (POST/PATCH/DELETE) con guards específicos: `/supervisors` solo
admin; `/agents` admin+supervisor; resto cualquier autenticado.
