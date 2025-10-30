from ..enums.imap_encryption_mode import ImapEncryptionMode
from dataclasses import dataclass


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
    dump_folder: str = None
    mirror: bool = False
    dry_run: bool = False
    