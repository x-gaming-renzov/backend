import os
import openai
import logging
import sys
import json

sys.path.append('..')

from . import prompts
from .tools import pattern_tool, decide_tool, suggest_tool

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")

TOOLS = [pattern_tool, decide_tool, suggest_tool]    

def call_tool(messages, tool_name, model="gpt-4o"):
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        functions=TOOLS,
        function_call={"name": tool_name},
    )
    return response.choices[0].message.function_call.arguments

def sanitize_json(json_obj, char_limit=200):
    """
    Sanitizes a JSON object (dict or list) into a truncated JSON string representation,
    preserving JSON-like structure and truncating inner objects/lists as necessary.
    
    Args:
        json_obj (dict or list): The JSON object to sanitize.
        char_limit (int): Maximum length of the output string (default is 500).
    
    Returns:
        str: Sanitized JSON string representation, truncated if necessary.
    """
    def truncate_json(obj, current_length=0):
        """
        Recursively processes a JSON object to build a truncated JSON-like string.
        
        Args:
            obj: The current JSON object (dict, list, or primitive).
            current_length: The current length of the resulting string.
        
        Returns:
            str: Truncated JSON string representation of the object.
            int: The updated length of the string.
        """
        if current_length >= char_limit:
            return "", current_length

        if isinstance(obj, dict):
            result = "{"
            for i, (key, value) in enumerate(obj.items()):
                key_str = json.dumps(key) + ": "
                value_str, new_length = truncate_json(value, current_length + len(result) + len(key_str))
                
                if current_length + len(result) + len(key_str) + new_length + 1 > char_limit:
                    result += "..."  # Truncate if adding more would exceed limit
                    return result, current_length + len(result)
                
                result += key_str + value_str
                current_length += len(key_str) + new_length
                if i < len(obj) - 1 and current_length + 1 < char_limit:
                    result += ", "
                    current_length += 2
                else:
                    break
            result += "}"
            return result, len(result)
        
        elif isinstance(obj, list):
            result = "["
            for i, item in enumerate(obj):
                item_str, new_length = truncate_json(item, current_length + len(result))
                
                if current_length + len(result) + new_length + 1 > char_limit:
                    result += "..."  # Truncate if adding more would exceed limit
                    return result, current_length + len(result)
                
                result += item_str
                current_length += new_length
                if i < len(obj) - 1 and current_length + 1 < char_limit:
                    result += ", "
                    current_length += 2
                else:
                    break
            result += "]"
            return result, len(result)
        
        else:
            # Primitive types (string, int, float, bool, None)
            primitive_str = json.dumps(obj)  # Ensure proper JSON formatting
            if current_length + len(primitive_str) > char_limit:
                return "...", current_length + 3
            return primitive_str, len(primitive_str)

    sanitized_str, _ = truncate_json(json_obj)
    return sanitized_str

def find_pattern_in_keys(keys,model="gpt-4o"):
    prompt = prompts.PATTERN_PROMPT.format(keys=keys)
    messages = [
        # {"role": "system", "content": "Identify patterns in the provided keys."},
        {"role": "user", "content": prompt},
    ]
    result = call_tool(messages, "find_pattern_in_keys")
    logging.info(f"pattern : {result}")
    return eval(result).get("pattern")  # Extract pattern

def decide_prefix_or_property(json_obj, key,model="gpt-4o"):
    sanitized_json = sanitize_json(json_obj)
    prompt = prompts.PREFIX_OR_PROPERTY_PROMPT.format(json_obj=sanitized_json, key=key)
    messages = [
        # {"role": "system", "content": "Decide if the key should be a prefix or a property."},
        {"role": "user", "content": prompt},    ]
    result = call_tool(messages, "decide_prefix_or_property")
    logging.info(f"decision : {result}")
    return eval(result).get("decision")  # Extract decision

def suggest_key_name(json_obj, key,model=None):
    sanitized_json = sanitize_json(json_obj)
    prompt = prompts.KEY_NAME_PROMPT.format(json_obj=sanitized_json, key=key)
    messages = [
        # {"role": "system", "content": "Suggest a meaningful key name for the JSON structure."},
        {"role": "user", "content": prompt},
    ]
    result = call_tool(messages, "suggest_key_name")
    logging.info(f"suggest : {result}")
    return eval(result).get("key_name")  # Extract key name

if __name__=="__main__":
    json_obj = {
    "name": "John Doe",
    "age": 30,
    "address": {
        "street": "123 Main St",
        "city": "Anytown"
    },
    "hobbies": ["reading", "coding", {"sports": ["soccer", "tennis"]}],
    "active": True
    }

    result = sanitize_json(json_obj, char_limit=100)
    print(result)