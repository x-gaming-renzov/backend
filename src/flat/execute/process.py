import logging
from collections import deque
import json
from typing import Dict, Any, List, Union
import os
import sys
# Set up logging configuration

logging_enabled = os.getenv("LOGGING_ENABLED", "False").lower() == "true"

if logging_enabled:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def flatten_nested_json(
    data: Any, 
    action_spec: Dict = None, 
    parent_key: str = '', 
    sep: str = '.'
) -> Dict:
    """
    Recursively flatten nested JSON with support for complex structures and logging.
    """
    logging.debug(f"Flattening data: {data} with parent_key: {parent_key}")
    result = {}
    
    # Handle dictionaries
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}{key}" if parent_key else key
            logging.debug(f"Processing dict key: {key}, new_key: {new_key}")
            
            if action_spec and key in action_spec.get('children', {}):
                child_action = action_spec['children'][key]
                logging.debug(f"Action spec found for key: {key}, action: {child_action.get('action')}")

                if child_action.get('action') == 'prefix' or child_action.get('type') == 'list' :
                    nested_result = flatten_nested_json(
                        value, 
                        child_action, 
                        parent_key=f"{new_key}{sep}", 
                        sep=sep
                    )
                    result.update(nested_result)
                elif child_action.get('action') == 'property':
                    nested_result = flatten_nested_json(
                        value, 
                        child_action, 
                        parent_key='', 
                        sep=sep
                    )
                    result.update(nested_result)
                    if child_action.get('name'):
                        result[child_action['name']] = key
            else:
                if isinstance(value, (dict, list)):
                    nested_result = flatten_nested_json(
                        value, 
                        None, 
                        parent_key=f"{new_key}{sep}", 
                        sep=sep
                    )
                    result.update(nested_result)
                else:
                    result[new_key] = value
                    # logging.debug(f"Adding primitive value: {value} with key: {new_key}")
    
    # Handle lists
    elif isinstance(data, list):
        logging.debug(f"Processing list with parent_key: {parent_key} and action {action_spec}" )
        processed_list = []
        
        for item in data:
            if isinstance(item, (dict, list)):
                logging.debug(f"Processing nested item in list: {item}")
                processed_list.append(
                    flatten_nested_json(item, None, parent_key='', sep=sep)
                )
            else:
                logging.debug(f"Adding primitive item to list: {item}")
                processed_list.append(item)
        
        result[parent_key.rstrip('.')] = processed_list
        logging.debug(f"List processed: {processed_list}")
    
    # Handle primitive types
    else:
        result[parent_key.rstrip('.')] = data
        logging.debug(f"Adding primitive value: {data} with key: {parent_key.rstrip('.')}")
    
    return result

def flatten_json(data_json: Union[Dict, List], action_json: Dict) -> List[Dict]:
    """
    Transform multiple JSON entries based on action specifications with logging.
    Handles original lists without converting them to dictionaries.
    """
    logging.info("Starting to flatten JSON data")
    original_is_list = isinstance(data_json, list)  # Track if input was a list
    logging.info(data_json)
    # Convert list to a dict for processing, only if original is a list
    if not action_json:
        return data_json

    if original_is_list:
        logging.debug("Input is a list; skipping actions for top-level items.")
        data_json = {str(i): entry for i, entry in enumerate(data_json)}
    
    transformed_results = []
    
    for key, event_data in data_json.items():
        logging.info(f"Processing entry with key: {key}")
        action_spec = action_json.get(key, action_json)
        
        # Flatten the event data
        flattened = None
        if isinstance(event_data,list):
            flattened = flatten_nested_json(event_data, None if original_is_list else action_spec,key)
        else:
            flattened = flatten_nested_json(event_data, None if original_is_list else action_spec)
        
        # Add property field only if the input was NOT originally a list
        if not original_is_list and action_spec.get('action') == 'property' and action_spec.get('name'):
            flattened[action_spec['name']] = key
            logging.debug(f"Added property field: {action_spec['name']} with value: {key}")
        
        transformed_results.append(flattened)
        logging.debug(f"Flattened result for key {key}: {flattened}")
    
    logging.info("Flattening complete.")
    
    # Return the list as-is if input was originally a list
    return transformed_results if not original_is_list else list(transformed_results)


# Test the implementation
if __name__ == '__main__':
    # Load JSON files
    with open('t1.json', 'r') as f:
        data_json = json.load(f)

    with open('action.json', 'r') as f:
        action_json = json.load(f)

    # Perform transformation
    transformed = flatten_json(data_json, action_json)

    # Print transformed JSON
    print(json.dumps(transformed, indent=2))

    # Optionally save the output to a file
    with open('output.json', 'w') as f:
        json.dump(transformed, f, indent=2)
