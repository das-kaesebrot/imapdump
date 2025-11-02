import logging
from ..enums.imap_encryption_mode import ImapEncryptionMode


class ImapDumpConfigDefaults:
    HOST: str = "127.0.0.1"
    CONSOLE_LOG_LEVEL: str = logging.getLevelName(logging.INFO).lower()
    USE_LOGFILE: bool = False
    LOGFILE_PATH: str = "imapdump.log"
    LOGFILE_LEVEL: str = logging.getLevelName(logging.INFO).lower()
    PORT: int = 993
    USERNAME: str = None
    PASSWORD: str = None
    DATABASE_FILE: str = ".imapdump-cache.db"
    ENCRYPTION_MODE: ImapEncryptionMode = ImapEncryptionMode.SSL
    FOLDER_REGEX: str = "^.*$"
    RECREATE: bool = False
    DUMP_FOLDER: str = "dumped_mails"
    MIRROR: bool = False
    DRY_RUN: bool = False
    ADDITIONAL_CONFIG_FILES: list[str] = []
