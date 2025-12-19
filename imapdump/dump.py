import argparse
from dataclasses import asdict
import json
import logging
import os
import yaml
from dacite import Config, from_dict

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
        description="Dump an IMAP account to a local directory",
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
        "--logfile-path",
        help="File to write log entries into",
        type=str,
        default=ImapDumpConfigDefaults.LOGFILE_PATH,
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
        default=ImapDumpConfigDefaults.HOST,
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
        help="Supply a config file (can be specified multiple times)",
        type=str,
        action="append",
    )

    args = parser.parse_args()

    config = ImapDumpConfig()

    if args.additional_config_files is not None:
        for config_filename in args.additional_config_files:
            with open(config_filename, "r") as f:
                config_file = yaml.safe_load(f)
                config_parsed = from_dict(
                    data_class=ImapDumpFileConfig, data=config_file, config=Config(cast=[ImapEncryptionMode]),
                )
                config.update_from_dict(vars(config_parsed))

    config.update_from_dict(vars(args))

    min_log_level = min(
        logging.getLevelNamesMapping()[config.console_log_level.upper()],
        logging.getLevelNamesMapping()[config.logfile_level.upper()],
    )

    log_formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(min_log_level)
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(log_formatter)
    stdout_handler.setLevel(config.console_log_level.upper())
    root_logger.addHandler(stdout_handler)

    logger = logging.getLogger("imapdump.main")

    if args.use_logfile:
        logfile = os.path.abspath(os.path.expanduser(config.logfile_path))
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(config.logfile_level.upper())
        root_logger.addHandler(file_handler)
        logger.info(f"Logging to '{logfile}'")

    logger = logging.getLogger("imapdump.main")
    logger.info(f"Running version {__version__}")
    logger.debug(f"Running as UID {os.getuid()}")

    logger.debug(f"Using config:\n{json.dumps(asdict(config), indent=4)}")

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
