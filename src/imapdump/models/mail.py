from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func
from .base import Base
from hashlib import sha256


class Mail(Base):
    __tablename__ = "mails"
    id: Mapped[str] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column()
    folder: Mapped[str] = mapped_column()
    rfc822: Mapped[bytes] = mapped_column()
    size: Mapped[int] = mapped_column()
    modified: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now(), default=func.now())
    created: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    @staticmethod
    def generate_id(folder_name: str, message_id: str) -> str:
        return sha256(f"{folder_name}_{message_id}".encode()).hexdigest()
    