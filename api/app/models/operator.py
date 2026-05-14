from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from api.app.models.base import Base


class Operator(Base):
    __tablename__ = "operators"

    id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(String, nullable=False)

    used_tokens = relationship(
        "RegistrationToken",
        back_populates="operator",
        foreign_keys="RegistrationToken.used_by_operator_id",
    )