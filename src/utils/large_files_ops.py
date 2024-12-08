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

def rename_field_in_json(data, old_field_name, new_field_name):
    """if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            # Rename the key if it matches the old_field_name
            new_key = new_field_name if key == old_field_name else key
            # Recursively process the value
            new_data[new_key] = rename_field_in_json(value, old_field_name, new_field_name)
        return new_data
    elif isinstance(data, list):
        # If it's a list, process each element recursively
        return [rename_field_in_json(item, old_field_name, new_field_name) for item in data]
    else:
        # Return the data as is if it's neither a dict nor a list
        return data"""
    
    data_str = json.dumps(data)
    data_str = data_str.replace(f'"{old_field_name}"', f'"{new_field_name}"')
    return json.loads(data_str)
