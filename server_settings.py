"""
Settings file - common constants for the projects
"""
import logging

# The following settings should be identical both for client and server
DEFAULT_PORT = 7777                     # TCP port for server to listen on
DEFAULT_ENCODING = 'UTF-8'              # Default encoding for JIM messages

# The following are settings unique to server
DEFAULT_LISTEN_ADDRESS = ''             # IP address for server to listen on
SOCKET_TIMEOUT = 0.2                    # Server socket timeout while waiting for client connections
MAX_CONNECTIONS = 2                     # Maximum number of client connections
CLIENT_CONNECTION_TIMEOUT = 0           # Client connection timeout in seconds - there will be no timeout
SELECT_TIMEOUT = 1.0                    # Server timeout for select.select() function waiting for clients

DIRECTORY_SEPARATOR = '/'

# *** Logging config
LOG_DIRECTORY = 'log'
LOG_NAME = 'app.server'
# Console log
LOG_CONSOLE_LEVEL = logging.NOTSET
LOG_CONSOLE_FORMAT = "%(asctime)s %(levelname)-10s %(module)s %(message)s"
# File log
LOG_FILE_NAME = DIRECTORY_SEPARATOR.join((LOG_DIRECTORY, 'server.log'))
LOG_FILE_BACKUP_DAYS_COUNT = 10       # Log backup days for daily logs
LOG_FILE_LEVEL = logging.NOTSET
LOG_FILE_FORMAT = "%(asctime)s %(levelname)-10s %(module)s %(message)s"
