from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.models import User
from app.auth.schemas import LoginRequest, SessionResponse, UserRead
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = service.authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    token, expires_at = create_access_token(user.id, user.role, user.ref_id)
    return SessionResponse(
        token=token,
        user=UserRead.model_validate(user),
        expires_at=expires_at,
    )


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
