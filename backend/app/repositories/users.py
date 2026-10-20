"""User lookup."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Role, User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(
            select(User).options(joinedload(User.role)).where(User.email == email)
        )

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.scalar(
            select(User).options(joinedload(User.role)).where(User.id == user_id)
        )

    def get_role(self, name: str) -> Role:
        role = self.session.scalar(select(Role).where(Role.name == name))
        if role is None:
            raise RuntimeError(f"Role {name} is not seeded")
        return role
