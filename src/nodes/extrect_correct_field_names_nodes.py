import os, pathlib, json, dotenv
from termcolor import colored
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain.tools.retriever import create_retriever_tool

from ..prompts.exctract_correct_field_names_template import generate_meaning_of_elements_in_data_prompt, generate_field_desc_prompt
from ..states.extrect_correct_field_names_states import ExtractCorrectFieldNamesStates, FieldRenameInfo
from ..tools.retriever_tool import get_retriever
from ..utils.large_files_ops import return_prompt_adjusted_values


dotenv.load_dotenv()

urls = [
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/package-summary.html',
        #'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/player/package-summary.html',
        #'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/entity/package-summary.html',
        #'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/block/package-summary.html',
        #'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/inventory/package-summary.html',
    ]
print(colored("Initializing retriever tool...", "yellow"))
retriever = get_retriever(urls)

def get_retriver_tool():
    
    print(colored("Retriever created successfully", "green"))
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_knowledge_from_docs",
        "Retrieve knowledge from documents provided by the user",
    )
    print(colored("Retriever tool created successfully", "green"))
    return retriever_tool

retriever_tool = get_retriver_tool()

model = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), streaming=True)
print(colored("ChatOpenAI model initialized", "green"))

elements_meaning_generator_model = model.bind_tools([retriever_tool])
elements_meaning_generator = generate_meaning_of_elements_in_data_prompt | elements_meaning_generator_model

small_model = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), streaming=True)
print(colored("ChatOpenAI small model initialized", "green"))

field_definiton_generator_model = small_model
field_definiton_generator_model = field_definiton_generator_model.with_structured_output(FieldRenameInfo)

field_definition_generator = generate_field_desc_prompt | field_definiton_generator_model

def get_first_few_elements(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    temp_dir_path = os.getcwd() + f'/temp/{ExtractCorrectFieldNamesStates.user_id}/{ExtractCorrectFieldNamesStates.user_session_id}'
    print(colored(f"Checking/creating directory: {temp_dir_path}", 'blue'))
    pathlib.Path(temp_dir_path).mkdir(parents=True, exist_ok=True)

    try:
        print(colored(f"Opening file: {ExtractCorrectFieldNamesStates.file_name}", 'blue'))
        with open(f'{temp_dir_path}/{ExtractCorrectFieldNamesStates.file_name}', 'r') as f:
            ExtractCorrectFieldNamesStates['first_few_elements'] = json.load(f)[:10]
            print(colored("First few elements extracted successfully", 'green'))
            return ExtractCorrectFieldNamesStates
    except FileNotFoundError:
        print(colored("File not found. Re-flatten process initiated.", 'red'))
        return None
    except json.JSONDecodeError:
        print(colored("JSON decoding error encountered.", 'red'))
        return None

def get_element_meaning(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    print(colored("Generating meaning of elements in data...", "yellow"))
    elements_meaning_generator_result = elements_meaning_generator.invoke(
        {
            "data_info_from_user": ExtractCorrectFieldNamesStates.data_info_from_user,
            "first_few_elements": ExtractCorrectFieldNamesStates.first_few_elements,
            "messages": ExtractCorrectFieldNamesStates.messages
        }
    )
    print(colored("Meaning of elements generated successfully", "green"))
    ExtractCorrectFieldNamesStates.meaning_of_elements_in_data = elements_meaning_generator_result.content
    ExtractCorrectFieldNamesStates["messages"] = [elements_meaning_generator_result]
    return ExtractCorrectFieldNamesStates

def should_retrive_for_element_info(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates):
    print(colored("Determining next step: retrieve or preprocess field info...", "yellow"))
    last_message = ExtractCorrectFieldNamesStates["messages"][-1]
    if last_message.tool_calls:
        print(colored("Decision: Retrieve element information", "green"))
        return "retrieve"
    print(colored("Decision: Preprocess field information", "green"))
    return "preprocess_field_info"

def preprocess_field_info(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    temp_dir_path = os.getcwd() + f'/temp/{ExtractCorrectFieldNamesStates["user_id"]}/{ExtractCorrectFieldNamesStates["user_session_id"]}'
    print(colored(f"Processing field information in: {temp_dir_path}", "blue"))

    try:
        print(colored(f"Opening file: {ExtractCorrectFieldNamesStates['file_name']}", 'blue'))
        with open(f'{temp_dir_path}/{ExtractCorrectFieldNamesStates["file_name"]}', 'r') as f:
            data = json.load(f)
            print(colored("File data loaded successfully", "green"))
    except FileNotFoundError:
        print(colored("File not found. Re-flatten process initiated.", 'red'))
        return None
    except json.JSONDecodeError:
        print(colored("Error decoding JSON from file.", 'red'))
        return None
    
    field_info_list = []
    accounted_fields = set()
    unique_fields = set()

    for element in data:
        #add all fields to unique_fields
        for key in element.keys():
            unique_fields.add(key)
    
    print(colored(f"Unique fields lenth: {len(unique_fields)}", 'white'))

    for element in data:
        for key in element.keys():
            if element[key] is None:
                continue
            if key not in accounted_fields:
                accounted_fields.add(key)
                print(colored(f"New field added: {key}", 'yellow'))
                field_info_list.append({
                    "field_name": key,
                    "field_type": str(type(element[key])),
                    "field_description": None,
                    "field_values": [return_prompt_adjusted_values(type(element[key]), element[key])],
                    "elements_where_field_present": [return_prompt_adjusted_values(type(element), element)]
                })
            else:
                for field in field_info_list:
                    if field["field_name"] == key:
                        if len(field["field_values"]) > 5:
                            break
                        field["field_values"].append(return_prompt_adjusted_values(type(element[key]), element[key]))
                        field["elements_where_field_present"].append(return_prompt_adjusted_values(type(element), element))
                        break
    print(colored(f"Accounted fields length: {len(accounted_fields)}", 'white'))
    print(colored(f"Field info list length: {len(field_info_list)}", 'white'))
    
    def get_element_with_field_name(field_name):
        count = 0
        elements = []
        for event in data:
            if field_name in event:
                count += 1
                elements.append(event)
                if count >= 3:
                    break
        return elements

    unaccounted_fields = set()
    for data_field in unique_fields : 
        if data_field not in accounted_fields:
            unaccounted_fields.add(data_field)
            print(colored(f"Unaccounted field added: {data_field}", 'yellow'))

    print(colored(f"Unaccounted fields length: {len(unaccounted_fields)}", 'white'))
    
    for unaccounted_field in unaccounted_fields:
        elements = get_element_with_field_name(unaccounted_field)
        elements = [return_prompt_adjusted_values(type(element), element) for element in elements]
        field_info_list.append({
            'field_name': unaccounted_field,
            'field_type': 'None',
            'field_description': 'None',
            'field_values': 'none everywhere',
            'elements_where_field_present': elements})

    ExtractCorrectFieldNamesStates["field_info_list"] = field_info_list
    print(colored("Field information processed successfully", "green"))
    return ExtractCorrectFieldNamesStates

def retrive_node(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    print(colored("Retrieving node information...", "yellow"))
    tool = retriever
    last_message = ExtractCorrectFieldNamesStates["messages"][-1]
    questions = last_message.tool_calls[0]['questions']
    answers = []
    for i in range(len(questions)):
        answers.append(tool.invoke(questions[i]))
    tool_message = ToolMessage(content=str(answers))
    ExtractCorrectFieldNamesStates["messages"].append(tool_message)
    print(colored("Node information retrieved successfully", "green"))

    return ExtractCorrectFieldNamesStates

def generate_field_name_description(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    print(colored("Generating field description...", "yellow"))
    field_info_list = ExtractCorrectFieldNamesStates["field_info_list"]

    for field_info in field_info_list:
        print(colored(f"Generating description for field: {field_info['field_name']}", "blue"))
        dump = retriever.invoke(f"dump {field_info['field_name']}")
        field_definition_generator_result = field_definition_generator.invoke(
            {
                "dump": dump,
                "data_info_from_user": ExtractCorrectFieldNamesStates["data_info_from_user"],
                "meaning_of_elements_in_data": ExtractCorrectFieldNamesStates["meaning_of_elements_in_data"],
                "field_info": field_info
            }
        )
        if isinstance(field_definition_generator_result, FieldRenameInfo):
            field_info['field_description'] = field_definition_generator_result.field_description
            field_info['field_new_name'] = field_definition_generator_result.field_new_name
        else:
            print(colored("Field description generation failed", "red"))
            print(colored(f"Output: {field_definition_generator_result}", "red"))
        print(colored(f"New name generated : {field_info['field_new_name']}", "green"))
        print(colored(f"Description generated : {field_info['field_description']}", "green"))
    ExtractCorrectFieldNamesStates["field_info_list"] = field_info_list
    return ExtractCorrectFieldNamesStates

