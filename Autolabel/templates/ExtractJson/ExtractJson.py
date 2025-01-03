from langgraph.graph import StateGraph, START, END

from .nodes.nodes import *
from .states.states import *

import os, pathlib, json, dotenv
from termcolor import colored

dotenv.load_dotenv()

def get_graph():
    graph = StateGraph(ExtractJsonState)

    graph.add_node("generate_field_info", generate_field_info)
    graph.add_node("generate_json_data", generate_json_data)
    graph.add_node("rejoine_json_batches", rejoine_json_batches)

    graph.add_edge(START, "generate_field_info")
    graph.add_edge("generate_field_info", "generate_json_data")
    graph.add_edge("generate_json_data", "rejoine_json_batches")
    graph.add_edge("rejoine_json_batches", END)

    compiled_graph = graph.compile()

    return compiled_graph

def run(task_info, user_id, chunk_context, data : List, json_object_context=None):
    cache_path = f"{os.getcwd()}/cache/ExtractJson/{user_id}/"
    os.makedirs(cache_path, exist_ok=True)

    with open(f"{cache_path}/data.txt", "w") as f:
        data = [f"{str(i)}\n\n" for i in data]
        f.writelines(data)
    data = None

    compiled_graph = get_graph()

    state = compiled_graph.invoke({
        "task_info": task_info,
        "user_id": user_id,
        "chunk_context": chunk_context,
        "cache_path": cache_path
    })

    with open(f"{cache_path}/final_json_data.json", "r") as f:
        result_data = json.load(f)
    with open(f"{cache_path}/final_json_info.json", "w") as f:
        f.write(json.dumps(state["json_object_info"].model_dump(), indent=4))

    return result_data
