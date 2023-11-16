from ..config.config import Config
from ..imap.dumper import ImapDumper


class ImapDumpHandler:
    _dumpers: list[ImapDumper]
    
    def __init__(self, config: Config) -> None:
        self._dumpers = []
        for name, imap_config in config.servers.items():
            self._dumpers.append(ImapDumper(config=imap_config, name=name, dump_folder=config.dump_folder))
            
    def dump(self):
        for dumper in self._dumpers:
            dumper.dump()