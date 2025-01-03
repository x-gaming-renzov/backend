import ijson
from collections import defaultdict

def extract_keys_and_examples(file_path, num_examples=5):
    """
    Extract unique field 'paths' (prefixes) and collect example values for each, excluding 'N/A' and 'NaN'.

    This version uses ijson's `prefix` to automatically handle nested JSON keys.
    For example, if you have nested structures like:
        {
            "metadata": {
                "author": "Alice"
            },
            "posts": [
                {"title": "Hello", "content": "World"},
                {"title": "Foo", "content": "Bar"}
            ]
        }
    You might end up with paths like:
        - metadata.author
        - posts.item.title
        - posts.item.content
    """
    field_examples = defaultdict(set)

    with open(file_path, 'r') as file:
        parser = ijson.parse(file)
        for prefix, event, value in parser:
            # Only capture actual scalar values at the "leaf" level
            if event in ('string', 'number', 'boolean', 'null'):
                # Exclude placeholders
                if value not in ('N/A', 'NaN', None):
                    # Only store up to num_examples examples per field
                    if len(field_examples[prefix]) < num_examples:
                        field_examples[prefix].add(str(value))

    # Convert sets to lists
    field_examples_dict = {k: list(v) for k, v in field_examples.items()}

    #if any key starts with item. remove that part from key string
    temp = {}
    for key in field_examples_dict:
        if str(key).startswith('item.'):
            temp[str(key)[5:]] = field_examples_dict[key]
    
    field_examples_dict = temp
    print(field_examples_dict)
    temp = None

    # Generate the one-line "basic" descriptions for each field
    field_descriptions = generate_field_descriptions(field_examples_dict)

    return field_examples_dict, field_descriptions

def generate_field_descriptions(field_examples):
    """
    Generate one-liner descriptions for each field based on its sample values.
    """
    field_descriptions = {}
    for field, examples in field_examples.items():
        # Just show a few examples in the description
        preview = return_prompt_adjusted_values(", ".join(examples[:3]))
        description = f"Field '{field}' contains values such as {preview}."
        field_descriptions[field] = description
    return field_descriptions

def return_prompt_adjusted_values(values):
    temp_value = str(values)
    if len(temp_value) > 100:
        temp_value = temp_value[:100] + "..."
    return temp_value

