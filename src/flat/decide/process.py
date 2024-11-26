import logging
from . import llm

def process_single_key(json_data, key, model=None):
    logging.info(f"Processing single key: {key}")
    key_data = json_data[key]

    # Decide whether to unnest (prefix) or send inside (property)
    action = llm.decide_prefix_or_property(key_data, key, model)
    if action == "property":
        key_name = llm.suggest_key_name(key_data,key, model)
        return {"pattern": key, "action": "property", "key_name": key_name}
    elif action == "prefix":
        return {"pattern": key, "action": "prefix", "key_name": None}

    logging.warning(f"Action not decided for key: {key}")
    return {"pattern": key, "action": None, "key_name": None}