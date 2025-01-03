from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FieldInfo(BaseModel):
    field_name: str = Field(..., description="Name of the field")
    field_type: str = Field(..., description="Type of the field")
    field_description: str = Field(..., description="Description of the field")

class JsonObjectInfo(BaseModel):
    json_object_context: str = Field(..., description="Meaning of the JSON object") 
    fields: List[FieldInfo] = Field(..., description="Fields in the JSON object")

class ExtractJsonState(BaseModel):
    json_object_info: Optional[JsonObjectInfo] = Field(None, description="Information about the JSON object")
    task_info: str = Field(..., description="Information about the task")
    user_id: str = Field(..., description="User ID")
    chunk_context: str = Field(..., description="Meaning of the chunk")
    cache_path: str = Field(..., description="Path to cache the data")

class ExtractJsonResponse(BaseModel):
    json_objects: List[Any] = Field(description="List of JSON objects for the task given fields.")