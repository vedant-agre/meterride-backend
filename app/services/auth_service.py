from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import UserLoginRequest, UserRegisterRequest
from app.services.exceptions import ConflictError, UnauthorizedError


class AuthService:
    @staticmethod
    def register_user(db: Session, data: UserRegisterRequest) -> User:
        # Check email uniqueness
        existing_email = db.query(User).filter(User.email == data.email).first()
        if existing_email:
            raise ConflictError("Email is already registered")

        # Check phone uniqueness
        existing_phone = db.query(User).filter(User.phone == data.phone).first()
        if existing_phone:
            raise ConflictError("Phone number is already registered")

        # Hash password and persist user
        password_hash = get_password_hash(data.password)
        user = User(
            name=data.name,
            email=data.email,
            phone=data.phone,
            password_hash=password_hash,
            role=data.role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, data: UserLoginRequest) -> tuple[str, User]:
        user = db.query(User).filter(User.email == data.email).first()
        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is inactive")

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
        token = create_access_token(data=token_data)
        return token, user
