# ==============================================================================
# 11.5 Logging
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib2.html#logging

# --- The logging module: a full-featured and flexible logging system ---
import logging

# At its simplest, log messages are sent to a file or to sys.stderr.
# By default, informational and debugging messages are suppressed,
# and the output is sent to standard error.

logging.debug('Debugging information')
logging.info('Informational message')
logging.warning('Warning:config file %s not found', 'server.conf')
logging.error('Error occurred')
logging.critical('Critical error -- shutting down')

# Output:
# WARNING:root:Warning:config file server.conf not found
# ERROR:root:Error occurred
# CRITICAL:root:Critical error -- shutting down

# --- Logging levels (from lowest to highest severity) ---
# DEBUG    - Detailed information, typically of interest only when diagnosing problems
# INFO     - Confirmation that things are working as expected
# WARNING  - An indication that something unexpected happened (default level)
# ERROR    - Due to a more serious problem, the software has not been able to perform a function
# CRITICAL - A serious error, indicating that the program itself may be unable to continue

# --- Logging to a file ---
# logging.basicConfig(filename='example.log', level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)s %(message)s')
# logging.debug('This message should go to the log file')
# logging.info('So should this')
# logging.warning('And this, too')

# --- Other output options ---
# Messages can be routed through email, datagrams, sockets, or to an HTTP Server.
# New filters can select different routing based on message priority.
#
# The logging system can be configured directly from Python or loaded from
# a user-editable configuration file for customized logging without
# altering the application.
