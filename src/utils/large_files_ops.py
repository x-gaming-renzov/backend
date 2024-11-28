import tiktoken

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