from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict

class Alpha(BaseModel):
    id: str
    name: str
    formula: List[Any]
    universe: List[str]
    timeframe: str
    performance: Dict[str, Dict[str, Any]] = {}
    model_config = ConfigDict(frozen=True)
