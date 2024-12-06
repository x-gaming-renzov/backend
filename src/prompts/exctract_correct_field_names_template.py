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
3. be as descriptive as possible without being too long.
4. New name must strictly based on information provided in data. DO NOT ADD ANYTHING FROM OUTSIDE. DO NOT HALLUCINATE.
5. Give special attention to the values field can take and if field name has any number in it, try to reflect that in new name.
6. IF FIELD NAME IS parent_index_do_not_change, new name should be parent_index_do_not_change.

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
5. IF FIELD NAME IS parent_index_do_not_change, new name should be parent_index_do_not_change.

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

generate_score_for_new_fields = PromptTemplate(
    template = """You are to assess the semantic clarity improvement of a field name in a dataset.
Here is the knowledge base to consider:
{dump}

#About the data : 
{data_info_from_user}

#About elements in data :
{meaning_of_elements_in_data}

Field information:
- Old field name: {field_name}
- New field name: {field_new_name}
- Sample values: {field_values}
- Elements where field is present: {elements_where_field_is_present}

Question:
On a scale from -5 to +5, how much does the new field name improve semantic clarity over the old field name?
- -5 means the new field name is much less clear than the old one
- 0 means no change in clarity
- +5 means the new field name is much clearer than the old one

Provide your assessment in JSON format with keys:

  "clarity_improvement_score": <your_score_here>,
  "justification": "<brief explanation>"


Provide only the JSON object as your response.""",
    input_variables=["dump", "data_info_from_user", "meaning_of_elements_in_data", "field_name", "field_new_name", "field_values", "elements_where_field_is_present"]
)

regenerate_low_scored_names = PromptTemplate(
    template="""The initial attempt to improve the field name '{field_name}' resulted in '{field_new_name}', which has a clarity improvement score of - {semantic_score}.
Here's the feedback provided by the user:
{assessment}

Your task is to suggest an even better field name that significantly enhances semantic clarity. Use the following information:

Knowledge base:
{dump}

Field information:
- Old field name: {field_name}
- Previous suggested field name: {field_new_name}
- Sample values: {field_values}
- Elements where field is present: {elements_where_field_is_present}

Provide only the JSON object as your response.""",
    input_variables=["dump", "field_name", "field_new_name", "field_values", "elements_where_field_is_present", "semantic_score", "assessment"]
)