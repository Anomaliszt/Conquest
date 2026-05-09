from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from api.app.models.base import Base


class RegistrationToken(Base):
    __tablename__ = "operator_registration_tokens"

    token_hash = Column(String, primary_key=True)
    used = Column(Integer, nullable=False, default=0)
    expires_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    used_at = Column(String, nullable=True)
    used_by_operator_id = Column(String, ForeignKey("operators.id", ondelete="SET NULL"), nullable=True)

    operator = relationship(
        "Operator",
        foreign_keys=[used_by_operator_id],
        back_populates="used_tokens",
    )