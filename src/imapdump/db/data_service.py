import logging
from sqlalchemy import URL, create_engine, Engine, select
from sqlalchemy.orm import Session

from ..models.mail import Base, Mail


class DataService:
    __engine: Engine = None
    __session = None
    _logger: logging.Logger

    def __init__(self, *, connection_string: str | URL = "sqlite://") -> None:
        self._logger = logging.getLogger(__name__)
        self._logger.info(
            f"Creating database engine with connection string '{connection_string}'"
        )

        # only echo SQL statements if we're logging at the debug level
        echo = self._logger.getEffectiveLevel() <= logging.DEBUG

        self.__engine = create_engine(connection_string, echo=echo)
        Base.metadata.create_all(self.__engine)
        self.__session = Session(self.__engine)

        assert self.__engine is not None
        assert self.__session is not None

    def __del__(self):
        self._logger.info("Shutting down")
        self.__session.close()
        
    def get_all_mails(self) -> list[Mail]:
        select_statement = select(Mail)
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

    def save(self, object):
        self.__session.add(object)

    def commit(self):
        self.__session.commit()
        self.__session.flush()
