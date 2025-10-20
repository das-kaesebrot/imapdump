import logging
import re

from ..db.data_service import DataService
from ..config.imap_config import ImapDumpConfig
from ..enums.imap_encryption_mode import ImapEncryptionMode
from ..models.mail import Mail
from imapclient import IMAPClient


class ImapDumper:
    _client: IMAPClient
    _logger: logging.Logger
    _data_service: DataService

    _folder_regex: str

    _force_dump: bool = True

    CHUNKSIZE: int = 1000

    def __init__(self, config: ImapDumpConfig) -> None:
        if config.encryption_mode == ImapEncryptionMode.NONE:
            self._client = IMAPClient(
                host=config.host, port=config.port, use_uid=True, ssl=False
            )
        elif config.encryption_mode == ImapEncryptionMode.STARTTLS:
            self._client = IMAPClient(
                host=config.host, port=config.port, use_uid=True, ssl=False
            )
            self._client.starttls()
        elif config.encryption_mode == ImapEncryptionMode.SSL:
            self._client = IMAPClient(
                host=config.host, port=config.port, use_uid=True, ssl=True
            )

        self._folder_regex = config.folder_regex
        self._force_dump = config.force_dump

        self._logger = logging.getLogger(f"dumper")

        connection_string = "sqlite:///imapdump.db"

        if config.database_file:
            connection_string = f"sqlite:///{config.database_file}"

        self._data_service = DataService(connection_string=connection_string)

        self._logger.info(f"Dumping '{config.username}'@'{config.host}:{config.port}'")

        if config.username and config.password:
            self._logger.debug(
                f"Logging in with credentials to IMAP server: '{config.username}'"
            )
            self._client.login(config.username, config.password)

        self._set_idle(True)

    def dump(self):
        self._write_all_messages()

    def _write_all_messages(self) -> dict:
        # stop idling
        self._set_idle(False)

        # get all folders in IMAP account
        folders = self._client.list_folders()
        folder_names = []

        # filter folders based on regex
        for flags, delim, folder_name in folders:
            self._logger.debug(f"{flags=}, {delim=}, {folder_name=}")

            if not re.match(self._folder_regex, folder_name):
                self._logger.info(f"Skipping ignored directory '{folder_name}'")
                continue

            folder_names.append(folder_name)

        messages = []

        # iterate over the remaining folders
        for folder_name in folder_names:
            # select folder to be examined
            self._client.select_folder(folder_name, readonly=True)

            message_ids = self._client.search()

            if len(message_ids) <= 0:
                self._logger.info(f"Skipping empty directory '{folder_name}'")
                continue

            chunks, remainder = divmod(len(message_ids), self.CHUNKSIZE)

            self._logger.info(
                f"Processing {len(message_ids)} message(s) in directory '{folder_name}'"
            )

            if remainder != 0:
                chunks += 1

            for chunk in range(chunks):
                start = chunk * self.CHUNKSIZE
                end = min((chunk + 1) * self.CHUNKSIZE, len(message_ids))

                ids = message_ids[start:end]

                percentage = (end / len(message_ids)) * 100

                new_or_updated_messages = []

                if self._force_dump:
                    # don't check against database if force dumping
                    new_or_updated_messages = ids
                else:
                    # don't retrieve entire message at first, only the size. Then compare to files already dumped and retrieve the full message as necessary.
                    for message_id, data in self._client.fetch(
                        messages=ids, data=["RFC822.SIZE"]
                    ).items():
                        mail_entity = Mail()
                        id = Mail.generate_id(
                            folder_name=folder_name, message_id=message_id
                        )
                        size = data.get(b"RFC822.SIZE")

                        create_or_update = (
                            self._data_service.mail_has_to_be_created_or_updated(
                                id, size
                            )
                        )

                        if not create_or_update:
                            continue

                        new_or_updated_messages.append(message_id)

                for message_id, data in self._client.fetch(
                    messages=new_or_updated_messages, data=["RFC822", "RFC822.SIZE"]
                ).items():
                    rfc822 = data.get(b"RFC822")
                    id = Mail.generate_id(
                        folder_name=folder_name, message_id=message_id
                    )
                    mail_entity = self._data_service.get_or_create_mail_by_id(id)

                    mail_entity.size = data.get(b"RFC822.SIZE")

                    mail_entity.folder = folder_name
                    mail_entity.uid = message_id
                    mail_entity.rfc822 = rfc822
                    mail_entity.date = data.get(b"INTERNALDATE")

                    messages.append(mail_entity)

                self._logger.info(f"'{folder_name}' progress: {percentage:.2f}%")

        self._data_service.save_all_and_commit(messages)

        # back to idling
        self._set_idle(True)

        self._logger.info(f"Found {len(messages)} new or updated message(s) to dump")

    def _set_idle(self, idle: bool):
        if idle:
            self._client.idle()
        else:
            self._client.idle_done()
