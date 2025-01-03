from langchain.prompts import PromptTemplate

generate_description_prompt = PromptTemplate(
    template="""
        You are to refine and enhance dataset field descriptions based on a given basic description.
        
        Field name: {field}
        Basic description: {basic_description}
        
        Write a concise 1-2 liner description in plain language for what this field represents.
        Provide the output in JSON format:
        {{
            "description": "<your_enhanced_description_here>"
        }}
        """,
        input_variables=["field", "basic_description"])

generate_field_names_prompt = PromptTemplate(
    template="""Given the following field names with example values, 
suggest more meaningful names that enhance clarity significantly. Use the keys,
their sample values, and the knowledge base provided below
to determine what a reasonable name should be. Remember these fields
are critical for building applications using LLMs. If you see
an ambiguous field name, think from first principles about what a good name
for the field would be.
Keep the field names in plain and simple English so that 
they are very easy to understand even for a 10-year-old.
Long field names are acceptable as they are intended to 
derive insights using LLMs.
Here's a knowledge base about the server to keep in 
mind for suggesting better field names: {knowledge_base}

Field names, descriptions and examples:
Field Name : {field_name}
Description : {description}

Provide new name for this field. """,
input_variables=["field_name", "example", "description", "knowledge_base"])

access_semantice_clarity_prompt = PromptTemplate(
    template="""You are to assess the semantic clarity improvement of a field name in a dataset.

Here is the knowledge base to consider:
{knowledge_base}

Field information:
- Old field name: {old_field}
- New field name: {new_field}
- Sample values: {examples}

Question:
On a scale from -5 to +5, how much does the new field name improve semantic clarity over the old field name?
- -5 means the new field name is much less clear than the old one
- 0 means no change in clarity
- +5 means the new field name is much clearer than the old one

Provide your assessment in JSON format:
{{
  "clarity_improvement_score": <your_score_here>,
  "justification": "<brief explanation>"
}}

Provide only the JSON object as your response.""",
input_variables=["old_field", "new_field", "examples", "knowledge_base"])

regenrate_field_name_prompt = PromptTemplate(
    template="""The initial attempt to improve the field name '{old_field}' resulted in '{initial_new_field}', which has a clarity improvement score of {assessment['clarity_improvement_score']}. 

Your task is to suggest an even better field name that significantly enhances semantic clarity. Use the following information:

Knowledge base:
{knowledge_base}

Field information:
- Old field name: {old_field}
- Previous suggested field name: {initial_new_field}
- Sample values: {examples}

Provide your new suggestion in JSON format:
{{
  "new_name": "<your_new_field_name>"
}}

Provide only the JSON object as your response.""",
input_variables=["old_field", "initial_new_field", "assessment", "examples", "knowledge_base"])