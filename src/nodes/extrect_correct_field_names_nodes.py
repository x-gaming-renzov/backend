import os, pathlib, json, dotenv
from termcolor import colored
from typing import Literal
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain.tools.retriever import create_retriever_tool

from ..prompts.exctract_correct_field_names_template import generate_meaning_of_elements_in_data_prompt, generate_field_desc_prompt, regenerate_field_desc_prompt, generate_score_for_new_fields, regenerate_low_scored_names
from ..states.extrect_correct_field_names_states import ExtractCorrectFieldNamesStates, FieldRenameInfo, SemanticScoreResult, SemanticRegenratedName, FieldInfo
from ..tools.retriever_tool import get_retriever
from ..utils.large_files_ops import return_prompt_adjusted_values, num_tokens_from_string


dotenv.load_dotenv()

print(colored("Initializing retriever tool...", "yellow"))
retriever = None
print(colored("Retriever tool initialized successfully", "green"))

def get_retriver_tool(user_id, user_session_id, data_info_from_user):
    print(colored("Initializing retriever tool...", "yellow"))
    retriever = get_retriever(user_id, user_session_id, data_info_from_user)
    print(colored("Retriever tool initialized successfully", "green"))
    print(colored("Retriever created successfully", "green"))
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_knowledge_from_docs",
        "Retrieve knowledge from documents provided by the user",
    )
    print(colored("Retriever tool created successfully", "green"))
    return retriever_tool



model = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), streaming=True)
print(colored("ChatOpenAI model initialized", "green"))

small_model = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), streaming=True)
print(colored("ChatOpenAI small model initialized", "green"))

field_definiton_generator_model = small_model
field_definiton_generator_model = field_definiton_generator_model.with_structured_output(FieldRenameInfo)
semantic_score_generator_model = small_model.with_structured_output(SemanticScoreResult)
regenerate_low_semantic_scored_fields_model = small_model.with_structured_output(SemanticRegenratedName)

field_definition_generator = generate_field_desc_prompt | field_definiton_generator_model
field_name_regenerator = regenerate_field_desc_prompt | field_definiton_generator_model
semantic_score_generator = generate_score_for_new_fields | semantic_score_generator_model
regenerate_low_semantic_scored_fields = regenerate_low_scored_names | regenerate_low_semantic_scored_fields_model

def get_first_few_elements(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    temp_dir_path = os.getcwd() + f'/temp/{ExtractCorrectFieldNamesStates.user_id}/{ExtractCorrectFieldNamesStates.user_session_id}'
    print(colored(f"Checking/creating directory: {temp_dir_path}", 'blue'))
    pathlib.Path(temp_dir_path).mkdir(parents=True, exist_ok=True)

    try:
        print(colored(f"Opening file: {ExtractCorrectFieldNamesStates.file_name}", 'blue'))
        with open(f'{temp_dir_path}/{ExtractCorrectFieldNamesStates.file_name}', 'r') as f:
            first_lines = f.read(1000)
            ExtractCorrectFieldNamesStates.first_few_elements = [first_lines]
            print(colored("First few elements extracted successfully", 'green'))
            return ExtractCorrectFieldNamesStates
    except FileNotFoundError:
        print(colored("File not found. Re-flatten process initiated.", 'red'))
        return None
    except json.JSONDecodeError:
        print(colored("JSON decoding error encountered.", 'red'))
        return None

def get_element_meaning(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    #retriever_tool = get_retriver_tool(ExtractCorrectFieldNamesStates.user_id, ExtractCorrectFieldNamesStates.user_session_id, ExtractCorrectFieldNamesStates.data_info_from_user)
    
    elements_meaning_generator_model = model
    elements_meaning_generator = generate_meaning_of_elements_in_data_prompt | elements_meaning_generator_model

    num_tokens = num_tokens_from_string(str({
            "data_info_from_user": ExtractCorrectFieldNamesStates.data_info_from_user,
            "first_few_elements": ExtractCorrectFieldNamesStates.first_few_elements,
            "messages": ExtractCorrectFieldNamesStates.messages
        }))
    print(colored(f"Number of tokens: {num_tokens}", "yellow"))
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
    ExtractCorrectFieldNamesStates.messages = [elements_meaning_generator_result]
    return ExtractCorrectFieldNamesStates

def should_retrive_for_element_info(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates):
    print(colored("Determining next step: retrieve or preprocess field info...", "yellow"))
    last_message = ExtractCorrectFieldNamesStates.messages[-1]
    if last_message.tool_calls:
        print(colored("Decision: Retrieve element information", "green"))
        return "retireve"
    print(colored("Decision: Preprocess field information", "green"))
    return "continue"

def preprocess_field_info(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    temp_dir_path = os.getcwd() + f'/temp/{ExtractCorrectFieldNamesStates.user_id}/{ExtractCorrectFieldNamesStates.user_session_id}'
    print(colored(f"Processing field information in: {temp_dir_path}", "blue"))

    try:
        print(colored(f"Opening file: {ExtractCorrectFieldNamesStates.file_name}", 'blue'))
        with open(f'{temp_dir_path}/{ExtractCorrectFieldNamesStates.file_name}', 'r') as f:
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
                    "field_type": str(type(element[key]).__name__),
                    "field_description": 'None',
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
            'field_values': ['none everywhere'],
            'elements_where_field_present': elements})

    ExtractCorrectFieldNamesStates.field_info_list = field_info_list
    print(colored("Field information processed successfully", "green"))
    return ExtractCorrectFieldNamesStates

def retrive_node(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    print(colored("Retrieving node information...", "yellow"))
    if ExtractCorrectFieldNamesStates.retriever is None:
        ExtractCorrectFieldNamesStates.retriever = get_retriver_tool(ExtractCorrectFieldNamesStates.user_id, ExtractCorrectFieldNamesStates.user_session_id, ExtractCorrectFieldNamesStates.data_info_from_user)
    tool = ExtractCorrectFieldNamesStates.retriever
    last_message = ExtractCorrectFieldNamesStates.messages[-1]
    print(colored(f"Last message: {last_message.tool_calls[0]}", "blue"))
    questions = last_message.tool_calls[0]['args']['query']
    answers = []
    if type(questions) == str:
        questions = [questions]
    for i in range(len(questions)):
        answers.append(tool.invoke(questions[i], kwargs={"k": 1}))
    tool_message = ToolMessage(content=str(answers), tool_call_id=last_message.tool_calls[0]['id'])
    print(colored(f"Node information retrieved: {answers}", "green"))
    ExtractCorrectFieldNamesStates.messages.append(tool_message)
    print(colored("Node information retrieved successfully", "green"))

    return ExtractCorrectFieldNamesStates

def generate_field_name_description(ExtractCorrectFieldNamesStates):
    print(colored("Generating field description...", "yellow"))
    field_info_list = ExtractCorrectFieldNamesStates.field_info_list

    def process_field(field_info, ExtractCorrectFieldNamesStates):
        print(colored(f"Generating description for field: {field_info.field_name}", "blue"))
        try:
            if ExtractCorrectFieldNamesStates.retriever is None:
                ExtractCorrectFieldNamesStates.retriever = get_retriver_tool(ExtractCorrectFieldNamesStates.user_id, ExtractCorrectFieldNamesStates.user_session_id, ExtractCorrectFieldNamesStates.data_info_from_user)
            dump = ExtractCorrectFieldNamesStates.retriever.invoke(f"dump {field_info.field_name}", kwargs={"k": 1})

            num_tokens = num_tokens_from_string(str({
                "dump": dump,
                "data_info_from_user": ExtractCorrectFieldNamesStates.data_info_from_user,
                "meaning_of_elements_in_data": ExtractCorrectFieldNamesStates.meaning_of_elements_in_data,
                "field_name": field_info.field_name,
                "field_data_type": field_info.field_type,
                "field_values": field_info.field_values,
                "elements_where_field_is_present": field_info.elements_where_field_present
            }))
            print(colored(f"Number of tokens: {num_tokens}", "yellow"))
            
            field_definition_generator_result = field_definition_generator.invoke(
                {
                    "dump": dump,
                    "data_info_from_user": ExtractCorrectFieldNamesStates.data_info_from_user,
                    "meaning_of_elements_in_data": ExtractCorrectFieldNamesStates.meaning_of_elements_in_data,
                    "field_name": field_info.field_name,
                    "field_data_type": field_info.field_type,
                    "field_values": field_info.field_values,
                    "elements_where_field_is_present": field_info.elements_where_field_present
                }
            )
            
            if isinstance(field_definition_generator_result, FieldRenameInfo):
                field_info.field_description = field_definition_generator_result.field_description
                field_info.field_new_name = field_definition_generator_result.field_new_name
                print(colored(f"New name generated : {field_info.field_new_name}", "green"))
                print(colored(f"Description generated : {field_info.field_description}", "green"))
            else:
                print(colored("Field description generation failed", "red"))
                print(colored(f"Output: {field_definition_generator_result}", "red"))
        except Exception as e:
            print(colored(f"Error processing field {field_info.field_name}: {e}", "red"))
        return field_info

    # Use ThreadPoolExecutor to process fields in parallel
    with ThreadPoolExecutor() as executor:
        future_to_field = {executor.submit(process_field, field, ExtractCorrectFieldNamesStates): field for field in field_info_list}
        updated_field_info_list = [future.result() for future in as_completed(future_to_field)]
    
    ExtractCorrectFieldNamesStates.field_info_list = updated_field_info_list
    return ExtractCorrectFieldNamesStates

def save_field_info(ExtractCorrectFieldNamesStates : ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    temp_dir_path = os.getcwd() + f'/temp/{ExtractCorrectFieldNamesStates.user_id}/{ExtractCorrectFieldNamesStates.user_session_id}'
    print(colored(f"Saving field information in: {temp_dir_path}", "blue"))

    #save ExtractCorrectFieldNamesStates in out.json
    with open(f'{temp_dir_path}/out.json', 'w') as f:
        ExtractCorrectFieldNamesStates.retriever = None
        json.dump(json.loads(ExtractCorrectFieldNamesStates.model_dump_json()), f, indent=4)
        print(colored("Field information saved successfully", "green"))
    return ExtractCorrectFieldNamesStates

def fetch_overlapping_field_names(field_info_list):
    same_field_name_dict = {}
    for field_info in field_info_list:
        if field_info.field_new_name in same_field_name_dict:
            same_field_name_dict[field_info.field_new_name].append(field_info.field_name)
        else:
            same_field_name_dict[field_info.field_new_name] = [field_info.field_name]
    
    field_names_to_remove = set() 
    for new_field_name in same_field_name_dict:
        if len(same_field_name_dict[new_field_name]) < 2:
            field_names_to_remove.add(new_field_name)
    for field_name in field_names_to_remove:
        same_field_name_dict.pop(field_name)
    
    print(colored(f"Overlapping field names: {same_field_name_dict}", "yellow"))
    return same_field_name_dict

def regenerate_field_name(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    field_info_list = ExtractCorrectFieldNamesStates.field_info_list
    same_field_name_dict = fetch_overlapping_field_names(field_info_list)

    if len(same_field_name_dict) == 0:
        return ExtractCorrectFieldNamesStates
    
    fields_to_regenerate = set()

    for new_field_name in same_field_name_dict:
        for i in same_field_name_dict[new_field_name]:
            fields_to_regenerate.add(i)
    
    for field_info in field_info_list:
        if field_info.field_name in fields_to_regenerate:
            if ExtractCorrectFieldNamesStates.retriever is None:
                ExtractCorrectFieldNamesStates.retriever = get_retriver_tool(ExtractCorrectFieldNamesStates.user_id, ExtractCorrectFieldNamesStates.user_session_id, ExtractCorrectFieldNamesStates.data_info_from_user)
            dump = ExtractCorrectFieldNamesStates.retriever.invoke(f"dump {field_info.field_name}", kwargs={"k": 1})

            num_tokens = num_tokens_from_string(str({
                "dump": dump,
                "data_info_from_user": ExtractCorrectFieldNamesStates.data_info_from_user,
                "meaning_of_elements_in_data": ExtractCorrectFieldNamesStates.meaning_of_elements_in_data,
                "field_name": field_info.field_name,
                "field_data_type": field_info.field_type,
                "field_values": field_info.field_values,
                "elements_where_field_is_present": field_info.elements_where_field_present
            }))
            print(colored(f"Number of tokens: {num_tokens}", "yellow"))
            
            field_definition_generator_result = field_name_regenerator.invoke(
                {
                    "dump": dump,
                    "data_info_from_user": ExtractCorrectFieldNamesStates.data_info_from_user,
                    "meaning_of_elements_in_data": ExtractCorrectFieldNamesStates.meaning_of_elements_in_data,
                    "field_name": field_info.field_new_name,
                    "field_data_type": field_info.field_type,
                    "field_values": field_info.field_values,
                    "elements_where_field_is_present": field_info.elements_where_field_present,
                    "previous_names" : [field_info.field_name],
                    "previous_descriptions" : field_info.field_description
                }
            )
            if isinstance(field_definition_generator_result, FieldRenameInfo):
                field_info.field_description = field_definition_generator_result.field_description
                field_info.field_new_name = field_definition_generator_result.field_new_name
            else:
                print(colored("Field description generation failed", "red"))
                print(colored(f"Output: {field_definition_generator_result}", "red"))
            print(colored(f"New name generated : {field_info.field_new_name}", "green"))
            print(colored(f"Description generated : {field_info.field_description}", "green"))
    ExtractCorrectFieldNamesStates.field_info_list = field_info_list

    return ExtractCorrectFieldNamesStates
 
def should_regenrate_fields(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates):
    field_info_list = ExtractCorrectFieldNamesStates.field_info_list
    same_field_name_dict = fetch_overlapping_field_names(field_info_list)
    for new_field_name in same_field_name_dict:
        if len(same_field_name_dict[new_field_name]) >= 1:
            return "regenerate_field_name"
    return "continue"

def score_one_field(input_info : FieldInfo, ExtractCorrectFieldNamesStates : ExtractCorrectFieldNamesStates) -> FieldInfo:
    print(colored("Generating scores for fields...", "yellow"))
    field_info = input_info

    if field_info.field_name == 'parent_index_do_not_change': 
        field_info.semantic_score = 5
        field_info.semantic_score_explanation = "This field is a parent index and should not be changed."
        return field_info

    if ExtractCorrectFieldNamesStates.retriever is None:
        ExtractCorrectFieldNamesStates.retriever = get_retriver_tool(ExtractCorrectFieldNamesStates.user_id, ExtractCorrectFieldNamesStates.user_session_id, ExtractCorrectFieldNamesStates.data_info_from_user)
    dump = ExtractCorrectFieldNamesStates.retriever.invoke(f"dump {field_info.field_name}", kwargs={"k": 1})

    num_tokens = num_tokens_from_string(str({
        "dump": dump,
        "data_info_from_user": ExtractCorrectFieldNamesStates.data_info_from_user,
        "meaning_of_elements_in_data": ExtractCorrectFieldNamesStates.meaning_of_elements_in_data,
        "field_name": field_info.field_name,
        "field_data_type": field_info.field_type,
        "field_values": field_info.field_values,
        "elements_where_field_is_present": field_info.elements_where_field_present
    }))
    print(colored(f"Number of tokens: {num_tokens}", "yellow"))
    
    semantic_score_generator_result = semantic_score_generator.invoke(
        {
            "dump": dump,
            "data_info_from_user": ExtractCorrectFieldNamesStates.data_info_from_user,
            "meaning_of_elements_in_data": ExtractCorrectFieldNamesStates.meaning_of_elements_in_data,
            "field_name": field_info.field_name,
            "field_values": field_info.field_values,
            "elements_where_field_is_present": field_info.elements_where_field_present,
            "field_new_name": field_info.field_new_name,
        }
    )
    
    if isinstance(semantic_score_generator_result, SemanticScoreResult):
        field_info.semantic_score = semantic_score_generator_result.clarity_improvement_score
        field_info.semantic_score_explanation = semantic_score_generator_result.justification
        print(colored(f"Score generated : {field_info.semantic_score}", "green"))
        print(colored(f"Explanation generated : {field_info.semantic_score_explanation}", "green"))
        return field_info
    else:
        print(colored("Score generation failed", "red"))
        print(colored(f"Output: {semantic_score_generator_result}", "red"))
        return None

def score_generation(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    print(colored("Generating scores for fields...", "yellow"))
    field_info_list = ExtractCorrectFieldNamesStates.field_info_list
    update_field_info_list = []

    with ThreadPoolExecutor() as executor:
        field_processes = []
        for field_info in field_info_list:
            field_processes.append(executor.submit(score_one_field, field_info, ExtractCorrectFieldNamesStates))
        
        #wait for all processes to finish
        for process in as_completed(field_processes):
            result = process.result()
            if result is not None:
                update_field_info_list.append(result)

    ExtractCorrectFieldNamesStates.field_info_list = update_field_info_list

    return ExtractCorrectFieldNamesStates

def regenerate_low_scored_fields(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    field_info_list = ExtractCorrectFieldNamesStates.field_info_list
    low_scored_fields = []
    for field_info in field_info_list:
        if field_info.semantic_score <= 3:
            low_scored_fields.append(field_info)
    
    def regenerate(field_info : FieldInfo, ExtractCorrectFieldNamesStates) :
        print(colored(f"Regenerating field: {field_info.field_name}", "blue"))
        if ExtractCorrectFieldNamesStates.retriever is None:
            ExtractCorrectFieldNamesStates.retriever = get_retriver_tool(ExtractCorrectFieldNamesStates.user_id, ExtractCorrectFieldNamesStates.user_session_id, ExtractCorrectFieldNamesStates.data_info_from_user)
        dump = ExtractCorrectFieldNamesStates.retriever.invoke(f"dump {field_info.field_name}", kwargs={"k": 1})

        num_tokens = num_tokens_from_string(str({
            "dump": dump,
            "data_info_from_user": ExtractCorrectFieldNamesStates.data_info_from_user,
            "meaning_of_elements_in_data": ExtractCorrectFieldNamesStates.meaning_of_elements_in_data,
            "field_name": field_info.field_name,
            "field_data_type": field_info.field_type,
            "field_values": field_info.field_values,
            "elements_where_field_is_present": field_info.elements_where_field_present
        }))
        print(colored(f"Number of tokens: {num_tokens}", "yellow"))
        
        regenerate_low_semantic_scored_fields_result = regenerate_low_semantic_scored_fields.invoke(
            {
                "dump": dump,
                "field_name": field_info.field_name,
                "field_new_name": field_info.field_new_name,
                "field_values": field_info.field_values,
                "elements_where_field_is_present": field_info.elements_where_field_present,
                "semantic_score": field_info.semantic_score,
                "assessment": field_info.semantic_score_explanation
            }
        )
        
        if isinstance(regenerate_low_semantic_scored_fields_result, SemanticRegenratedName):
            field_info.field_new_name = regenerate_low_semantic_scored_fields_result.field_new_name
            field_info.field_description = regenerate_low_semantic_scored_fields_result.field_description
            print(colored(f"New name generated : {field_info.field_new_name}", "green"))
            print(colored(f"Description generated : {field_info.field_description}", "green"))
            return field_info
        else:
            print(colored("Field regeneration failed", "red"))
            print(colored(f"Output: {regenerate_low_semantic_scored_fields_result}", "red"))
            return None 
    def improve_score(field_info : FieldInfo, ExtractCorrectFieldNamesStates) :
        retires = 0
        while field_info.semantic_score <=3 and retires < 5:
            print(colored(f"Retrying field: {field_info.field_name}. Current score :{field_info.semantic_score}", "blue"))

            field_info = regenerate(field_info, ExtractCorrectFieldNamesStates)
            field_info = score_one_field(field_info, ExtractCorrectFieldNamesStates)
            print(colored(f"New score: {field_info.semantic_score}", "green"))

            retires += 1
        return field_info
    
    with ThreadPoolExecutor() as executor:
        field_processes = []
        for field_info in low_scored_fields:
            field_processes.append(executor.submit(improve_score, field_info, ExtractCorrectFieldNamesStates))
        
        #wait for all processes to finish
        for process in as_completed(field_processes):
            result = process.result()
            if result is not None:
                for i in range(len(field_info_list)):
                    if field_info_list[i].field_name == result.field_name:
                        field_info_list[i] = result

    ExtractCorrectFieldNamesStates.field_info_list = field_info_list
    return ExtractCorrectFieldNamesStates

def process_whole_file_in_batches(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:
    
    temp_dir_path = os.getcwd() + f'/temp/{ExtractCorrectFieldNamesStates.user_id}/{ExtractCorrectFieldNamesStates.user_session_id}'

    try:
        #open file data file
        print(colored(f"Opening file: {ExtractCorrectFieldNamesStates.file_name}", 'blue'))
        with open(f'{temp_dir_path}/{ExtractCorrectFieldNamesStates.file_name}', 'r') as f:
            whole_data = json.load(f)
            print(colored("File data loaded successfully", "green"))
    except FileNotFoundError:
        print(colored("File not found. Re-flatten process initiated.", 'red'))
        return None
    except json.JSONDecodeError:
        print(colored("Error decoding JSON from file.", 'red'))
        return None
    
    field_name_mapping = {}

    for field_info in ExtractCorrectFieldNamesStates.field_info_list:
        field_name_mapping[field_info.field_name] = field_info.field_new_name
    
    batch_size = 1000
    batch_index = 0

    while batch_index < len(whole_data):
        batch = []
        for i in range(batch_index, min(batch_index + batch_size, len(whole_data))):
            element = whole_data[i]
            batch_element = {}
            for key in element.keys():
                if key in field_name_mapping:
                    batch_element[field_name_mapping[key]] = element[key]
            batch.append(batch_element)
        batch_index += min(batch_index + batch_size, len(whole_data))

        with open(f'{temp_dir_path}/temp_{batch_index}.json', 'w') as f:
            json.dump(batch, f, indent=4)
            print(colored(f"Batch {batch_index} saved successfully", "green"))
    
    return ExtractCorrectFieldNamesStates
                    
def rejoin_batches(ExtractCorrectFieldNamesStates: ExtractCorrectFieldNamesStates) -> ExtractCorrectFieldNamesStates:   
    temp_dir_path = os.getcwd() + f'/temp/{ExtractCorrectFieldNamesStates.user_id}/{ExtractCorrectFieldNamesStates.user_session_id}'
    print(colored(f"Rejoining batches in: {temp_dir_path}", "blue"))

    data = []

    for file in os.listdir(temp_dir_path):
        if file.startswith("temp_"):
            with open(f'{temp_dir_path}/{file}', 'r') as f:
                temp_data = json.load(f)
                data.extend(temp_data)
                print(colored(f"Joined file: {file}", "yellow"))

    with open(f'{temp_dir_path}/out.json', 'w') as f:
        json.dump(data, f, indent=4)
        print(colored("Batches rejoined successfully", "green"))
    
    #delete all temp files
    for file in os.listdir(temp_dir_path):
        if file.startswith("temp_"):
            os.remove(f'{temp_dir_path}/{file}')
            print(colored(f"Deleted file: {file}", "yellow"))

    return ExtractCorrectFieldNamesStates
