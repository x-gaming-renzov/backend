import os, pathlib, json, dotenv
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_openai import ChatOpenAI

from ....memory.XGMemoryClient import XGMemoryClient

from ..states.states import *
from ..prompts.prompts import *
from ..utils.largefileops import *

dotenv.load_dotenv()

print(colored(f"Status: ", "yellow"), colored(f"Initialising nodes", "white")) 

print(colored(f"Status: ", "yellow"), colored(f"Initialising ChatOpenAI", "white"))
model = ChatOpenAI(model="gpt-4o-mini")
print(colored(f"Status: ", "green"), colored(f"ChatOpenAI initialised", "white"))
print(colored(f"Status: ", "yellow"), colored(f"Initialising XGMemoryClient", "white"))
memory = XGMemoryClient(user_name="XG")
print(colored(f"Status: ", "green"), colored(f"XGMemoryClient initialised", "white"))

def pre_process(GenerateCleanMetadataStates : GenerateCleanMetadataStates) -> GenerateCleanMetadataStates:
    print(colored(f"Status: ", "yellow"), colored(f"Pre-processing", "white"))

    if not os.path.exists(GenerateCleanMetadataStates.cache_path):
        os.makedirs(GenerateCleanMetadataStates.cache_path)

    print(colored(f"Status: ", "yellow"), colored(f"extracting keys and examples", "white"))
    key_value_map, field_descriptions = extract_keys_and_examples(GenerateCleanMetadataStates.data_path)
    print(colored(f"Status: ", "green"), colored(f"keys and examples extracted", "white"))

    GenerateCleanMetadataStates.field_info_list = []
    print(colored(f"Status: ", "yellow"), colored(f"adding field info to GenerateCleanMetadataStates", "white"))
    if GenerateCleanMetadataStates.field_info_list is None:
        GenerateCleanMetadataStates.field_info_list = []
    for key, value in key_value_map.items():
        GenerateCleanMetadataStates.field_info_list.append(FieldInfo(old_name=key, 
                                                                     new_name="", 
                                                                     description=field_descriptions[key], 
                                                                     sample=str(value), 
                                                                     semantic_clarity_score='0.0', 
                                                                     semantic_justification=""))
    print(colored(f"Status: ", "green"), colored(f"field info added to GenerateCleanMetadataStates", "white"))

    print(colored(f"Status: ", "yellow"), colored(f"Populating memory with kb", "white"))
    with open(GenerateCleanMetadataStates.kb_path, "r") as f:
        kb = f.read()
    kb += "\n This is a KB about data user wants to clean"
    memory.add_kb_memory(kb)

    return GenerateCleanMetadataStates

def generate_description(GenerateCleanMetadataStates : GenerateCleanMetadataStates) -> GenerateCleanMetadataStates:
    print(colored(f"Status: ", "yellow"), colored(f"Generating description", "white"))

    generator_model = model.with_structured_output(FieldDescription)
    generator = generate_description_prompt | generator_model

    def generate_desc(field_info : FieldInfo):
        response = generator.invoke({"field": field_info.old_name, "basic_description": field_info.description})
        if isinstance(response, FieldDescription):
            field_info.description = response.description
        return field_info
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(generate_desc, field_info) for field_info in GenerateCleanMetadataStates.field_info_list]
        field_info_list = []
        for future in as_completed(futures):
            field_info_list.append(future.result())
        GenerateCleanMetadataStates.field_info_list = field_info_list
    return GenerateCleanMetadataStates

def generate_field_name(GenerateCleanMetadataStates : GenerateCleanMetadataStates) -> GenerateCleanMetadataStates:
    print(colored(f"Status: ", "yellow"), colored(f"Generating field name", "white"))

    generator_model = model.with_structured_output(FieldNameResponse)
    generator = generate_field_names_prompt | generator_model

    def generate_field(field_info : FieldInfo):
        response = generator.invoke({"field_name": field_info.old_name, 
                                     "example": field_info.sample, 
                                     "description": field_info.description, 
                                     "knowledge_base": memory.get_memory(field_info.description, 3)})
        if isinstance(response, FieldNameResponse):
            field_info.new_name = response.new_name
        return field_info
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(generate_field, field_info) for field_info in GenerateCleanMetadataStates.field_info_list]
        field_info_list = []
        for future in as_completed(futures):
            field_info_list.append(future.result())
        GenerateCleanMetadataStates.field_info_list = field_info_list
    return GenerateCleanMetadataStates

def access_semantic_clarity(GenerateCleanMetadataStates : GenerateCleanMetadataStates) -> GenerateCleanMetadataStates:
    print(colored(f"Status: ", "yellow"), colored(f"Accessing semantic clarity", "white"))

    generator_model = model.with_structured_output(SemanticClarityScoreResponse)
    generator = access_semantice_clarity_prompt | generator_model

    def access_semantic(field_info : FieldInfo):
        response = generator.invoke({"old_field": field_info.old_name, 
                                     "new_field": field_info.new_name, 
                                     "examples": field_info.sample, 
                                     "knowledge_base": memory.get_memory(field_info.description, 3)})
        if isinstance(response, SemanticClarityScoreResponse):
            field_info.semantic_clarity_score = str(response.clarity_improvement_score)
            field_info.semantic_justification = response.justification
        return field_info
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(access_semantic, field_info) for field_info in GenerateCleanMetadataStates.field_info_list]
        field_info_list = []
        for future in as_completed(futures):
            field_info_list.append(future.result())
        GenerateCleanMetadataStates.field_info_list = field_info_list
    return GenerateCleanMetadataStates

def regenerate_low_scoring_fields(GenerateCleanMetadataStates : GenerateCleanMetadataStates) -> GenerateCleanMetadataStates:
    print(colored(f"Status: ", "yellow"), colored(f"Regenerating low scoring fields", "white"))

    low_scoring_fields = [field_info for field_info in GenerateCleanMetadataStates.field_info_list if float(field_info.semantic_clarity_score) < 3]
    print(colored(f"Status: ", "yellow"), colored(f"Low scoring fields: {[field_info.new_name for field_info in GenerateCleanMetadataStates.field_info_list]}", "white"))

    generator_model = model.with_structured_output(FieldNameResponse)
    generator = generate_field_names_prompt | generator_model

    def generate_field(field_info : FieldInfo):
        response = generator.invoke({"field_name": field_info.old_name, 
                                     "example": field_info.sample, 
                                     "description": field_info.description, 
                                     "knowledge_base": memory.get_memory(field_info.description, 3)})
        if isinstance(response, FieldNameResponse):
            field_info.new_name = response.new_name
        return field_info
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(generate_field, field_info) for field_info in low_scoring_fields]
        field_info_list = []
        for future in as_completed(futures):
            field_info_list.append(future.result())
        for field_info in field_info_list:
            GenerateCleanMetadataStates.field_info_list.append(field_info)
    
    GenerateCleanMetadataStates = access_semantic_clarity(GenerateCleanMetadataStates)
    return GenerateCleanMetadataStates