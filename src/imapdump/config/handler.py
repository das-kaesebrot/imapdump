import dacite
import yaml
import logging
import os
import json

from .imap_config import ImapConfig
from .config import Config

class ConfigHandler:
    CONFIG_PATH: str = "config.yml"
    ROOT_KEY: str = "servers"
    _logger: logging.Logger
    _raw_config: dict = {}
    
    config: Config
    
    def __init__(self):
        self._logger = logging.getLogger("confighandler")
        self._load_config()
    
    def _load_config(self) -> None:
        config_path = os.getenv("IMAPDUMP_CONFIG_PATH", self.CONFIG_PATH)
        
        self._logger.debug(f"Loading config from {config_path}")
        
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Couldn't find config file at {config_path}")

        with open(file=config_path, mode='r') as f:
            if config_path.endswith(('.yaml', '.yml')):
                self._raw_config = yaml.safe_load(f)
            elif config_path.endswith('.json'):
                self._raw_config = json.load(f)
            else:
                raise ValueError(f"Unsupported file extension for config file: {config_path}")
        
        self._print()
        
        if not isinstance(self._raw_config, dict):
            raise ValueError("Config has to be serializable to a dict")
        
        if not self.ROOT_KEY in self._raw_config.keys():
            raise ValueError(f"Root key \"{self.ROOT_KEY}\" missing")
        
        self.config = Config()
        
        try:
            for key, value in self._raw_config.get(self.ROOT_KEY, {}).items():
                self.config.servers[key] = dacite.from_dict(data_class=ImapConfig, data=value)
        except ValueError as e:
            self._logger.exception(f"Error while deserializing config")
            
        keys = len(self.config.servers.keys())
        
        self._logger.info(f"Found {keys} config(s)")
        
        if keys <= 0:
            raise ValueError("No configs present")
        
    def _print(self) -> None:
        self._logger.debug(f"Raw config: {json.dumps(self._raw_config, indent=4)}")
        