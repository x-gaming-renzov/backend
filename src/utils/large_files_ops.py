import tiktoken, json

def return_prompt_adjusted_values(data_type:str, values):
    temp_value = str(values)
    if len(temp_value) > 100:
        temp_value = temp_value[:100] + "..."
    return temp_value

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens

def rename_field_single_pass(data, field_map):
    """
    Single-pass renaming using a hashmap of old -> new field names.
    """
    if isinstance(data, dict):
        return {
            field_map.get(key, key): rename_field_single_pass(value, field_map)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [rename_field_single_pass(item, field_map) for item in data]
    else:
        return data

def rename_field_in_json(data, old_field_name, new_field_name):
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            # Rename the key if it matches the old_field_name
            new_key = new_field_name if key == old_field_name else key
            new_data[new_key] = rename_field_in_json(value, old_field_name, new_field_name)
        return new_data

    elif isinstance(data, list):
        # Recursively apply the function to each item in the list
        return [rename_field_in_json(item, old_field_name, new_field_name) for item in data]

    # If data is not a dict or list, return it as is
    return data

def get_field_info_list(data):
    field_info_list = []
    if isinstance(data, dict):
        for key, value in data.items():
            field_info_list.append({
                    "field_name": key,
                    "field_type": str(type(value).__name__),
                    "field_description": 'None',
                    "field_values": [return_prompt_adjusted_values(type(value), value)],
                    "elements_where_field_present": [return_prompt_adjusted_values(type(value), value)]
                })
            field_info_list.extend(get_field_info_list(value))
    elif isinstance(data, list):
        for item in data:
            field_info_list.extend(get_field_info_list(item))
    return field_info_list