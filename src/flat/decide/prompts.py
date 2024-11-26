PATTERN_PROMPT = """
Given the following JSON keys:
{keys}
Identify if there is a pattern in these keys. If yes, return the regex pattern. If no, return "no pattern".
#What patterns to indetify
Keys having similar structure
Keys having similar data, like a uuid or timestamp

#What patterns to not identify
Keys having same primitive data type, like string
Keys having vastly different meaning
"""

PREFIX_OR_PROPERTY_PROMPT =  """ You are a data cleaning expert. 
        The json below will be turned into a flat json which look like this
        [
        {{
        ..
        }},
        {{
        ..
        }}
        ]
        Given the JSON sample: {json_obj}, should the key '{key}' be a prefix or a property?
        Prefix is {{A:{{B:c}}}} --> [{{A.B:c}}]
        Property is {{A:{{B:c}}}} --> [{{B:c,"key_name":A}}]
        To decide, you need to consider data redudency and the meaningfulness.
        For example in case of location:{{x:..}} it makes sense to unnest and prefix
        While for player_123:{{...}}, it makes snese to {{player_id:player_123}}
        """

KEY_NAME_PROMPT ="""Suggest a key name for this property {key} for addition to following JSON structure: {json_obj}."""