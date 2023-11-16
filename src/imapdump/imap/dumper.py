import logging
import os
import shutil
from ..utils.str_utils import envelope_to_msg_title
from imapclient.response_types import Envelope
from ..config.imap_config import ImapConfig
from imapclient import IMAPClient

class ImapDumper:
    _client: IMAPClient
    _folder: str = None
    
    _logger: logging.Logger
    
    def __init__(self, config: ImapConfig, name: str, dump_folder: str) -> None:
                
        self._client = IMAPClient(
            host=config.host,
            port=config.port,
            use_uid=True,
            ssl=config.ssl)
        
        self._folder = os.path.join(dump_folder, name)
        
        self._logger = logging.getLogger(f"dumper.{name}")
        
        self._client.login(config.username, config.password)
        self._set_idle(True)
            
    def dump(self):
        self._set_idle(False)
        
        messages_in_account = {}
        
        for flags, delim, name in self._client.list_folders():
            self._logger.debug(f"{flags=}, {delim=}, {name=}")
            
            self._client.select_folder(name, readonly=True)
            
            msg_ids = self._client.search()
            
            if len(msg_ids) <= 0:
                continue
            
            messages_in_directory = {}
            
            for msgid, data in self._client.fetch(messages=msg_ids, data=['RFC822', 'ENVELOPE']).items():
                envelope = data.get(b'ENVELOPE')
                rfc822 = data.get(b'RFC822')
                
                assert isinstance(envelope, Envelope)
                
                msg_title = envelope_to_msg_title(envelope)
                                
                self._logger.info(msg_title)
                self._logger.debug(msgid)
                
                messages_in_directory[msg_title] = rfc822
                
            messages_in_account[name] = messages_in_directory
            
        self._set_idle(True)
        
        if os.path.exists(self._folder):
            shutil.rmtree(self._folder)
        
        for subfolder, messages in messages_in_account.items():
            assert isinstance(messages, dict)
            
            account_subfolder_write_path = os.path.join(self._folder, subfolder)
            os.makedirs(account_subfolder_write_path)
            
            for message_filename, message_content in messages.items():
                filename = os.path.join(account_subfolder_write_path, f"{message_filename}.eml")
                
                with open(filename, 'wb') as f:
                    f.write(message_content)
            
            
    def _set_idle(self, idle: bool):
        if idle: self._client.idle()
        else: self._client.idle_done()
        