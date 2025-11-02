from ..enums.imap_encryption_mode import ImapEncryptionMode
from .default_values import ImapDumpConfigDefaults
from dataclasses import dataclass, asdict, field


@dataclass
class ImapDumpConfig:
    host: str = ImapDumpConfigDefaults.HOST

    console_log_level: str = ImapDumpConfigDefaults.CONSOLE_LOG_LEVEL
    port: int = ImapDumpConfigDefaults.PORT
    username: str = ImapDumpConfigDefaults.USERNAME
    password: str = ImapDumpConfigDefaults.PASSWORD
    database_file: str = ImapDumpConfigDefaults.DATABASE_FILE
    encryption_mode: ImapEncryptionMode = ImapDumpConfigDefaults.ENCRYPTION_MODE
    folder_regex: str = ImapDumpConfigDefaults.FOLDER_REGEX
    dump_folder: str = ImapDumpConfigDefaults.DUMP_FOLDER

    additional_config_files: list[str] = field(
        default_factory=lambda: ImapDumpConfigDefaults.ADDITIONAL_CONFIG_FILES
    )
    use_logfile: bool = ImapDumpConfigDefaults.USE_LOGFILE
    logfile_level: str = ImapDumpConfigDefaults.LOGFILE_LEVEL
    logfile_path: str = ImapDumpConfigDefaults.LOGFILE_PATH

    # flags
    recreate: bool = ImapDumpConfigDefaults.RECREATE
    mirror: bool = ImapDumpConfigDefaults.MIRROR
    dry_run: bool = ImapDumpConfigDefaults.DRY_RUN

    def update_from_dict(self, vars_dict: dict):
        props = asdict(self).keys()

        for key, value in vars_dict.items():
            if key not in props:
                raise ValueError(f"Prop '{key}' not in dataclass!")

            if getattr(ImapDumpConfigDefaults, key.upper()) == value:
                continue

            if getattr(self, key) != value:
                setattr(self, key, value)
