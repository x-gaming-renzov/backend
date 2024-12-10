from src.nodes.extrect_correct_field_names_nodes import get_first_few_elements, get_element_meaning, preprocess_field_info, generate_field_name_description, save_field_info, regenerate_field_name, process_whole_file_in_batches, rejoin_batches, score_generation, regenerate_low_scored_fields, process_whole_file
from src.states.extrect_correct_field_names_states import ExtractCorrectFieldNamesStates
from src.nodes.extrect_correct_field_names_nodes import  retrive_node, should_retrive_for_element_info, should_regenrate_fields
from langgraph.graph import StateGraph, START, END

def get_feild_name_correcting_task_graph():
    workflow = StateGraph(ExtractCorrectFieldNamesStates)

    workflow.add_node("get_first_few_elements", get_first_few_elements)
    workflow.add_node("get_element_meaning", get_element_meaning)
    workflow.add_node("preprocess_field_info", preprocess_field_info)
    workflow.add_node("generate_field_name_description", generate_field_name_description)
    workflow.add_node("retireve", retrive_node)
    workflow.add_node("save_field_info", save_field_info)
    workflow.add_node("regenerate_field_name", regenerate_field_name)
    workflow.add_node("generate_score_for_new_fields", score_generation)
    workflow.add_node("regenerate_low_scored_names", regenerate_low_scored_fields)
    workflow.add_node("rejoin_batches", rejoin_batches)
    workflow.add_node("process_whole_file_in_batches", process_whole_file_in_batches)

    workflow.add_conditional_edges(
        "get_element_meaning",
        should_retrive_for_element_info,
        {"continue" : "preprocess_field_info", "retireve" : "retireve"}
    )

    workflow.add_conditional_edges(
        "regenerate_low_scored_names",
        should_regenrate_fields,
        {"regenerate_field_name" : "regenerate_field_name", "continue" : "save_field_info"}
    )

    workflow.add_conditional_edges(
        "regenerate_field_name",
        should_regenrate_fields,
        {"regenerate_field_name" : "regenerate_field_name", "continue" : "save_field_info"}
    )
    workflow.add_edge("get_first_few_elements", "get_element_meaning")
    workflow.add_edge("preprocess_field_info", "generate_field_name_description")
    workflow.add_edge("generate_field_name_description", "generate_score_for_new_fields")
    workflow.add_edge("generate_score_for_new_fields", "regenerate_low_scored_names")
    workflow.add_edge("retireve", 'get_element_meaning')
    workflow.add_edge("save_field_info", "process_whole_file_in_batches")
    workflow.add_edge("process_whole_file_in_batches", "rejoin_batches")
    workflow.add_edge("rejoin_batches", END)

    workflow.add_edge(START, "get_first_few_elements")

    compiled_workflow = workflow.compile()

    #save the compiled workflow image 
    img = compiled_workflow.get_graph().draw_mermaid_png()
    with open('workflow.png', 'wb') as f:
        f.write(img)

    return compiled_workflow
