import argparse
import logging
import os
import yamlargparse

from .imap.dumper import ImapDumper
from .enums.imap_encryption_mode import ImapEncryptionMode
from .config.imap_config import ImapDumpConfig


def main():
    available_levels = [
        level.lower() for level in logging.getLevelNamesMapping().keys()
    ]
    available_levels.remove(logging.getLevelName(logging.NOTSET).lower())
    available_levels.remove(logging.getLevelName(logging.WARNING).lower())

    parser = yamlargparse.ArgumentParser(
        description="Dump IMAP accounts to a local directory",
        error_handler=yamlargparse.usage_and_exit_error_handler,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,        
    )
    
    parser.add_argument(
        "-l",
        "--logging",
        help="set the log level",
        dest="loglevel",
        type=str,
        choices=available_levels,
        default=logging.getLevelName(logging.INFO).lower(),
    )
    
    parser.add_argument(
        "--host",
        help="Hostname of the IMAP server",
        type=str,
        required=True,
    )    
    
    parser.add_argument(
        "-f",
        "--file",
        help="Database file",
        type=str,
        dest="database_file",
        default=None
    )
    
    parser.add_argument(
        "-p",
        "--port",
        help="Port of the IMAP server",
        type=int,
        default=993,
    )
    
    parser.add_argument(
        "-u",
        "--username",
        help="Username for the IMAP account",
        type=str,
        default=None,
    )
    
    parser.add_argument(
        "--password",
        help="Password of the IMAP account",
        type=str,
        default=None,
    )
    
    parser.add_argument(
        "--encryption-mode",
        help="IMAP encryption mode",        
        type=ImapEncryptionMode,
        required=False,
        choices=ImapEncryptionMode.list(),
        default=ImapEncryptionMode.SSL,
    )
    
    parser.add_argument(
        "--folder-regex",
        help="Pattern to match against for including folders",
        type=str,
        default="^.*$"
    )
    
    parser.add_argument('--config', action=yamlargparse.ActionConfigFile)

    args = parser.parse_args()

    logging.basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        level=args.loglevel.upper(),
    )
    logger = logging.getLogger("main")
    logger.debug(f"Running as UID {os.getuid()}")
    
    config = ImapDumpConfig(**vars(args))

    try:
        dumper = ImapDumper(config=config)
        dumper.dump()

    except KeyboardInterrupt as e:
        logger.info("Got KeyboardInterrupt")
    except Exception as e:
        logger.exception("Exception encountered")
    finally:
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
