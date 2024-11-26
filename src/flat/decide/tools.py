pattern_tool = {
    "name": "find_pattern_in_keys",
    "description": "Identify patterns (regex) in JSON keys.",
    "parameters": {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The regex pattern that matches the keys, or 'no pattern' if no pattern exists.",
            }
        },
        "required": ["pattern"],
    },
}

decide_tool = {
    "name": "decide_prefix_or_property",
    "description": "Decide if a key should be a prefix (unnested fields) or its own property.",
    "parameters": {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["prefix", "property"],
                "description": "Should the key be treated as a prefix or a property?",
            }
        },
        "required": ["decision"],
    },
}

suggest_tool = {
    "name": "suggest_key_name",
    "description": "Suggest a meaningful key name for a JSON structure.",
    "parameters": {
        "type": "object",
        "properties": {
            "key_name": {
                "type": "string",
                "description": "A meaningful name for the key.",
            }
        },
        "required": ["key_name"],
    },
}
