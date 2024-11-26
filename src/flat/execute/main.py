import sys
import json
import argparse

sys.path.append('..')

from .util import load_json, save_json
from .process import flatten_json


def parse_arguments_for_script():
    """
    Parse command-line arguments for the JSON flattener, and return them as a dictionary.
    
    :return: Dictionary of parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Flatten JSON files based on action configuration.',
        epilog='Example: python main.py -d data.json -a action.json -o output.json'
    )
    
    # Required arguments
    parser.add_argument(
        '-d', '--data', 
        type=str, 
        required=True, 
        help='Path to the input data JSON file'
    )
    
    parser.add_argument(
        '-a', '--action', 
        type=str, 
        required=True, 
        help='Path to the action JSON file'
    )
    
    # Optional arguments
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        default='flattened_output.json', 
        help='Path to the output JSON file (default: flattened_output.json)'
    )
    
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true', 
        help='Enable verbose output'
    )
    
    # Return parsed arguments as a dictionary
    args = parser.parse_args()
    return vars(args)

def flatten_json_from_args(args):
    """
    Takes the parsed arguments and performs the JSON flattening functionality.
    
    :param args: Parsed arguments dictionary
    """
    try:
        # Load input JSON files
        data_json = load_json(args['data'])
        action_json = load_json(args['action'])
        
        # Perform flattening
        flattened_result = flatten_json(data_json, action_json)

        print(flattened_result)
        
        # Save the result
        save_json(flattened_result, args['output'])
        
        # Verbose output
        if args['verbose']:
            print(f"Input data file: {args['data']}")
            print(f"Action configuration file: {args['action']}")
            print(f"Flattened output saved to: {args['output']}")
            print(f"Total events processed: {len(flattened_result)}")
    
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

def main():
    """
    Main function to process JSON flattening from command-line arguments
    """
    # Parse arguments using the reusable function
    args = parse_arguments_for_script()
    
    # Perform the flattening operation with the parsed arguments
    flatten_json_from_args(args)

if __name__ == "__main__":
    main()
