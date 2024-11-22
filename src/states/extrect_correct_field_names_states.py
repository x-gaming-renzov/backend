from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class FieldInfo(BaseModel):
    field_name : str
    field_type : str
    field_description : str = None
    field_values : List[Any]
    elements_where_field_present : List[Any]

class ExtractCorrectFieldNamesStates(BaseModel):
    file_name : str
    user_id : str
    user_session_id : str
    data_info_from_user : str
    meaning_of_elements_in_data : Optional[str] = None
    first_few_elements : List[Any] = []
    field_info_list : List[FieldInfo] = []
    messages : Sequence[BaseMessage] = []