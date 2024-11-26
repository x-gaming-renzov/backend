import os
import openai
import logging

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
    prompt = prompts.PREFIX_OR_PROPERTY_PROMPT.format(json_obj=json_obj, key=key)
    messages = [
        # {"role": "system", "content": "Decide if the key should be a prefix or a property."},
        {"role": "user", "content": prompt},    ]
    result = call_tool(messages, "decide_prefix_or_property")
    logging.info(f"decision : {result}")
    return eval(result).get("decision")  # Extract decision

def suggest_key_name(json_obj, key,model=None):
    prompt = prompts.KEY_NAME_PROMPT.format(json_obj=json_obj, key=key)
    messages = [
        # {"role": "system", "content": "Suggest a meaningful key name for the JSON structure."},
        {"role": "user", "content": prompt},
    ]
    result = call_tool(messages, "suggest_key_name")
    logging.info(f"suggest : {result}")
    return eval(result).get("key_name")  # Extract key name