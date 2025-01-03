from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FieldInfo(BaseModel):
    old_name: str = Field('', title="Old Name")
    new_name: str = Field('', title="New Name")
    description: str = Field('', title="Description")
    sample: str = Field('', title="Sample")
    semantic_clarity_score: str = Field('', title="Semantic Clarity Score")
    semantic_justification: str = Field('', title="Semantic Justification")

class GenerateCleanMetadataStates(BaseModel):
    field_info_list: Optional[List[FieldInfo]] = Field([], title="Field Info List")
    cache_path: str = Field(title="Cache Path")
    kb_path: str = Field(title="KB Path")
    data_path: str = Field(title="Data Path")

class FieldDescription(BaseModel):
    description : str = Field(title="Description")
    field_name : str = Field(title="Field Name")

class FieldDescriptionResponse(BaseModel):
    descriptions : List[FieldDescription] = Field(title="Descriptions")
    
class FieldNameResponse(BaseModel):
    new_name: str = Field(title="New Name")

class SemanticClarityScoreResponse(BaseModel):
    clarity_improvement_score: float
    justification: str