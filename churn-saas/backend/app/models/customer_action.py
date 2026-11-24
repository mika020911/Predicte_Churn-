from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CustomerAction(Base):
    """Journal des actions de rétention menées pour un client.

    Le statut `cancelled` remplace une suppression physique : l'historique est
    conservé. L'organisation se déduit du client (pas de colonne dédiée).
    """

    __tablename__ = "customer_actions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # call | email | discount | onboarding | other
    action_type = Column(String(20), nullable=False)
    # todo | in_progress | done | cancelled
    status = Column(
        String(20), nullable=False, default="todo", server_default="todo"
    )
    note = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    customer = relationship("Customer", back_populates="actions")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
