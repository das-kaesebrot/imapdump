from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func
from .base import Base


class Mail(Base):
    __tablename__ = "mails"
    uid: Mapped[str] = mapped_column(primary_key=True)
    rfc822: Mapped[str] = mapped_column()
    envelope: Mapped[str] = mapped_column()
    modified: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now())
    created: Mapped[datetime] = mapped_column(DateTime, default=func.now())
