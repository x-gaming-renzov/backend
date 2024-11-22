import os, pathlib, json, dotenv
from termcolor import colored
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain.tools.retriever import create_retriever_tool

from ..prompts.exctract_correct_field_names_template import generate_meaning_of_elements_in_data_prompt
from ..states.extrect_correct_field_names_states import ExtractCorrectFieldNamesStates
from ..tools.retriever_tool import get_retriever
from ..utils.large_files_ops import return_prompt_adjusted_values

dotenv.load_dotenv()
def get_retriver_tool():
    urls = [
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/block/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/enchantment/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/entity/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/hanging/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/inventory/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/player/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/server/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/vehicle/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/weather/package-summary.html',
        'https://hub.spigotmc.org/javadocs/spigot/org/bukkit/event/world/package-summary.html',
    ]
    retriever = get_retriever(urls)
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_knowledge_from_docs",
        "Retrieve knowledge from documents provided by the user",
    )
    return retriever_tool

model = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), streaming=True)

elements_meaning_generator_model = model.bind_tools([get_retriver_tool()])

elements_meaning_generator = generate_meaning_of_elements_in_data_prompt | elements_meaning_generator_model

def get_first_few_elements(ExtractCorrectFieldNamesStates : ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    # Check if directory exists
    temp_dir_path = os.getcwd() + f'/temp/{ExtractCorrectFieldNamesStates["user_id"]}/{ExtractCorrectFieldNamesStates["user_session_id"]}'
    print(colored(f"Checking if directory exists: {temp_dir_path}", 'blue'))
    pathlib.Path(temp_dir_path).mkdir(parents=True, exist_ok=True)
    print(colored(f"Directory checked/created: {temp_dir_path}", 'green'))

    try:
        # Open file and get first few elements
        print(colored(f"Opening file: {ExtractCorrectFieldNamesStates['file_name']}", 'blue'))
        with open(f'{temp_dir_path}/{ExtractCorrectFieldNamesStates["file_name"]}', 'r') as f:
            ExtractCorrectFieldNamesStates['first_few_elements'] = json.load(f)[:10]
            print(colored("First few elements extracted successfully", 'green'))
            return ExtractCorrectFieldNamesStates
    except FileNotFoundError:
        print(colored("File not found", 'red'))
        # Initiate re-flatten process
        print(colored("Initiating re-flatten process", 'green'))
        return None
    except json.JSONDecodeError:
        print(colored("Error decoding JSON from file", 'red'))
        return None

def get_element_meaning(ExtractCorrectFieldNamesStates : ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    elements_meaning_generator_result = elements_meaning_generator.invoke(
        {
            "data_info_from_user": ExtractCorrectFieldNamesStates["data_info_from_user"],
            "first_few_elements": ExtractCorrectFieldNamesStates["first_few_elements"]
        }
    )
    ExtractCorrectFieldNamesStates["meaning_of_elements_in_data"] = elements_meaning_generator_result.content
    ExtractCorrectFieldNamesStates["messages"] = [elements_meaning_generator_result]
    return ExtractCorrectFieldNamesStates

def should_retrive_for_element_info(ExtractCorrectFieldNamesStates : ExtractCorrectFieldNamesStates) -> Literal["retireve", "preprocess_field_info"]:
    last_message = ExtractCorrectFieldNamesStates["messages"][-1]
    if last_message.tool_calls:
        return "retrieve"
    return "preprocess_field_info"

def preprocess_field_info(ExtractCorrectFieldNamesStates : ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    temp_dir_path = os.getcwd() + f'/temp/{ExtractCorrectFieldNamesStates["user_id"]}/{ExtractCorrectFieldNamesStates["user_session_id"]}'

    try:
        # Open file and get first few elements
        print(colored(f"Opening file: {ExtractCorrectFieldNamesStates['file_name']}", 'blue'))
        with open(f'{temp_dir_path}/{ExtractCorrectFieldNamesStates["file_name"]}', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(colored("File not found", 'red'))
        # Initiate re-flatten process
        print(colored("Initiating re-flatten process", 'green'))
        return None
    except json.JSONDecodeError:
        print(colored("Error decoding JSON from file", 'red'))
        return None
    
    field_info_list = []
    unique_fields = set()

    for element in data:
        for key in element.keys():
            if key not in unique_fields:
                unique_fields.add(key)
                field_info_list.append({
                    "field_name": key,
                    "field_type": type(element[key]),
                    "field_description": None,
                    "field_values": [return_prompt_adjusted_values(type(element[key]),element[key])],
                    "elements_where_field_present": [return_prompt_adjusted_values(type(element),element)]
                })
            else:
                for field in field_info_list:
                    if field["field_name"] == key:
                        #check if len of field_values is greater than 5. if yes, then exit loop
                        if len(field["field_values"]) > 5:
                            break
                        field["field_values"].append(return_prompt_adjusted_values(type(element[key]),element[key]))
                        field["elements_where_field_present"].append(return_prompt_adjusted_values(type(element),element))
                        break
    ExtractCorrectFieldNamesStates["field_info_list"] = field_info_list
            
    
    return ExtractCorrectFieldNamesStates

def retrive_node(ExtractCorrectFieldNamesStates : ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    tool = get_retriever()
    last_message = ExtractCorrectFieldNamesStates["messages"][-1]
    questions = last_message.tool_calls[0]['questions']
    answers = []
    for i in range(len(questions)):
        answers.append(tool.retrieve(questions[i]))
    tool_meesage = ToolMessage(content=str(answers))
    ExtractCorrectFieldNamesStates["messages"].append(tool_meesage)

    return ExtractCorrectFieldNamesStates