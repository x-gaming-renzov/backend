import tiktoken, json
from src.states.extrect_correct_field_names_states import FieldInfo



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

def get_field_info_list(data, field_info_list=None):
    if field_info_list is None:
        field_info_list = []

    field_names = [field_info['field_name'] for field_info in field_info_list]
    new_fields = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key not in field_names:
                new_field_info = {
                    "field_name": key,
                    "field_type": str(type(value).__name__),
                    "field_description": 'None',
                    "field_values": [return_prompt_adjusted_values(type(value), value)],
                    "elements_where_field_present": [return_prompt_adjusted_values(type(value), value)]
                }
                new_fields.append(new_field_info)
            else:
                # Find the existing field and update if lengths are less than 3
                for field_info in field_info_list:
                    if field_info['field_name'] == key:
                        if len(field_info['field_values']) < 3:
                            field_info['field_values'].append(return_prompt_adjusted_values(type(value), value))
                        if len(field_info['elements_where_field_present']) < 3:
                            field_info['elements_where_field_present'].append(return_prompt_adjusted_values(type(value), value))
            # Recursive call
            get_field_info_list(value, field_info_list)

    elif isinstance(data, list):
        for item in data:
            get_field_info_list(item, field_info_list)

    # Add new fields after iteration to avoid modifying the list during iteration
    field_info_list.extend(new_fields)
    return field_info_list



