# EDDN Relay

A WebSocket relay server for Elite Dangerous Data Network (EDDN) messages with customizable filtering capabilities.

## Features

- Real-time EDDN message forwarding
- WebSocket server for client connections
- Customizable message filtering
- Support for multiple concurrent clients
- Filter conditions: exact match, regex, AND/OR combinations
- Configurable via environment variables

## Requirements

- Python 3.10 or higher
- ZeroMQ library
- WebSockets support
- FastApi
- Uvicorn

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with the following optional settings:

```env
EDDN_URL=tcp://eddn.edcd.io:9500
EDDN_TIMEOUT=600000
RELAY_PORT=9600
RELAY_HOST=127.0.0.1
LOG_LEVEL=INFO
```

## Usage

Start the relay server:

```bash
python -m src.application
```

### Client Connection

Connect to the WebSocket server at `ws://<RELAY_HOST>:<RELAY_PORT>/ws` and send a filter configuration:

```json
{
    "type": "filter",
    "filter": {
        "type": "exact",
        "path": ["schemaRef"],
        "value": "https://eddn.edcd.io/schemas/commodity/3"
    }
}
```

### Filter Types

- **Exists**: Match when a specific path exists
- **Exact Match**: Match exact values at specific paths
- **Regex**: Match values using regular expressions
- **All**: Combine multiple conditions with AND logic
- **Any**: Combine multiple conditions with OR logic