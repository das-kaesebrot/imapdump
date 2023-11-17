from typing import Dict
from dataclasses import dataclass, field

from ..config.imap_config import ImapConfig


@dataclass
class Config:
    servers: Dict[str, ImapConfig] = field(default_factory=dict)
    dump_folder: str = "dump"
