# Import libraries
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# EDDN connection settings
EDDN_URL = os.getenv('EDDN_URL', 'tcp://eddn.edcd.io:9500')  # URL of the EDDN ZeroMQ server
EDDN_TIMEOUT = int(os.getenv('EDDN_TIMEOUT', "600000"))      # ZeroMQ receive timeout in milliseconds

# Local relay server settings
RELAY_PORT = int(os.getenv('RELAY_PORT', "9600"))            # Port for the WebSocket relay server
RELAY_HOST = os.getenv('RELAY_HOST', '127.0.0.1')            # Host address for the relay server

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()          # Application logging level
