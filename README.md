# EDDN Relay

A WebSocket relay server for Elite Dangerous Data Network (EDDN) messages with customizable filtering capabilities and message storage.

## Features

- Real-time EDDN message forwarding via WebSocket
- Configurable message filtering with multiple filter types
- MongoDB integration for message storage and historical queries
- Support for multiple concurrent clients
- REST API endpoint for querying historical messages
- Docker support for easy deployment
- Automatic reconnection for reliable data streaming
- Configurable via environment variables

## Requirements

- Python 3.10 or higher
- ZeroMQ library
- WebSockets support
- FastAPI
- Uvicorn
- MongoDB (optional)

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with the following optional settings:

```env
# EDDN Connection Settings
EDDN_URL=tcp://eddn.edcd.io:9500
EDDN_TIMEOUT=600000

# Relay Server Settings
RELAY_PORT=9600
RELAY_HOST=127.0.0.1

# MongoDB Settings (Optional)
USE_MONGODB=false
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=eddn_relay

# Logging
LOG_LEVEL=INFO
```

## Usage

### Starting the Server

You can start the relay server in two ways:

1. Directly with Python:
```bash
python -m src.application
```

2. Using Docker:
```bash
docker build -t eddn-relay .
docker run -p 9600:9600 eddn-relay
```

### Client Connection

Connect to the WebSocket server at `ws://<RELAY_HOST>:<RELAY_PORT>/ws` and send a filter configuration:

```json
{
    "type": "filter",
    "filter": {
        "type": "exact",
        "path": "schemaRef",
        "value": "https://eddn.edcd.io/schemas/commodity/3"
    }
}
```

### Filter Types

- **Exists**: Match when a specific path exists in the message
  ```json
  {
    "type": "exists",
    "path": "message.event"
  }
  ```

- **Exact Match**: Match exact values at specific paths
  ```json
  {
    "type": "exact",
    "path": "message.event",
    "value": "Scan"
  }
  ```

- **Regex**: Match values using regular expressions
  ```json
  {
    "type": "regex",
    "path": "message.StarSystem",
    "pattern": "^Sol.*"
  }
  ```

- **All**: Combine multiple conditions with AND logic
  ```json
  {
    "type": "all",
    "conditions": [
      {
        "type": "exact",
        "path": "message.event",
        "value": "Scan"
      },
      {
        "type": "exists",
        "path": "message.StarSystem"
      }
    ]
  }
  ```

- **Any**: Combine multiple conditions with OR logic
  ```json
  {
    "type": "any",
    "conditions": [
      {
        "type": "exact",
        "path": "message.event",
        "value": "FSDJump"
      },
      {
        "type": "exact",
        "path": "message.event",
        "value": "CarrierJump"
      }
    ]
  }
  ```

### Historical Data API

When MongoDB is enabled, you can query the last 24 hours of messages using the REST API:

```http
POST /messages/24-hour-cache
Content-Type: application/json

{
    "filters": {
        "type": "exact",
        "path": "message.event",
        "value": "Scan"
    },
    "after_timestamp": "2025-06-06T17:30:00Z",
    "max_items": 1000
}
```

The API supports the same filter types as the WebSocket connections.

### Example Clients

Check the `client_examples` directory for sample implementations:

- `filtered_client_websocket_simple.py`: Basic WebSocket client with simple filtering
- `filtered_client_websocket.py`: Advanced WebSocket client with complex filters
- `filtered_cache_query.py`: Example of querying historical data via REST API