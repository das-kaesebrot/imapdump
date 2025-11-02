from ..enums.imap_encryption_mode import ImapEncryptionMode
from .default_values import ImapDumpConfigDefaults
from dataclasses import dataclass


@dataclass
class ImapDumpFileConfig:
    host: str
    port: int = ImapDumpConfigDefaults.PORT
    username: str = ImapDumpConfigDefaults.USERNAME
    password: str = ImapDumpConfigDefaults.PASSWORD
    database_file: str = ImapDumpConfigDefaults.DATABASE_FILE
    encryption_mode: ImapEncryptionMode = ImapDumpConfigDefaults.ENCRYPTION_MODE
    folder_regex: str = ImapDumpConfigDefaults.FOLDER_REGEX
    dump_folder: str = ImapDumpConfigDefaults.DUMP_FOLDER
