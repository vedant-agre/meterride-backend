from uuid import UUID
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserUpdateRequest
from app.services.exceptions import ConflictError, NotFoundError


class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        return user

    @staticmethod
    def update_user_profile(
        db: Session, user: User, data: UserUpdateRequest
    ) -> User:
        if data.phone is not None and data.phone != user.phone:
            existing_phone = (
                db.query(User)
                .filter(User.phone == data.phone, User.id != user.id)
                .first()
            )
            if existing_phone:
                raise ConflictError("Phone number is already in use")
            user.phone = data.phone

        if data.name is not None:
            user.name = data.name

        db.commit()
        db.refresh(user)
        return user
