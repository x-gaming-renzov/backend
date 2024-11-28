
import json
import sys


def flatten_json_leaving_lists(data, parent_key='', sep='.'):
    
    flat_list = []

    if isinstance(data, dict):
        flat_dict = {}
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                # Flatten nested dictionary
                #nested_flat_list = flatten_json_leaving_lists(v, new_key, sep=sep)
                #if nested_flat_list:
                #    flat_dict.update(nested_flat_list[0])
                flat_dict[new_key] = [v]
            elif isinstance(v, list):
                # check is it is list of dict
                flat_dict[new_key] = v
            else:
                # Primitive value
                flat_dict[new_key] = v
        flat_list.append(flat_dict)
    elif isinstance(data, list):
        # Process each item in the list
        for item in data:
            item_flat_list = flatten_json_leaving_lists(item, parent_key=parent_key, sep=sep)
            flat_list.extend(item_flat_list)
    else:
        # Data is a primitive value
        flat_list.append({parent_key or 'value': data})

    return flat_list
