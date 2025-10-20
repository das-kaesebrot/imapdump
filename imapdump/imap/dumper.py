import logging
import re
import os
import shutil

from ..db.data_service import DataService
from ..config.imap_config import ImapDumpConfig
from ..enums.imap_encryption_mode import ImapEncryptionMode
from ..models.mail import Mail
from imapclient import IMAPClient


class ImapDumper:
    _client: IMAPClient
    _logger: logging.Logger
    _data_service: DataService

    _is_idle: bool = False

    _dump_folder: str

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

        self._logger = logging.getLogger(__name__)

        database_file = ".imapdump-cache.db"
        if config.database_file:
            database_file = config.database_file

        if self._force_dump:
            self._logger.info(
                "FORCE DUMP ACTIVATED, DUMP FOLDER AND CACHE WILL BE RECREATED!"
            )

        self._data_service = DataService(
            connection_string=f"sqlite:///{database_file}", recreate=self._force_dump
        )

        self._logger.info(f"Dumping '{config.username}'@'{config.host}:{config.port}'")
        self._dump_folder = os.path.abspath(
            os.path.expanduser(config.dump_folder.rstrip("/"))
        )

        if config.username and config.password:
            self._logger.debug(
                f"Logging in with credentials to IMAP server: '{config.username}'"
            )
            self._client.login(config.username, config.password)

        self._set_idle(True)
        self._is_idle = True

    def dump(self):
        self._write_all_messages_to_db()
        self._dump_to_folder()

    def _write_all_messages_to_db(self) -> dict:
        logger = self._logger.getChild("cache")
        logger.info("Updating cache")
        # stop idling
        self._set_idle(False)

        # get all folders in IMAP account
        folders = self._client.list_folders()
        folder_names = []

        # filter folders based on regex
        for flags, delim, folder_name in folders:
            logger.debug(f"{flags=}, {delim=}, {folder_name=}")

            if not re.match(self._folder_regex, folder_name):
                logger.info(f"Skipping ignored directory '{folder_name}'")
                continue

            folder_names.append(folder_name)

        messages = []

        # iterate over the remaining folders
        for folder_name in folder_names:
            # select folder to be examined
            self._client.select_folder(folder_name, readonly=True)

            message_ids = self._client.search()

            if len(message_ids) <= 0:
                logger.info(f"Skipping empty directory '{folder_name}'")
                continue

            chunks, remainder = divmod(len(message_ids), self.CHUNKSIZE)

            logger.info(
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
                    self._data_service.remove_all_mails()  # clean the cache
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
                    messages=new_or_updated_messages,
                    data=[
                        "RFC822.SIZE",
                        "INTERNALDATE",
                        "BODY[HEADER.FIELDS (SUBJECT)]",
                    ],
                ).items():
                    id = Mail.generate_id(
                        folder_name=folder_name, message_id=message_id
                    )
                    mail_entity = self._data_service.get_or_create_mail_by_id(id)
                    mail_entity.size = data.get(b"RFC822.SIZE")
                    mail_entity.title = data.get(
                        b"BODY[HEADER.FIELDS (SUBJECT)]"
                    ).decode(errors="ignore")[9:]

                    mail_entity.folder = folder_name
                    mail_entity.uid = message_id
                    mail_entity.date = data.get(b"INTERNALDATE")

                    messages.append(mail_entity)

                logger.info(f"'{folder_name}' progress: {percentage:.2f}%")

        self._data_service.save_all_and_commit(messages)

        # back to idling
        self._set_idle(True)

        logger.info("Done updating cache")
        logger.info(f"Found {len(messages)} new or updated message(s) to dump")

    def _dump_to_folder(self):
        logger = self._logger.getChild("writer")
        logger.info("Starting writer")
        if not self._dump_folder:
            logger.warning("No dump folder specified, ignoring folder output!")
            return

        all_mails = self._data_service.get_all_mails()

        logger.info(f"Dumping {len(all_mails)} message(s) to '{self._dump_folder}'")

        if self._force_dump and os.path.isdir(self._dump_folder):
            shutil.rmtree(self._dump_folder)

        os.makedirs(self._dump_folder, exist_ok=True)

        written = 0
        to_write = 0
        skipped = 0

        folder_uid_map = {}

        for mail in all_mails:
            fs_mail_folder = os.path.join(self._dump_folder, mail.folder)
            if not os.path.isdir(fs_mail_folder):
                os.makedirs(fs_mail_folder, exist_ok=False)

            filename = os.path.join(
                fs_mail_folder,
                f"{mail.id}_{self.replace_trash(mail.title, truncate_length=16)}.eml",
            )

            # skip file write if not force dumping and the file already exists
            if os.path.exists(filename) and not self._force_dump:
                skipped += 1
                continue

            if mail.folder not in folder_uid_map.keys():
                folder_uid_map[mail.folder] = {}

            folder_uid_map[mail.folder][str(mail.uid)] = filename
            to_write += 1

        if skipped != len(all_mails):
            self._set_idle(False)

        for folder_name, mails_in_folder in folder_uid_map.items():
            self._client.select_folder(folder_name, readonly=True)

            message_ids = list(mails_in_folder.keys())

            chunks, remainder = divmod(len(mails_in_folder.keys()), self.CHUNKSIZE)

            logger.info(
                f"Writing {len(message_ids)} message(s) from IMAP directory '{folder_name}'"
            )

            if remainder != 0:
                chunks += 1

            for chunk in range(chunks):
                start = chunk * self.CHUNKSIZE
                end = min((chunk + 1) * self.CHUNKSIZE, len(message_ids))

                ids = message_ids[start:end]

                percentage = (end / len(message_ids)) * 100

                for message_id, data in self._client.fetch(
                    messages=ids, data=["RFC822"]
                ).items():
                    rfc822 = data.get(b"RFC822")
                    filename = mails_in_folder[str(message_id)]

                    logger.debug(
                        f"Writing message {message_id} RFC822 data ({len(rfc822)} byte) to '{filename}'"
                    )

                    with open(filename, mode="wb") as f:
                        f.write(rfc822)
                    written += 1

                logger.info(f"Writing '{folder_name}' progress: {percentage:.2f}%")

            # set modification time to mail timestamp
            os.utime(filename, (mail.date.timestamp(), mail.date.timestamp()))

        if written > 0:
            self._set_idle(True)

        logger.info("Done writing to filesystem")
        logger.info(f"Dumped {written} message(s) ({skipped} already dumped before)")

    def _set_idle(self, idle: bool):
        if idle and not self._is_idle:
            self._client.idle()
            self._is_idle = idle
        elif not idle and self._is_idle:
            self._client.idle_done()
            self._is_idle = idle
        else:
            self._logger.info("Skipped duplicate IDLE call")

    # lol
    # https://stackoverflow.com/a/39059279
    # remove non-ascii chars and truncate to a fixed length
    @staticmethod
    def replace_trash(unicode_string: str, truncate_length: int = 32) -> str:
        for i in range(0, len(unicode_string)):
            try:
                unicode_string[i].encode("ascii")
            except UnicodeEncodeError:
                # means it's non-ASCII
                unicode_string = unicode_string[i].replace(
                    ""
                )  # replacing it with nothing

        # replace spaces with underscores
        unicode_string = unicode_string.replace(" ", "_")
        # remove everything that's not a letter, a number, an underscore or a dash
        unicode_string = re.sub(r"[^a-zA-Z0-9_\-]+", "", unicode_string)
        return unicode_string[:truncate_length].rstrip("_")
