"""
Settings file - common constants for the projects
"""
import logging

# The following settings should be identical both for client and server
DEFAULT_PORT = 7777                     # TCP port for server to listen on
DEFAULT_ENCODING = 'UTF-8'              # Default encoding for JIM messages

# The following are settings unique to client
DEFAULT_SERVER_ADDRESS = '127.0.0.1'    # Server IP address for client to connect to
CONNECTION_TIMEOUT = 60                 # Connection timeout in seconds
SELECT_TIMEOUT = 60.0                   # Timeout for select.select() function waiting for data

DIRECTORY_SEPARATOR = '/'

# *** Logging config
LOG_DIRECTORY = 'log'
LOG_NAME = 'app.client'
# Console log
LOG_CONSOLE_LEVEL = logging.NOTSET
LOG_CONSOLE_FORMAT = "%(asctime)s %(levelname)-10s %(module)s %(message)s"
# File log
LOG_FILE_NAME = DIRECTORY_SEPARATOR.join((LOG_DIRECTORY, 'client.log'))
LOG_FILE_LEVEL = logging.NOTSET
LOG_FILE_FORMAT = "%(asctime)s %(levelname)-10s %(module)s %(message)s"
