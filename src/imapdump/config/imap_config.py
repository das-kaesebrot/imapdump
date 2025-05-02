from ..enums.imap_encryption_mode import ImapEncryptionMode
from dataclasses import dataclass, field


@dataclass
class ImapDumpConfig:
    loglevel: str
    host: str
    port: int = 993
    username: str = None
    password: str = None
    database_file: str = None
    encryption_mode: ImapEncryptionMode = ImapEncryptionMode.SSL
    folder_regex: str = "^.*$"
    config: dict = None
    force_dump: bool = False
