from dataclasses import dataclass, field


@dataclass
class ImapConfig:
    host: str
    username: str = None
    password: str = None
    port: int = 993
    ssl: bool = True
    ignored: list[str] = field(default_factory=list)