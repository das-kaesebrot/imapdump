import argparse
from dataclasses import asdict
import json
import logging
import os
import yaml
from dacite import from_dict

from . import __version__
from .imap.dumper import ImapDumper
from .enums.imap_encryption_mode import ImapEncryptionMode
from .config.imapdump_config import ImapDumpConfig
from .config.fileconfig import ImapDumpFileConfig
from .config.default_values import ImapDumpConfigDefaults


def main():
    available_levels = [
        level.lower() for level in logging.getLevelNamesMapping().keys()
    ]
    available_levels.remove(logging.getLevelName(logging.NOTSET).lower())
    available_levels.remove(logging.getLevelName(logging.WARNING).lower())

    parser = argparse.ArgumentParser(
        prog="imapdump",
        description="Dump IMAP accounts to a local directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars="@",
    )

    parser.add_argument(
        "-l",
        "--logging",
        help="Console log level",
        dest="console_log_level",
        type=str,
        choices=available_levels,
        default=ImapDumpConfigDefaults.CONSOLE_LOG_LEVEL,
    )
    
    parser.add_argument(
        "--use-logfile",
        help="Write log files",
        action="store_true",
    )

    parser.add_argument(
        "--logfile-folder",
        help="Folder for log files",
        type=str,
        default=ImapDumpConfigDefaults.LOGFILE_FOLDER
    )

    parser.add_argument(
        "--logfile-level",
        help="Log files log level",
        type=str,
        choices=available_levels,
        default=ImapDumpConfigDefaults.LOGFILE_LEVEL,
    )

    parser.add_argument(
        "--host",
        help="Hostname of the IMAP server",
        type=str,
    )

    parser.add_argument(
        "-f",
        "--file",
        help="Database file",
        type=str,
        dest="database_file",
        default=ImapDumpConfigDefaults.DATABASE_FILE,
    )

    parser.add_argument(
        "-p",
        "--port",
        help="Port of the IMAP server",
        type=int,
        default=ImapDumpConfigDefaults.PORT,
    )

    parser.add_argument(
        "-u",
        "--username",
        help="Username for the IMAP account",
        type=str,
        default=ImapDumpConfigDefaults.USERNAME,
    )

    parser.add_argument(
        "--password",
        help="Password of the IMAP account",
        type=str,
        default=ImapDumpConfigDefaults.PASSWORD,
    )

    parser.add_argument(
        "--encryption-mode",
        help="IMAP encryption mode",
        type=ImapEncryptionMode,
        required=False,
        choices=ImapEncryptionMode.list(),
        default=ImapDumpConfigDefaults.ENCRYPTION_MODE,
    )

    parser.add_argument(
        "--folder-regex",
        help="Pattern to match against for including folders",
        type=str,
        default=ImapDumpConfigDefaults.FOLDER_REGEX,
    )
    
    group_mode = parser.add_mutually_exclusive_group()

    group_mode.add_argument(
        "--recreate",
        help="Recreate cache and recreate the dump directory (destructive, this will delete dumped files!), then dump all matching messages",
        action="store_true",
    )

    group_mode.add_argument(
        "--mirror",
        help="Remove all unknown files and folders from output folder and exactly mirror server state",
        action="store_true",
    )

    parser.add_argument(
        "--dry-run",
        help="Only simulate what would be done, don't actually write/change anything",
        action="store_true",
    )

    parser.add_argument(
        "--dump-folder",
        help="Where to dump .eml files to",
        type=str,
        default=ImapDumpConfigDefaults.DUMP_FOLDER,
    )

    parser.add_argument(
        "-c",
        "--config",
        dest="additional_config_files",
        help="Supply a config file",
        type=str,
        action="append",
    )
    
    args = parser.parse_args()
    
    if args.additional_config_files is not None:
        additional_args = []
        for config_filename in args.additional_config_files:
            with open(config_filename, 'r') as f:
                config = yaml.safe_load(f)
                config_parsed = from_dict(data_class=ImapDumpFileConfig, data=config)
                for key, value in asdict(config_parsed).items():
                    additional_args.extend([f"--{key.replace('_', '-')}", str(value)])

        # Reload arguments to override config file values with command line values
        args = parser.parse_args(additional_args)
        args = parser.parse_args(namespace=args)
    

    logging.basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        level=args.console_log_level.upper(),
    )
    logger = logging.getLogger("imapdump.main")
    logger.info(f"Running version {__version__}")
    logger.debug(f"Running as UID {os.getuid()}")

    config = ImapDumpConfig(**vars(args))

    try:
        dumper = ImapDumper(config=config)
        dumper.dump()

    except KeyboardInterrupt:
        logger.info("Got KeyboardInterrupt")
    except Exception:
        logger.exception("Exception encountered")
    finally:
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
