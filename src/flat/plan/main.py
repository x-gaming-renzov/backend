import sys
import os
import logging
import json

sys.path.append('..')

from .treeplan import TreePlan  # Importing the TreePlan class from treeplan.py

logging_enabled = os.getenv("LOGGING_ENABLED", "False").lower() == "true"

def process_json(json_data, output_file=None):
    """
    Takes in a JSON object, processes it using the TreePlan class,
    and optionally saves the processed tree to a file.
    
    Args:
        json_data: The input JSON data.
        output_file (str, optional): The file path to save the processed JSON.
    """
    # Instantiate the TreePlan class
    tree_plan = TreePlan()

    # Step 1: Process the input JSON data to build the tree
    tree_plan.process_json(json_data)

    # Step 2: Process the tree to apply regex patterns and other logic
    tree_plan.process()

    # Step 3: Get the final processed tree structure
    processed_tree = tree_plan.get()

    # If an output file is specified, save the processed tree to the file
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(processed_tree, f, indent=2)
        logging.info(f"Processed tree saved to {output_file}")
    
    return processed_tree

def read_json_from_file(file_path):
    """
    Reads a JSON file from the given path and returns the parsed data.
    """
    with open(file_path, 'r') as file:
        return json.load(file)

def setup_logging():
    if logging_enabled:
        # Configure the root logger to show logs at INFO level or higher
        logging.basicConfig(
            level=logging.INFO,  # Set the root logger level to INFO
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.info("Logging enabled!")
        
        # Suppress log messages from external libraries (set their log level to WARNING or higher)
        logging.getLogger("urllib3").setLevel(logging.WARNING)  # Example: Suppress urllib3 logs
        logging.getLogger("openai").setLevel(logging.WARNING)   # Example: Suppress OpenAI logs
        logging.getLogger("requests").setLevel(logging.WARNING)  # Example: Suppress Requests library logs
        logging.getLogger("httpx").setLevel(logging.WARNING)  # Example: Suppress Requests library logs
        logging.getLogger("certifi").setLevel(logging.WARNING)  # Example: Suppress Requests library logs
        
    else:
        # Disable logging entirely
        logging.basicConfig(level=logging.CRITICAL)

if __name__ == "__main__":
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser(description="Process a JSON file and build a tree structure.")
    parser.add_argument('json_file', type=str, help="Path to the JSON file to process")
    parser.add_argument('--output_file', type=str, help="Path to save the processed JSON tree (optional)")
    args = parser.parse_args()

    # Initialize TreePlan and read the JSON
    json_data = read_json_from_file(args.json_file)

    # Process the JSON with optional output file
    processed_tree = process_json(json_data, output_file=args.output_file)

    # Print the processed tree
    # logging.getLogger(json.dumps(processed_tree, indent=2))
    logger = logging.getLogger()
    logger.info(json.dumps(processed_tree, indent=2))