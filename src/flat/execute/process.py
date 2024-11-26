import sys
sys.path.append('..')

def flatten_json(data_json, action_json):
    """
    Flatten JSON using depth-first search based on action_json rules
    
    :param data_json: Original JSON with event data
    :param action_json: JSON defining flattening actions
    :return: List of flattened JSON objects
    """
    flattened_results = []
    
    # Iterate through each event in the data JSON
    for event_key, event_data in data_json.items():
        # Check if this event is in the action JSON
        if event_key not in action_json:
            continue
        
        # Create a copy of the event data to modify
        flattened_event = event_data.copy()
        
        # Add the event ID to the flattened event
        flattened_event['event_id'] = event_key
        
        # Process children defined in the action JSON
        action_event = action_json[event_key]
        if 'children' in action_event:
            for child_key, child_action in action_event['children'].items():
                if child_key not in event_data:
                    continue
                
                # Handle prefix action (nested properties)
                if child_action.get('action') == 'property':
                    child_data = event_data[child_key]
                    
                    # If child is a nested dictionary, prefix its keys
                    if isinstance(child_data, dict):
                        for sub_key, sub_value in child_data.items():
                            flattened_event[f"{child_key}.{sub_key}"] = sub_value
                        
                        # Remove the original nested dictionary
                        del flattened_event[child_key]
        
        # Remove any remaining nested dictionaries that weren't processed
        for key in list(flattened_event.keys()):
            if isinstance(flattened_event[key], dict):
                del flattened_event[key]
        
        flattened_results.append(flattened_event)
    
    return flattened_results