import logging
import os
import argparse

from .imap.handler import ImapDumpHandler
from .config.handler import ConfigHandler

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.INFO,
    )

    args = parser.parse_args()
    
    logging.basicConfig(format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s', level=args.loglevel)
    logger = logging.getLogger("server")
    logger.debug(f"Running as UID {os.getuid()}")
    
    try:
        conf_handler = ConfigHandler()
        handler = ImapDumpHandler(conf_handler.config)
        
        handler.dump()
        
    except KeyboardInterrupt as e:
        logger.info("Got KeyboardInterrupt")        
    except Exception as e:
        logger.exception("Exception encountered")
        raise
    finally:
        logger.info("Shutting down")

if __name__ == "__main__":
    main()