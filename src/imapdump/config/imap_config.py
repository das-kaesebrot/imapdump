from dataclasses import dataclass


@dataclass
class ImapConfig:
    host: str
    username: str = None
    password: str = None
    port: int = 993
    ssl: bool = True
