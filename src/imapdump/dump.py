import logging
import os
import argparse

from .imap.handler import ImapDumpHandler
from .config.handler import ConfigHandler


def main():
    available_levels = [
        level.lower() for level in logging.getLevelNamesMapping().keys()
    ]
    available_levels.remove(logging.getLevelName(logging.NOTSET).lower())
    available_levels.remove(logging.getLevelName(logging.WARNING).lower())

    parser = argparse.ArgumentParser(
        description="Dump IMAP accounts to a local directory"
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

    args = parser.parse_args()

    logging.basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        level=args.loglevel.upper(),
    )
    logger = logging.getLogger("main")
    logger.debug(f"Running as UID {os.getuid()}")

    try:
        conf_handler = ConfigHandler()
        handler = ImapDumpHandler(conf_handler.config)

        handler.dump()

    except KeyboardInterrupt as e:
        logger.info("Got KeyboardInterrupt")
    except Exception as e:
        logger.exception("Exception encountered")
    finally:
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
