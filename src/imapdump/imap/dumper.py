import logging

from ..db.data_service import DataService
from hashlib import sha256
from ..config.imap_config import ImapDumpConfig
from ..models.mail import Mail
from imapclient import IMAPClient


class ImapDumper:
    _client: IMAPClient
    _logger: logging.Logger
    _data_service: DataService

    _ignored_folders: list[str]

    CHUNKSIZE: int = 1000

    def __init__(self, config: ImapDumpConfig, name: str, data_service: DataService) -> None:
        self._client = IMAPClient(
            host=config.host, port=config.port, use_uid=True, ssl=config.ssl
        )

        self._ignored_folders = config.ignored

        self._logger = logging.getLogger(f"dumper.{name}")
        
        self._data_service = data_service

        self._logger.info(f"Dumping '{config.username}'@'{config.host}:{config.port}'")

        self._client.login(config.username, config.password)
        self._set_idle(True)

    def dump(self):
        messages_per_folder = self._get_all_messages()
        self._write_messages_to_database(messages_per_folder)

    def _get_all_messages(self) -> dict:
        # stop idling
        self._set_idle(False)

        messages_in_account = {}

        # get all folders in IMAP account
        folders = self._client.list_folders()
        folder_names = []

        # filter folders based on ignored folder settings
        for flags, delim, name in folders:
            self._logger.debug(f"{flags=}, {delim=}, {name=}")

            stripped_name = name.split(delim.decode())[-1]

            if stripped_name in self._ignored_folders or name in self._ignored_folders:
                self._logger.info(f"Skipping ignored directory '{name}'")
                continue

            folder_names.append(name)
            
        messages = []

        # iterate over the remaining folders
        for name in folder_names:
            # select folder to be examined
            self._client.select_folder(name, readonly=True)

            msg_ids = self._client.search()

            if len(msg_ids) <= 0:
                self._logger.info(f"Skipping empty directory '{name}'")
                continue

            chunks, remainder = divmod(len(msg_ids), self.CHUNKSIZE)

            self._logger.info(
                f"Processing {len(msg_ids)} message(s) in directory '{name}'"
            )

            if remainder != 0:
                chunks += 1

            for chunk in range(chunks):
                start = chunk * self.CHUNKSIZE
                end = min((chunk + 1) * self.CHUNKSIZE, len(msg_ids))

                ids = msg_ids[start:end]

                percentage = (end / len(msg_ids)) * 100

                # TODO don't retrieve entire message at first, only the size. Then compare to files already dumped and retrieve the full message as necessary.
                # Get envelope info and entire message (RFC822)
                for msgid, data in self._client.fetch(
                    messages=ids, data=["RFC822"]
                ).items():
                    rfc822 = data.get(b"RFC822")

                    # sanity check
                    mail_entity = Mail()
                    mail_entity.id = sha256(f"{name}_{msgid}".encode()).hexdigest()
                    mail_entity.folder = name
                    mail_entity.uid = msgid
                    mail_entity.rfc822 = rfc822
                    
                    messages.append(mail_entity)
                
                self._logger.info(
                    f"'{name}' progress: {percentage:.2f}%"
                )
        
        self._data_service.save_all_and_commit(messages)        
        
        # back to idling
        self._set_idle(True)

        self._logger.info(f"Found {len(messages_in_account.keys())} message(s) to dump")

        return messages_in_account

    def _write_messages_to_database(self, messages: dict):
        num_new = 0
        num_skipped = 0
        num_all = 0

        self._logger.info(f"Dumping")

        for subfolder, messages in messages.items():
            assert isinstance(messages, dict)

            num_all += len(messages)

            for message_filename, message_content in messages.items():
                num_new += 1
                
                
        self._data_service.save_all_and_commit()
        self._logger.info(
            f"Done writing! New: {num_new}, skipped: {num_skipped}, total: {num_all}"
        )

    def _set_idle(self, idle: bool):
        if idle:
            self._client.idle()
        else:
            self._client.idle_done()
