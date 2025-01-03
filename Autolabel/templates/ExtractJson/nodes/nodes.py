from ..prompts.prompts import *
from ..states.states import *
from ..utils.large_file_ops import *

import os, pathlib, json, dotenv
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_openai import ChatOpenAI

from ....utils.helpers import num_tokens_from_string

dotenv.load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), streaming=True)

# nodes using llm
def generate_field_info(ExtractJsonState : ExtractJsonState) -> ExtractJsonState:
    print(colored("Generating field info", "blue"))
    generator_model = model.with_structured_output(JsonObjectInfo)
    generator = generate_field_description_prompt | generator_model

    response = generator.invoke({
        "topic": ExtractJsonState.task_info,
        "chunk_context": ExtractJsonState.chunk_context
    })

    print(colored("Response generated", "green"))
    if isinstance(response, JsonObjectInfo):
        ExtractJsonState.json_object_info = response
        print(ExtractJsonState.json_object_info.model_dump())

    return ExtractJsonState

def generate_json_data(ExtractJsonState : ExtractJsonState) -> ExtractJsonState:
    print(colored("Generating json data", "blue"))
    

    #creat directory {os.getcwd()}/{ExtractJsonState.cache_path}/chunks
    os.makedirs(f"{ExtractJsonState.cache_path}/chunks", exist_ok=True)
    #creat directory {os.getcwd()}/{ExtractJsonState.cache_path}/json_data
    os.makedirs(f"{ExtractJsonState.cache_path}/json_data", exist_ok=True)

    #create chunks
    num_chunks = create_chunks(f"{ExtractJsonState.cache_path}/data.txt", ExtractJsonState.cache_path)
    print(colored(f"Created {num_chunks} chunks", "green"))

    def generate_json_objects(task_info, chunk_context, fields, data_dump, json_object_context, chunk_id) -> List[Dict]:
        generator_model = model.with_structured_output(ExtractJsonResponse)
        generator = generate_json_objects_prompt | generator_model
        print(colored(f"Processing chunk {chunk_id}", "green"))
        print({
            "task_info": task_info,
            "chunk_context": chunk_context,
            "fields": [str(field.model_dump()) for field in fields],
            "data_dump": data_dump,
            "json_object_context": json_object_context
        })
        response = generator.invoke({
            "task_info": task_info,
            "chunk_context": chunk_context,
            "fields": fields,
            "data_dump": data_dump,
            "json_object_context": json_object_context
        })
        print(colored(f"Chunk {chunk_id} processed", "green"))
        print(response)
        if isinstance(response, ExtractJsonResponse):
            print(colored(f"Writing chunk {chunk_id} to file", "green"))
            with open(f"{ExtractJsonState.cache_path}/json_data/{chunk_id}.json", "w") as f:
                json.dump(response.json_objects, f, indent=4)
    
    with ThreadPoolExecutor() as executor:
        futures = []
        
        #process chunk in batches
        batch_size = 10

        for i in range(0, num_chunks, batch_size):
            print(colored(f"Processing chunks {i} to {min(i + batch_size, num_chunks)}", "yellow"))
            for chunk_id in range(i, min(i + batch_size, num_chunks)):
                print(colored(f"Processing chunk {chunk_id}", "yellow"))
                with open(f"{ExtractJsonState.cache_path}/chunks/chunk_{chunk_id}.txt", "r") as f:
                    data_dump = f.read()
                futures.append(executor.submit(generate_json_objects, ExtractJsonState.task_info, ExtractJsonState.chunk_context, ExtractJsonState.json_object_info.fields, data_dump, ExtractJsonState.json_object_info.json_object_context, chunk_id))

        for future in as_completed(futures):
            future.result()

    return ExtractJsonState

def rejoine_json_batches(EtractJsonState : ExtractJsonState) -> ExtractJsonState:
    json_data = []
    for file in os.listdir(f"{EtractJsonState.cache_path}/json_data"):
        with open(f"{EtractJsonState.cache_path}/json_data/{file}", "r") as f:
            json_data.extend(json.load(f))
    
    with open(f"{EtractJsonState.cache_path}/final_json_data.json", "w") as f:
        json.dump(json_data, f, indent=4)
    
    return EtractJsonState