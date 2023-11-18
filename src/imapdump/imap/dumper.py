import logging
import os
from ..utils.str_utils import envelope_to_msg_title
from ..utils.hash_utils import filehash, bytehash
from imapclient.response_types import Envelope
from ..config.imap_config import ImapConfig
from imapclient import IMAPClient


class ImapDumper:
    _client: IMAPClient
    _folder: str = None
    _logger: logging.Logger
    
    _ignored_folders: list[str]

    CHUNKSIZE: int = 1000

    def __init__(self, config: ImapConfig, name: str, dump_folder: str) -> None:
        self._client = IMAPClient(
            host=config.host, port=config.port, use_uid=True, ssl=config.ssl
        )
        
        self._ignored_folders = config.ignored

        self._folder = os.path.join(dump_folder, name)

        self._logger = logging.getLogger(f"dumper.{name}")

        self._logger.info(f"Dumping '{config.username}'@'{config.host}:{config.port}'")

        self._client.login(config.username, config.password)
        self._set_idle(True)

    def dump(self):
        messages_per_folder = self._get_all_messages()
        self._write_message_files(messages_per_folder)

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

        # iterate over the remaining folders
        for name in folder_names:
            # select folder to be examined
            self._client.select_folder(name, readonly=True)

            msg_ids = self._client.search()

            if len(msg_ids) <= 0:
                self._logger.info(f"Skipping empty directory '{name}'")
                continue

            messages_in_directory = {}

            chunks, remainder = divmod(len(msg_ids), self.CHUNKSIZE)

            self._logger.info(
                f"Processing {len(msg_ids)} messages in directory '{name}'"
            )

            if remainder != 0:
                chunks += 1

            for chunk in range(chunks):
                start = chunk * self.CHUNKSIZE
                end = min((chunk + 1) * self.CHUNKSIZE, len(msg_ids))

                ids = msg_ids[start:end]
                
                percentage = (end / len(msg_ids)) * 100

                # Get envelope info and entire message (RFC822)
                for msgid, data in self._client.fetch(
                    messages=ids, data=["RFC822", "ENVELOPE"]
                ).items():
                    envelope = data.get(b"ENVELOPE")
                    rfc822 = data.get(b"RFC822")

                    # sanity check
                    assert isinstance(envelope, Envelope)

                    msg_filename = f"{envelope_to_msg_title(envelope)}.eml"

                    # add message to folder specific dict using generated title as key
                    messages_in_directory[msg_filename] = rfc822

                # add message title/message content dict as directory dict entry
                messages_in_account[name] = messages_in_directory
                
                self._logger.info(
                    f"'{name}' progress: {percentage:.2f}%"
                )

        # back to idling
        self._set_idle(True)

        return messages_in_account

    def _write_message_files(self, messages: dict):
        num_new = 0
        num_skipped = 0
        num_all = 0

        self._logger.info(f"Dumping to '{self._folder}'")

        for subfolder, messages in messages.items():
            assert isinstance(messages, dict)

            account_subfolder_write_path = os.path.join(self._folder, subfolder)

            os.makedirs(account_subfolder_write_path, exist_ok=True)

            num_all += len(messages)

            for message_filename, message_content in messages.items():
                filename = os.path.join(account_subfolder_write_path, message_filename)

                # check if message was already saved (by md5 hash comparison) and skip if that's the case
                if os.path.isfile(filename):
                    message_hash = bytehash(message_content)
                    if filehash(filename) == message_hash:
                        self._logger.debug(
                            f"Skipping file '{filename}': Already exists and hash '{message_hash}' matches"
                        )
                        num_skipped += 1
                        continue

                self._logger.debug(f"Writing new file '{filename}'")
                num_new += 1
                with open(filename, "wb") as f:
                    f.write(message_content)

            self._cleanup_leftovers(messages.keys(), account_subfolder_write_path)

        self._logger.info(
            f"Done writing! New: {num_new}, skipped: {num_skipped}, total: {num_all}"
        )

    # cleans up all unexpected files in a subfolder
    def _cleanup_leftovers(self, allowed_files: list[str], folder: str):
        files_in_directory = os.listdir(folder)
        leftovers = [
            filename for filename in files_in_directory if filename not in allowed_files
        ]

        self._logger.debug(f"Found {len(leftovers)} items not in backup")

        for filename in leftovers:
            filename = os.path.join(folder, filename)
            if not os.path.isfile(filename):
                continue

            self._logger.debug(f"Removing '{filename}'")
            os.remove(filename)

    def _set_idle(self, idle: bool):
        if idle:
            self._client.idle()
        else:
            self._client.idle_done()
