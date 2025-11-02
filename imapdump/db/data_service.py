import logging
import os
import sqlite3
from sqlalchemy import URL, create_engine, Engine, select, delete
from sqlalchemy.orm import Session

from ..models.mail import Base, Mail


class DataService:
    __engine: Engine = None
    __session = None
    _logger: logging.Logger

    def __init__(
        self,
        *,
        connection_string: str | URL = "sqlite://",
        recreate: bool = False,
        dry_run: bool = False,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._logger.info(
            f"Creating database engine with connection string '{connection_string}'"
        )

        # only echo SQL statements if we're logging at the debug level
        echo = self._logger.getEffectiveLevel() <= logging.DEBUG

        existing_db = None
        if dry_run:
            # bruh this is some C++ style substring handling
            existing_db_file = connection_string[len("sqlite:///") :]
            connection_string = "sqlite:///:memory:"
            if os.path.isfile(existing_db_file):
                existing_db = sqlite3.connect(existing_db_file)

        self.__engine = create_engine(connection_string, echo=echo)

        if existing_db:
            self._logger.info(
                f"Copying existing database into in-memory db for dry run"
            )
            conn = self.__engine.raw_connection().dbapi_connection
            existing_db.backup(conn)
            existing_db.close()

        if recreate:
            Base.metadata.drop_all(self.__engine)
            self._logger.info("Dropped existing database")

        Base.metadata.create_all(self.__engine)
        self.__session = Session(self.__engine)

        assert self.__engine is not None
        assert self.__session is not None

    def close_db(self):
        self._logger.info("Shutting down")
        self.__session.invalidate()
        self.__engine.dispose()

    def get_all_mails(self) -> list[Mail]:
        select_statement = select(Mail)
        return self.__session.scalars(select_statement).all()

    def get_all_mail_folders(self) -> list[str]:
        select_statement = select(Mail.folder).distinct()
        return self.__session.scalars(select_statement).all()

    def get_mail_by_id(self, id) -> Mail | None:
        select_statement = select(Mail).where(Mail.id.is_(id))

        return self.__session.scalars(select_statement).one_or_none()

    def get_or_create_mail_by_id(self, id) -> Mail | None:
        select_statement = select(Mail).where(Mail.id.is_(id))

        mail = self.__session.scalars(select_statement).one_or_none()

        if not mail:
            mail = Mail()
            mail.id = id

        return mail

    def mail_has_to_be_created_or_updated(self, id, size: int) -> bool:
        mail = self.get_mail_by_id(id)

        return mail is None or mail.size != size

    def save_and_commit(self, object):
        self.save(object)
        self.commit()

    def save_all(self, objects: list):
        self.__session.add_all(objects)

    def save_all_and_commit(self, objects: list):
        self.save_all(objects)
        self.commit()

    def remove_diff(self, ids: list[str]):
        """
        Removes all that messages that are not in the given list from the database
        """
        delete_statement = delete(Mail).where(Mail.id.not_in(ids))
        self.__session.execute(delete_statement)
        self.commit()

    def save(self, object):
        self.__session.add(object)

    def remove_all_mails(self):
        delete_statement = delete(Mail)
        self.__session.execute(delete_statement)
        self.commit()

    def commit(self):
        self.__session.commit()
        self.__session.flush()
