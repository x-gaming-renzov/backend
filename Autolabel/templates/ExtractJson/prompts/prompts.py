from langchain.prompts import PromptTemplate

generate_field_description_prompt = PromptTemplate(
    template="""
For a data dump, You want to create a json data for : 
{topic}

Context for each chunk of data in data dump :
{chunk_context}

#TASK : 
For better linking between json objects you want to create list of fields that indicates what type of insights and content this object have, you are creating list of fields and description you will use in your labelded json data

Given List of fields and description you want to use in your json data, write a json object with fields and description
Define what type of insights and content this object have. 
""",
input_variables=["topic", "chunk_context"]
)

generate_json_objects_prompt = PromptTemplate(
    template="""
create a json list for task : 
{task_info}
Each json object represents following information :
{json_object_context}

#Context for each chunk of data in data dump :
{chunk_context}

#Fields to be used in json data :
{fields}

RULES : 
1. DO NOT HALLUCIANTE
2. IF YOU ARE NOT GETTING ANY INSIGHT RETURN BLANK LIST
3. IF INFORMATION ABOUT CERTAIN FIELD NOT PRESENT DO NOT INCLUDE THAT FIEDL IN DICT

#Task : 
Given the fields and description you want to use in your json data, return a list of json objects with fields given above.

#DATA DUMP :
{data_dump}
""",
input_variables=["task_info", "chunk_context", "fields", "data_dump", "json_object_context"]
)

