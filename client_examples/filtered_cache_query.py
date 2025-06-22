import json
import requests

if __name__ == "__main__":
    url = "http://localhost:9600/messages/24-hour-cache"
    
    
    data = {
        "filters": {
            "type": "all",
            "conditions": [
                {
                    "type": "exists",
                    "path": "message.event"
                }
            ]
        },
    
        "after_timestamp": "2025-06-06T17:30:00Z",
        "max_items": 1000
    }
    
    data = json.dumps(data)
    
    response = requests.post(url, data=data, timeout=10)
    
    content = json.loads(response.content)
    
    print(content)