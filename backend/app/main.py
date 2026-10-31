from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError

from app.auth.routes import router as auth_router
from app.supervisors.routes import router as supervisors_router
from app.agents.routes import router as agents_router
from app.clients.routes import router as clients_router
from app.policies.routes import router as policies_router
from app.claims.routes import router as claims_router
from app.dashboard.routes import router as dashboard_router

# The schema is owned by Alembic: run `alembic upgrade head` before starting.
app = FastAPI(title="Zipshield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Translate domain exceptions into clean HTTP responses, in one central place.
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


app.include_router(auth_router)
app.include_router(supervisors_router)
app.include_router(agents_router)
app.include_router(clients_router)
app.include_router(policies_router)
app.include_router(claims_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {"name": "Zipshield API", "docs": "/docs"}
