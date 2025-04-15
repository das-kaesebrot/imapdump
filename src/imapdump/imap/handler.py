from ..config.config import Config
from ..imap.dumper import ImapDumper
from ..db.data_service import DataService


class ImapDumpHandler:
    _dumpers: list[ImapDumper]

    def __init__(self, config: Config) -> None:
        self._dumpers = []
        for name, imap_config in config.servers.items():
            self._dumpers.append(
                ImapDumper(
                    config=imap_config, name=name, data_service=DataService(connection_string="sqlite:///test.db")
                )
            )

    def dump(self):
        for dumper in self._dumpers:
            dumper.dump()
