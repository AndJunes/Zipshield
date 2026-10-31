from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.security import hash_password, verify_password

# Verified when the email is unknown, so a login attempt takes the same time
# whether or not the account exists.
_DUMMY_HASH = hash_password("dummy-password-for-constant-time")


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
