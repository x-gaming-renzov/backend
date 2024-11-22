from langchain.prompts import PromptTemplate

generate_meaning_of_elements_in_data = PromptTemplate(
    template="""
I have a very very large (more than 5 gbs) of json data. It contains list of elements. 
Some informaton about data from user is : {data_info_from_user}

#Task : Give a 3-4 line information about what elements in this data mean based on information provided by user.

#NOTE : You can also ask Retriver agent to answer some questions if you need more information.

First few elements in data are :
{first_few_elements}
""",
    input_variables=["data_info_from_user", "first_few_elements"]
)