import json
import os

def load_json(file_path):
    """
    Load JSON from a file.
    
    :param file_path: Path to the JSON file
    :return: Loaded JSON data
    :raises FileNotFoundError: If the file doesn't exist
    :raises json.JSONDecodeError: If the file is not valid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        raise
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {file_path}")
        raise

def save_json(data, file_path, indent=2):
    """
    Save data to a JSON file.
    
    :param data: Data to be saved
    :param file_path: Path to save the JSON file
    :param indent: Indentation for pretty printing (default: 2)
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=indent)
        print(f"Successfully saved data to {file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")
    except TypeError as e:
        print(f"Error serializing data: {e}")