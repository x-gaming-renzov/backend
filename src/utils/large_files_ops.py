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
    """
    Recursively renames fields in a JSON structure (dict or list).
    """
    if isinstance(data, dict):
        return {
            new_field_name if k == old_field_name else k: rename_field_in_json(v, old_field_name, new_field_name)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [rename_field_in_json(item, old_field_name, new_field_name) for item in data]
    else:
        return data

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