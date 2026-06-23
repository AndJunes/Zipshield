from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import Base, engine
from app.core.exceptions import ConflictError, NotFoundError

# Import the models so SQLAlchemy registers them before creating the tables.
from app.auth import models as _auth                # noqa: F401
from app.supervisors import models as _supervisors  # noqa: F401
from app.agents import models as _agents            # noqa: F401
from app.clients import models as _clients          # noqa: F401
from app.policies import models as _policies        # noqa: F401
from app.claims import models as _claims            # noqa: F401

from app.auth.routes import router as auth_router
from app.supervisors.routes import router as supervisors_router
from app.agents.routes import router as agents_router
from app.clients.routes import router as clients_router
from app.policies.routes import router as policies_router
from app.claims.routes import router as claims_router
from app.dashboard.routes import router as dashboard_router

# Create the tables in the database if they do not exist yet.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Zipshield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200","http://localhost:58376"],
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
    return {"message": "Policy API is running"}
