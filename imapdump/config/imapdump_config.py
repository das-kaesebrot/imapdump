from ..enums.imap_encryption_mode import ImapEncryptionMode
from .default_values import ImapDumpConfigDefaults
from dataclasses import dataclass


@dataclass
class ImapDumpConfig:
    host: str
    
    loglevel: str = ImapDumpConfigDefaults.LOGLEVEL
    port: int = ImapDumpConfigDefaults.PORT
    username: str = ImapDumpConfigDefaults.USERNAME
    password: str = ImapDumpConfigDefaults.PASSWORD
    database_file: str = ImapDumpConfigDefaults.DATABASE_FILE
    encryption_mode: ImapEncryptionMode = ImapDumpConfigDefaults.ENCRYPTION_MODE
    folder_regex: str = ImapDumpConfigDefaults.FOLDER_REGEX
    dump_folder: str = ImapDumpConfigDefaults.DUMP_FOLDER
    
    # flags
    force_dump: bool = ImapDumpConfigDefaults.FORCE_DUMP
    mirror: bool = ImapDumpConfigDefaults.MIRROR
    dry_run: bool = ImapDumpConfigDefaults.DRY_RUN
    