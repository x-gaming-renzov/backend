from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GenerateRedditDataState(BaseModel):
    subreddits: List[str] 
    kb_data : str
    cache_path: str
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str
    user_id: Optional[str] = None

class TaskInfo(BaseModel):
    task_info : str

class RelevanceInfo(BaseModel):
    relevance : str
    relevance_score : float
    is_relevant : bool
