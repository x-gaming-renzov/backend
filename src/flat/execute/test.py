import sys
import json

sys.path.append('..')

from .util import read_json, write_json
from .process import flatten_json

def main():
    # Sample input data (as you provided)
    data_json = {
        "event_001": {
            "event_type": "player_join",
            "player_id": "player_12345",
            "timestamp": "2024-11-21T10:00:00Z",
            "location": {"x": 100, "y": 64, "z": -300},
            "details": {"message": "Player joined the game"}
        },
        "event_002": {
            "event_type": "block_break",
            "player_id": "player_12345",
            "timestamp": "2024-11-21T10:05:00Z",
            "location": {"x": 105, "y": 65, "z": -310},
            "details": {
                "block_type": "stone", 
                "tool_used": "diamond_pickaxe", 
                "dropped_items": ["cobblestone"]
            }
        },
        "event_003": {
            "event_type": "chat_message",
            "player_id": "player_67890",
            "timestamp": "2024-11-21T10:10:00Z",
            "details": {
                "message": "Anyone up for a raid?", 
                "chat_channel": "global"
            }
        }
    }
    
    action_json = {
        "event_001": {
            "key": "event_001",
            "action": "property",
            "name": "events",
            "children": {
                "location": {
                    "key": "location",
                    "action": "property",
                    "name": "location",
                    "children": {}
                },
                "details": {
                    "key": "details",
                    "action": "property",
                    "name": "propertyDetails",
                    "children": {}
                }
            }
        },
        "event_002": {
            "key": "event_002",
            "action": "property",
            "name": "events",
            "children": {
                "location": {
                    "key": "location",
                    "action": "property",
                    "name": "location",
                    "children": {}
                },
                "details": {
                    "key": "details",
                    "action": "property",
                    "name": "propertyDetails",
                    "children": {}
                }
            }
        },
        "event_003": {
            "key": "event_003",
            "action": "property",
            "name": "events",
            "children": {
                "details": {
                    "key": "details",
                    "action": "property",
                    "name": "propertyDetails",
                    "children": {}
                }
            }
        }
    }
    
    # Flatten the JSON
    flattened = flatten_json(data_json, action_json)
    
    # Pretty print the result
    print(json.dumps(flattened, indent=2))

if __name__ == "__main__":
    main()