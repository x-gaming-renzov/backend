from langchain.prompts import PromptTemplate

generate_meaning_of_elements_in_data_prompt = PromptTemplate(
    template="""
I have a very very large (more than 5 gbs) of json data. It contains list of elements. 
Some informaton about data from user is : {data_info_from_user}

Previous Messages : {messages}

#Task : Give a 3-4 line information about what elements in this data mean based on information provided by user.

First few elements in data are :
{first_few_elements}
""",
    input_variables=["data_info_from_user", "first_few_elements", 'messages']
)

generate_field_desc_prompt = PromptTemplate(
    template="""
##Context : 
#Relevant dump from knowledge base :
{dump}

#About the data : 
{data_info_from_user}

#About elements in data :
{meaning_of_elements_in_data}

#Task : 
You are given information about one field in elements of data. You have to generate a new name and description for field in data.

General Guidlines : 
1. Observe what types of elements field is in
2. Observe what values field can take
3. Observe where field is present in elements

Aproach to solve this task :
1. Observe what other field is present in elements along with this field.
2. Observe what values this field can take.
3. Observe where this field is present in elements.
4. Try to understand what this field means in context of element it is present in.
5. Generate a new name and description for this field based on above observations.

Rule for making new name :
1. New name should be descriptive and should reflect meaning of field.
2. Words in new name should be separated by underscore.
4. New name must strictly based on information provided in data. DO NOT ADD ANYTHING FROM OUTSIDE. DO NOT HALLUCINATE.

Rules for making description :
1. Description MUST BE IN 2 LINER. No more than 2 lines.
2. Description should be based meaning of this field with respect to element it is present in.
3. Use concrete and precise language.
4. Description must strictly based on information provided in data. DO NOT ADD ANYTHING FROM OUTSIDE. DO NOT HALLUCINATE.

#Field Information :
Field Name : {field_name}
Field Data Type : {field_data_type}
Field Values : {field_values}

Elements where field is present :
{elements_where_field_is_present}

""",
    input_variables=["dump", "data_info_from_user", "meaning_of_elements_in_data", "field_name", "field_data_type", "field_values", "elements_where_field_is_present"]
)

regenerate_field_desc_prompt = PromptTemplate(
    template="""
##Context : 
#Relevant dump from knowledge base :
{dump}

#About the data : 
{data_info_from_user}

#About elements in data :
{meaning_of_elements_in_data}

#Task : 
You are given information about one field and some names suited to rename this field in elements of data. You have to generate a new name and description for field in data.

General Guidlines : 
1. Observe what types of elements field is in
2. Observe what values field can take
3. Observe where field is present in elements

Aproach to solve this task :
1. Observe what other field is present in elements along with this field.
2. Observe what values this field can take.
3. Observe where this field is present in elements.
4. Try to understand what this field means in context of element it is present in.
5. Generate a new name and description for this field based on above observations.

Rule for making new name :
1. New name should be descriptive and should reflect meaning of field.
2. Words in new name should be separated by underscore.
4. New name must strictly based on information provided in data. DO NOT ADD ANYTHING FROM OUTSIDE. DO NOT HALLUCINATE.

Rules for making description :
1. Description MUST BE IN 2 LINER. No more than 2 lines.
2. Description should be based meaning of this field with respect to element it is present in.
3. Use concrete and precise language.
4. Description must strictly based on information provided in data. DO NOT ADD ANYTHING FROM OUTSIDE. DO NOT HALLUCINATE.

#Field Information :
Field Name : {field_name}
Field Data Type : {field_data_type}
Field Values : {field_values}
Previous Names : {previous_names}
Previous Descriptions : {previous_descriptions}
Reason for regenerating : Clashin with other field names. Needs more descriptive name.

Elements where field is present :
{elements_where_field_is_present}

""",
    input_variables=["dump", "data_info_from_user", "meaning_of_elements_in_data", "field_name", "field_data_type", "field_values", "elements_where_field_is_present"]
)