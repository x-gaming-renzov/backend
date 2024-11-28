import tiktoken

def return_prompt_adjusted_values(data_type:str, values:list):
    #check if field_data types can be very large ie list, str, bytes, set, tuple etc
    if data_type in ['list', 'set', 'tuple', 'dict', 'bytes', 'str', 'bytearray']:
        #convert to string and check if larger than 1000 characters
        temp_field_values = [str(value) for value in values]
        if any(len(value) > 1000 for value in temp_field_values):
            #save only first 1000 characters as str leaving field_data_type unchanged
            field_values = [value[:1000] for value in temp_field_values]
        else:
            field_values = temp_field_values
    else:
        field_values = values
    return field_values

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens