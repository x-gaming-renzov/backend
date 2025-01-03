from langgraph.graph import StateGraph, START, END

import os, pathlib, json, dotenv
from termcolor import colored
import uuid

from .nodes.nodes import *
from .states.states import *

dotenv.load_dotenv()

class GenerateCleanMetadata:
    def __init__(self, data_path : str, kb_path : str, cache_path : str = "./cache", user_id=None):
        #check if cache path exists
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        self.data_path = data_path
        self.kb_path = kb_path
        self.cache_path = cache_path
        self.user_id = user_id if user_id is not None else str(uuid.uuid4())

    def get_graph(self):
        graph = StateGraph(GenerateCleanMetadataStates)

        graph.add_node("pre_process", pre_process)
        graph.add_node("generate_description", generate_description)
        graph.add_node("generate_field_name", generate_field_name)
        graph.add_node("access_semantic_clarity", access_semantic_clarity)
        graph.add_node("regenerate_low_scoring_fields", regenerate_low_scoring_fields)

        graph.add_edge(START, "pre_process")
        graph.add_edge("pre_process", "generate_description")
        graph.add_edge("generate_description", "generate_field_name")
        graph.add_edge("generate_field_name", "access_semantic_clarity")
        graph.add_edge("access_semantic_clarity", "regenerate_low_scoring_fields")
        graph.add_edge("regenerate_low_scoring_fields", END)

        compiled_graph = graph.compile()

        return compiled_graph
    
    def run(self):
        print(colored("Running GenerateCleanMetadata", "cyan"))
        graph = self.get_graph()
        print(colored("Graph compiled", "green"))
        
        # Run the graph
        print(colored("Running the graph", "cyan"))
        output = graph.invoke({
                            "data_path" : self.data_path,
                            "kb_path" : self.kb_path,
                            "cache_path" : self.cache_path,
                        })
        print(colored("Graph run successfully", "green"))
        
        field_mapping = {}
        enhanced_descriptions = {}
        semantic_clarity_report = {}

        print(colored("Generating metadata", "cyan"))

        for fieldinfo in output['field_info_list']:
            if isinstance(fieldinfo, FieldInfo):
                field_mapping[fieldinfo.old_name] = fieldinfo.new_name
                enhanced_descriptions[fieldinfo.old_name] = fieldinfo.description
                semantic_clarity_report[fieldinfo.old_name] = {
                    "old_field_name" : fieldinfo.old_name,
                    "new_field_name" : fieldinfo.new_name,
                    "clarity_improvement_score" : fieldinfo.semantic_clarity_score,
                    "justification" : fieldinfo.semantic_justification

                }
        
        metadata_obj = {
                "field_mapping": field_mapping,
                "enhanced_descriptions": enhanced_descriptions,
                "semantic_clarity_report": semantic_clarity_report,
            }
        
        print(colored("Metadata generated successfully", "green"))
        
        return metadata_obj

        