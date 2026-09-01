from pydantic import BaseModel
from datetime import datetime



class AgentMemory(BaseModel):

    recommendation_id:str

    resource_id:str

    action:str

    approved:bool

    execution_status:str

    realized_savings:float

    user_feedback:str | None = None

    created_at:datetime

    updated_at:datetime