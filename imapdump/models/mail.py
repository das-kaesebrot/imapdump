from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func
from .base import Base
import hashlib
import functools
import re


class Mail(Base):
    __tablename__ = "mails"
    id: Mapped[str] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column()
    folder: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    size: Mapped[int] = mapped_column()
    date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    modified: Mapped[datetime] = mapped_column(
        DateTime, onupdate=func.now(), default=func.now()
    )
    created: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    @functools.cached_property
    def filename(self):
        return f"{self.id}_{self.__replace_trash(self.title, truncate_length=16)}.eml"

    @staticmethod
    def generate_id(folder_name: str, message_id: str) -> str:
        h = hashlib.blake2b(digest_size=20)
        h.update(f"{folder_name}_{message_id}".encode())
        return h.hexdigest()

    # lol
    # https://stackoverflow.com/a/39059279
    # remove non-ascii chars and truncate to a fixed length
    @staticmethod
    def __replace_trash(unicode_string: str, truncate_length: int = 32) -> str:
        for i in range(0, len(unicode_string)):
            try:
                unicode_string[i].encode("ascii")
            except UnicodeEncodeError:
                # means it's non-ASCII
                unicode_string = unicode_string[i].replace(
                    ""
                )  # replacing it with nothing

        # replace spaces with underscores
        unicode_string = unicode_string.replace(" ", "_")
        # remove everything that's not a letter, a number, an underscore or a dash
        unicode_string = re.sub(r"[^a-zA-Z0-9_\-]+", "", unicode_string)
        return unicode_string[:truncate_length].rstrip("_")
