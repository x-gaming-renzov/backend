import os
import shutil
import argparse
import json
import sys

sys.path.append('.')

from .plan.main import process_json  # Assuming plan/main.py has this function
from .execute.main import flatten_json_from_args  # Assuming execute/main.py has this function

def parse_arguments():
    """
    Parse command-line arguments for input directory and filename.
    """
    parser = argparse.ArgumentParser(description="Process a JSON file and generate a flattened output.")
    
    parser.add_argument(
        '-d', '--directory', 
        type=str, 
        required=True, 
        help="Directory containing the data JSON file"
    )
    
    parser.add_argument(
        '-f', '--filename', 
        type=str, 
        required=True, 
        help="Name of the data JSON file"
    )
    
    return parser.parse_args()

def load_json(file_path):
    """
    Load a JSON file from the given path and return the parsed data.
    """
    with open(file_path, 'r') as f:
        return json.load(f)

def main(input_dir, input_file, output_file):
    """
    Main function to generate action JSON, flatten the data, and save the output.
    """
    # Parse the command-line arguments
    
    # Define the paths for the input and output files
    input_path = os.path.join(input_dir, input_file)
    output_path = os.path.join(input_dir, output_file)
    original_path = os.path.join(input_dir, "original.json")

    # Step 1: Make a copy of the input JSON as original.json
    try:
        shutil.copy(input_path, original_path)
        print(f"Original JSON copied to: {original_path}")
    except Exception as e:
        print(f"Error copying original JSON: {e}")
        return

    # Step 2: Generate action.json using the plan module
    try:
        # Assuming the function in plan.main.py is `generate_action_json`
        data_json = load_json(input_path) 
        action_json = process_json(data_json)
        
        # Save action.json to a file in the same directory
        action_path = os.path.join(input_dir, "action.json")
        with open(action_path, 'w') as f:
            json.dump(action_json, f, indent=2)
        print(f"Action JSON saved to: {action_path}")
    except Exception as e:
        print(f"Error generating action JSON: {e}")
        return

    # Step 3: Use execute.main.py to flatten the JSON using the action JSON
    try:
        # Prepare the arguments for execute.main.py
        execute_args = {
            'data': input_path,    # Path to the original data JSON
            'action': action_path,  # Path to the action JSON
            'output': output_path,  # Path to save the flattened JSON
            'verbose': False        # Optional, set to True if you want verbose output
        }
        
        # Call the flatten_json_from_args function from execute.main.py
        flatten_json_from_args(execute_args)
        print(f"Flattened JSON saved to: {output_path}")
    except Exception as e:
        print(f"Error flattening JSON: {e}")
        return

if __name__ == "__main__":
    main()
