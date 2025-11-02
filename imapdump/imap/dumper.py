import glob
import logging
import re
import os
import shutil

from ..db.data_service import DataService
from ..config.imapdump_config import ImapDumpConfig
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

    _recreate: bool
    _mirror: bool
    _dry_run: bool

    _db_file: str

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
        self._recreate = config.recreate
        self._mirror = config.mirror
        self._dry_run = config.dry_run

        self._logger = logging.getLogger(__name__)
        self._db_file = config.database_file

        self._logger.info(f"Dumping '{config.username}'@'{config.host}:{config.port}'")
        self._dump_folder = os.path.abspath(
            os.path.expanduser(config.dump_folder.rstrip("/"))
        )

        if config.username and config.password:
            self._logger.debug(
                f"Logging in with credentials to IMAP server: '{config.username}'"
            )
            self._client.login(config.username, config.password)

        if self._dry_run:
            self._logger.info(
                "Dry run mode activated, nothing will actually be changed"
            )

        if self._recreate:
            self._logger.info(
                "RECREATE MODE ACTIVATED, DUMP FOLDER AND CACHE WILL BE RECREATED!"
            )
        elif self._mirror:
            self._logger.info(
                "Mirror mode activated, unknown files/folders in output folder will be removed"
            )

        self._data_service = DataService(
            connection_string=f"sqlite:///{self._db_file}",
            recreate=self._recreate,
            dry_run=self._dry_run,
        )

        self._set_idle(True)
        self._is_idle = True

    def dump(self):
        empty_folders = self._write_all_messages_to_db()
        self._dump_to_folder(empty_folders)
        self._data_service.close_db()

    def _write_all_messages_to_db(self) -> dict:
        logger = self._logger.getChild("cache")
        logger.info("Updating cache")
        # stop idling
        self._set_idle(False)

        # get all folders in IMAP account
        folders = self._client.list_folders()
        folder_names = []
        empty_folders = []

        seen_mails = []

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
                empty_folders.append(folder_name)

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

                if self._recreate:
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

                        if self._mirror:
                            seen_mails.append(id)

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

        if self._mirror:
            self._data_service.remove_diff(seen_mails)

        # back to idling
        self._set_idle(True)

        logger.info("Done updating cache")
        logger.info(f"Found {len(messages)} new or updated message(s) to dump")

        return empty_folders

    def _dump_to_folder(self, empty_folders: list[str]):
        logger = self._logger.getChild("writer")
        logger.info("Starting writer")

        all_mails = self._data_service.get_all_mails()

        logger.info(f"Dumping {len(all_mails)} message(s) to '{self._dump_folder}'")

        if self._recreate and os.path.isdir(self._dump_folder) and not self._dry_run:
            logger.info(f"Deleting '{self._dump_folder}'")
            shutil.rmtree(self._dump_folder)

        if not self._dry_run:
            os.makedirs(self._dump_folder, exist_ok=True)

        all_unknown_files = glob.glob(
            pathname="**", root_dir=self._dump_folder, recursive=True
        )

        for empty_folder in empty_folders:
            logger.info(f"Dumping empty folder '{empty_folder}'")
            if not self._dry_run:
                os.makedirs(
                    os.path.join(self._dump_folder, empty_folder), exist_ok=True
                )
            try:
                all_unknown_files.remove(empty_folder)
            except ValueError:
                pass

        written = 0
        written_byte = 0
        to_write = 0
        skipped = 0

        folder_uid_map = {}

        for mail in all_mails:
            fs_mail_folder = os.path.join(self._dump_folder, mail.folder)
            if not os.path.isdir(fs_mail_folder) and not self._dry_run:
                os.makedirs(fs_mail_folder, exist_ok=False)

            filename = mail.filename

            try:
                all_unknown_files.remove(os.path.join(mail.folder, filename))
            except ValueError:
                pass

            if mail.folder in all_unknown_files:
                all_unknown_files.remove(mail.folder)

            full_filename = os.path.join(fs_mail_folder, filename)

            # skip file write if not force dumping and the file already exists
            if os.path.exists(full_filename) and not self._recreate:
                skipped += 1
                continue

            if mail.folder not in folder_uid_map.keys():
                folder_uid_map[mail.folder] = {}

            folder_uid_map[mail.folder][str(mail.uid)] = (full_filename, mail.date)
            to_write += 1

        if skipped != len(all_mails):
            self._set_idle(False)

        unknown_emls = []
        unknown_files = []
        for unknown_file in all_unknown_files:
            if unknown_file.endswith(".eml"):
                unknown_emls.append(unknown_file)
            else:
                unknown_files.append(unknown_file)

        if len(unknown_emls) > 0:
            unknown_emls_string = "\n".join(list(map(lambda x: f"'{x}'", unknown_emls)))
            logger.info(
                f"Found {len(unknown_emls)} mail files in dump folder '{self._dump_folder}' that are not present on the server:\n{unknown_emls_string}"
            )
            if self._mirror:
                for unknown_eml in unknown_emls:
                    logger.info(f"Removing unknown file '{unknown_eml}'")
                    if not self._dry_run:
                        os.unlink(os.path.join(self._dump_folder, unknown_eml))

        if len(unknown_files) > 0:
            unknown_files_string = "\n".join(
                list(map(lambda x: f"'{x}'", unknown_files))
            )
            logger.info(
                f"Found {len(unknown_files)} unknown files/folders in dump folder '{self._dump_folder}':\n{unknown_files_string}"
            )

            if self._mirror:
                for unknown_file in unknown_files:
                    if os.path.isfile(unknown_file):
                        logger.info(f"Removing unknown file '{unknown_file}'")
                        if not self._dry_run:
                            os.unlink(os.path.join(self._dump_folder, unknown_file))
                    else:
                        logger.info(f"Removing unknown folder '{unknown_file}'")
                        if not self._dry_run:
                            shutil.rmtree(
                                os.path.join(self._dump_folder, unknown_file),
                                ignore_errors=True,
                            )

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
                    # bruh this is so terrible
                    filename = mails_in_folder[str(message_id)][0]
                    mail_date = mails_in_folder[str(message_id)][1]

                    logger.debug(
                        f"Writing message {message_id} RFC822 data ({len(rfc822)} chars) to '{filename}'"
                    )

                    if not self._dry_run:
                        with open(filename, mode="wb") as f:
                            written_byte += f.write(rfc822)

                    written += 1

                    # set modification time to mail timestamp
                    if not self._dry_run:
                        os.utime(
                            filename, (mail_date.timestamp(), mail_date.timestamp())
                        )

                logger.info(f"Writing '{folder_name}' progress: {percentage:.2f}%")

        if written > 0:
            self._set_idle(True)

        logger.info("Done writing to filesystem")
        logger.info(
            f"Dumped {written} message(s) {'(SIMULATED)' if self._dry_run else ''} ({written_byte:,} byte) ({skipped} already dumped before)"
        )

    def _set_idle(self, idle: bool):
        if idle and not self._is_idle:
            self._client.idle()
            self._is_idle = idle
        elif not idle and self._is_idle:
            self._client.idle_done()
            self._is_idle = idle
        else:
            self._logger.info("Skipped duplicate IDLE call")
