import sys
import os
import logging
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

sys.path.append('..')

from . import llm
from . import process


# Configure logging
logging_enabled = os.getenv("LOGGING_ENABLED", "False").lower() == "true"
# logging.basicConfig(level=logging.info if logging_enabled else logging.CRITICAL)

def decide_and_name(json_data, keys, model=None):
    logging.info(f"Starting Decide and Name process for {keys}")
    
    # Multi-key processing
    if len(keys) > 1:
        pattern = llm.find_pattern_in_keys(keys, model)
        if pattern == "no pattern":
            pattern = None
        if pattern:
            logging.info(f"Pattern found: {pattern}")
            key_name = llm.suggest_key_name({"example": json_data[keys[0]]},keys, model)
            return [pattern, "property", key_name]
        else:
            logging.info("No pattern found. Processing each key individually.")
            return [process.process_single_key(json_data, key, model) for key in keys]

    # Single key processing
    elif keys:
        return process.process_single_key(json_data, keys[0], model)

    logging.warning("No keys provided for processing.")
    return []

def setup_logging():
    if logging_enabled:
        # Configure the root logger to show logs at INFO level or higher
        logging.basicConfig(
            level=logging.INFO,  # Set the root logger level to INFO
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.info("Logging enabled!")
        
        # Suppress log messages from external libraries (set their log level to WARNING or higher)
        logging.getLogger("urllib3").setLevel(logging.WARNING)  # Example: Suppress urllib3 logs
        logging.getLogger("openai").setLevel(logging.WARNING)   # Example: Suppress OpenAI logs
        logging.getLogger("requests").setLevel(logging.WARNING)  # Example: Suppress Requests library logs
        logging.getLogger("httpx").setLevel(logging.WARNING)  # Example: Suppress Requests library logs
        
    else:
        # Disable logging entirely
        logging.basicConfig(level=logging.CRITICAL)

# Call the setup_logging function to configure logging

if __name__ == "__main__":

    setup_logging()

    # Test example
    # sample_json = {
    #     "event_001": {"type": "A", "value": 123},
    #     "event_002": {"type": "B", "value": 456},
    # }
    # keys = ["event_001", "event_002"]

#     sample_json = {
#     "events": [
#       { "id": "event_001", "type": "player_join", "player": "player_12345", "time": "2024-11-21T10:00:00Z", "loc": { "x": 100, "y": 64, "z": -300 }, "msg": "Player joined the game" },
#       { "id": "event_002", "type": "block_break", "player": "player_12345", "time": "2024-11-21T10:05:00Z", "loc": { "x": 105, "y": 65, "z": -310 }, "block": "stone", "tool": "diamond_pickaxe", "drops": ["cobblestone"] },
#       { "id": "event_003", "type": "chat_message", "player": "player_67890", "time": "2024-11-21T10:10:00Z", "msg": "Anyone up for a raid?", "channel": "global" },
#       { "id": "event_004", "type": "player_death", "player": "player_12345", "time": "2024-11-21T10:15:00Z", "loc": { "x": 120, "y": 63, "z": -320 }, "cause": "fall_damage", "items": ["diamond_pickaxe", "iron_helmet"] },
#       { "id": "event_005", "type": "mob_kill", "player": "player_67890", "time": "2024-11-21T10:20:00Z", "loc": { "x": 150, "y": 70, "z": -200 }, "mob": "zombie", "tool": "iron_sword", "drops": ["rotten_flesh", "iron_ingot"] },
#       { "id": "event_006", "type": "item_craft", "player": "player_12345", "time": "2024-11-21T10:25:00Z", "loc": { "x": 100, "y": 64, "z": -300 }, "item": "golden_apple", "ingredients": ["gold_ingot", "apple"] }
#     ]
#   }
    
#     keys = ["events"]

    # sample_json = {
    #     "player_12345": {
    #       "join_event": {
    #         "timestamp": "2024-11-21T10:00:00Z",
    #         "location": { "x": 100, "y": 64, "z": -300 },
    #         "details": "Player joined the game"
    #       },
    #       "actions": [
    #         {
    #           "action": "block_break",
    #           "timestamp": "2024-11-21T10:05:00Z",
    #           "location": { "x": 105, "y": 65, "z": -310 },
    #           "block": { "type": "stone", "tool": "diamond_pickaxe", "drops": ["cobblestone"] }
    #         },
    #         {
    #           "action": "player_death",
    #           "timestamp": "2024-11-21T10:15:00Z",
    #           "location": { "x": 120, "y": 63, "z": -320 },
    #           "reason": "fall_damage",
    #           "drops": ["diamond_pickaxe", "iron_helmet"]
    #         },
    #         {
    #           "action": "item_craft",
    #           "timestamp": "2024-11-21T10:25:00Z",
    #           "location": { "x": 100, "y": 64, "z": -300 },
    #           "crafted_item": "golden_apple",
    #           "materials": ["gold_ingot", "apple"]
    #         }
    #       ]
    #     },
    #     "player_67890": {
    #       "chat_event": {
    #         "timestamp": "2024-11-21T10:10:00Z",
    #         "message": "Anyone up for a raid?",
    #         "channel": "global"
    #       },
    #       "actions": [
    #         {
    #           "action": "mob_kill",
    #           "timestamp": "2024-11-21T10:20:00Z",
    #           "location": { "x": 150, "y": 70, "z": -200 },
    #           "mob": "zombie",
    #           "tool": "iron_sword",
    #           "loot": ["rotten_flesh", "iron_ingot"]
    #         }
    #       ]
    #     }
    # }

    # keys = ["player_12345", "player_67890"]

    sample_json = {
              "action": "block_break",
              "timestamp": "2024-11-21T10:05:00Z",
              "location": { "x": 105, "y": 65, "z": -310 },
              "block": { "type": "stone", "tool": "diamond_pickaxe", "drops": ["cobblestone"] }
            }
    
    keys = ["location","block"]

    result = decide_and_name(sample_json, keys)
    print(result)
