import os
import sys
import logging.handlers

import client_settings as sett

# Create logging directory if not already exists
os.makedirs(sett.LOG_DIRECTORY, exist_ok=True)

# Configure main logger
logging.basicConfig(
    stream=sys.stderr,
    level=sett.LOG_CONSOLE_LEVEL,
    format=sett.LOG_CONSOLE_FORMAT,
)

# Configure app logger
log = logging.getLogger(sett.LOG_NAME)
log.propagate = True            # Propagate to the main logger to write to stderr
log.setLevel(sett.LOG_FILE_LEVEL)
log_handler = logging.FileHandler(sett.LOG_FILE_NAME)
log_handler.setFormatter(logging.Formatter(sett.LOG_FILE_FORMAT))
log.addHandler(log_handler)
