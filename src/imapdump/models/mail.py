from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func
from .base import Base


class Mail(Base):
    __tablename__ = "mails"
    id: Mapped[str] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column()
    folder: Mapped[str] = mapped_column()
    rfc822: Mapped[bytes] = mapped_column()
    modified: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now(), default=func.now())
    created: Mapped[datetime] = mapped_column(DateTime, default=func.now())
