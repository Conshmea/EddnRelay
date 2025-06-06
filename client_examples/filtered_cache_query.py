import requests
import json

if __name__ == "__main__":
    url = "http://localhost:9600/messages/24-hour-cache"
    
    conditions = {
        "type": "all",
        "conditions": [
            {
                "type": "exists",
                "path": "message.event",
            }
        ]
    }
    
    conditions = json.dumps(conditions)
    
    params = {
        "after_timestamp": "2025-06-06T17:30:00Z",
        "max_items": 1000
    }
    
    response = requests.post(url, data=conditions, params=params, timeout=10)
    
    content = json.loads(response.content)
    
    print(content)