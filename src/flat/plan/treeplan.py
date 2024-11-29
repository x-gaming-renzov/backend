import sys

sys.path.append('..')

import re
from collections import deque,defaultdict
import logging
from ..decide.main import decide_and_name

class TreePlan:
    def __init__(self):
        self.tree = {}  # Hierarchical tree structure
        self.regex_map = {}  # Store regex patterns with incremental IDs
        self.regex_counter = 1  # Counter for generating regex IDs
        self.logger = logging.getLogger(__name__)

    def process_json(self, json_data):
        """
        Build a tree from the JSON data, only including dictionary values.
        """
        self.tree = self._build_tree(json_data)

    def _build_tree(self, json_data, parent_path=''):
        """
        Recursively build tree, keeping only dictionary or list values.
        """
        tree = {}
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if isinstance(value, (dict, list)):
                    node_path = f"{parent_path}.{key}" if parent_path else key
                    tree[key] = {
                        'key': key,
                        'type': 'dict' if isinstance(value, dict) else 'list',
                        'action': None,
                        'name': None,
                        'children': self._build_tree(value, node_path)
                    }
        elif isinstance(json_data, list):
            for index, item in enumerate(json_data):
                if isinstance(item, (dict, list)):
                    key = str(index)
                    node_path = f"{parent_path}.{key}" if parent_path else key
                    tree[key] = {
                        'key': key,
                        'type': 'dict' if isinstance(item, dict) else 'list',
                        'action': None,
                        'name': None,
                        'children': self._build_tree(item, node_path)
                    }
        return tree

    def check(self, node, parent_path=''):
        """
        Check if node matches any existing regex patterns.
        """
        node_path = f"{parent_path}.{node['key']}" if parent_path else node['key']
        
        for regex_id, (pattern, _, _) in self.regex_map.items():
            if re.match(pattern, node_path):
                return regex_id
        return None

    def generate(self, nodes):
        """
        Generate regex patterns for a group of nodes.
        If all nodes in the group match a common pattern, a single regex is generated.
        Otherwise, individual patterns are generated for each node.
        """
        keys = list(nodes.keys())  # Extract keys from the JSON structure
        self.logger.info(f"Generating regex for nodes with keys: {keys} under parent path: ")

        json_data = {key: nodes[key]['children'] for key in keys if 'children' in nodes[key]}
        self.logger.info(f"JSON data extracted for decide_and_name: {json_data}")

        # Call decide_and_name to determine patterns
        pattern_info = decide_and_name(json_data, keys)

        if isinstance(pattern_info, list) and all(isinstance(entry, dict) for entry in pattern_info):
            # Multiple patterns generated for different keys
            self.logger.info(f"Generated multiple regex patterns for keys: {keys}")
            self.logger.info(f"Patterns: {pattern_info}")
            return {
                'patterns': pattern_info,
                'keys': keys
            }
        else:
            # Single common pattern for all keys
            self.logger.info(f"Generated single common regex pattern for keys: {keys}")
            self.logger.info(f"Pattern: {pattern_info}")

            if len(nodes) == 1:
                # Single node case
                self.logger.info("Single node case")
                return {
                    'pattern': pattern_info['pattern'],  # Regex pattern
                    'action': pattern_info['action'],  # Action
                    'key_name': pattern_info['key_name'],  # Optional key name
                    'keys': keys
                }
                
            return {
                'pattern': pattern_info[0],  # Regex pattern
                'action': pattern_info[1],  # Action
                'key_name': pattern_info[2],  # Optional key name
                'keys': keys
            }

    def _add_node_to_queue(self, queue, regex_id, node):
        """
        Add node to the queue under the specified regex group.
        If the group doesn't exist, add it to the end of the queue.
        """
        # Check if the regex_id group exists in the queue
        for group in queue:
            if regex_id in group:
                group[regex_id].append(node)
                return
        
        # If no existing group found, create a new group at the end
        queue.append({regex_id: [node]})

    def process(self):
        """
        Grouped BFS traversal to process nodes with regex-based grouping.
        """
        # Initialize BFS queue with root nodes grouped by an initial group ID
        initial_group_id = 0
        queue = deque([{initial_group_id: list(self.tree.values())}])

        while queue:
            # Process current group of nodes
            current_group = queue.popleft()
            self.logger.info("Processing group: %s", current_group)

            # Process each regex group in the current level
            next_level_queue = deque()

            for current_regex_id, nodes in current_group.items():
                self.logger.info("Processing regex group ID: %d, Nodes: %s", current_regex_id, nodes)

                # Try to process up to 3 nodes from the current group
                nodes_to_process = nodes[:3]
                remaining_nodes = nodes[3:]

                self.logger.info("Nodes to process: %s", nodes_to_process)
                self.logger.info("Remaining nodes: %s", remaining_nodes)

                # Process the selected nodes
                if nodes_to_process:
                    matched_regex_id = self.check(nodes_to_process[0])
                    self.logger.info("Matched regex ID: %s", matched_regex_id)

                    if matched_regex_id:
                        # If single node and matches existing regex
                        self.logger.info("Applying existing regex pattern for node: %s", nodes_to_process[0]['key'])
                        
                        pattern, action, name = self.regex_map[matched_regex_id]
                        nodes_to_process[0]['action'] = action
                        nodes_to_process[0]['name'] = name

                        # Add children to queue under the matched regex group
                        if nodes_to_process[0]['children']:
                            children = list(nodes_to_process[0]['children'].values())
                            self.logger.info("Node has children, adding to next level queue: %s", children)
                            for child in children:
                                self._add_node_to_queue(next_level_queue, matched_regex_id, child)
                        
                        # Remove processed node
                        if(len(nodes_to_process) > 1):
                            remaining_nodes.append(nodes_to_process[1])
                        if(len(nodes_to_process) > 2):
                            remaining_nodes.append(nodes_to_process[2])
                        
                    else:
                        # Generate new regex for group of nodes
                        self.logger.info("Generating new regex pattern for nodes: %s", nodes_to_process)
                        nodes_dict = {node['key']: node for node in nodes_to_process}
                        generation_result = self.generate(nodes_dict)
                        self.logger.info("Generation result: %s", generation_result)

                        # Handle single pattern case
                        if 'pattern' in generation_result:
                            # Create new regex entry
                            new_regex_id = self.regex_counter
                            self.regex_counter += 1
                            self.regex_map[new_regex_id] = (
                                generation_result['pattern'], 
                                generation_result.get('action'), 
                                generation_result.get('key_name')
                            )
                            self.logger.info("Created new regex with ID: %d, Pattern: %s", new_regex_id, generation_result['pattern'])

                            # Process and add nodes
                            for node in nodes_to_process:
                                node['action'] = generation_result.get('action')
                                node['name'] = generation_result.get('key_name') or node['key']

                                # Add children to queue under new regex group
                                if node['children']:
                                    children = list(node['children'].values())
                                    self.logger.info("Node has children, adding to next level queue: %s", children)
                                    for child in children:
                                        self._add_node_to_queue(next_level_queue, new_regex_id, child)

                        # Handle multiple pattern case
                        elif 'patterns' in generation_result:
                            for pattern_info in generation_result['patterns']:
                                # Create new regex entry
                                new_regex_id = self.regex_counter
                                self.regex_counter += 1
                                self.regex_map[new_regex_id] = (
                                    pattern_info['pattern'], 
                                    pattern_info['action'], 
                                    pattern_info['key_name']
                                )
                                self.logger.info("Created new regex with ID: %d, Pattern: %s", new_regex_id, pattern_info['pattern'])
                                self.logger.info("Pattern info: %s", pattern_info)
                                # Find and process corresponding nodes

                                for node in nodes_to_process:
                                    if node['key'] == pattern_info['pattern']:
                                        node['action'] = pattern_info['action']
                                        node['name'] = pattern_info['key_name']

                                        # Add children to queue under new regex group
                                        if node['children']:
                                            children = list(node['children'].values())
                                            self.logger.info("Node has children, adding to next level queue: %s", children)
                                            for child in children:
                                                self._add_node_to_queue(next_level_queue, new_regex_id, child)

                if remaining_nodes:
                    self.logger.info("There are remaining nodes, adding them back to queue: %s", remaining_nodes)
                    current_group[current_regex_id] = remaining_nodes
                    queue.appendleft(current_group)

            # If there are nodes for the next level, add to queue
            if next_level_queue:
                self.logger.info("Next level queue has nodes, extending queue")
                queue.extend(next_level_queue)

        self.logger.info("BFS processing complete")

    def print_tree(self, tree=None, indent=0):
        """
        Print the tree structure with indentation.
        """
        if tree is None:
            tree = self.tree
        
        for key, node in tree.items():
            print(" " * indent + f"{key}: action={node['action']}, name={node['name']}")
            if node['children']:
                self.print_tree(node['children'], indent + 2)

    def get(self):
        """
        Return the current tree structure.
        """
        return self.tree