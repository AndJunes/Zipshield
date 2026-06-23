from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.security import verify_password


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
