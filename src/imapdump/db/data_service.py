import logging
from sqlalchemy import URL, create_engine, Engine
from sqlalchemy.orm import Session

from ..models.mail import Base, Mail

class DataService:
    __engine: Engine = None
    __session = None
    _logger: logging.Logger

    def __init__(self, *, connection_string: str | URL = "sqlite://") -> None:
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"Creating database engine with connection string '{connection_string}'")
        
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

    def save_and_commit(self, object):
        self.__session.add(object)
        self.__session.commit()
        self.__session.flush()
        