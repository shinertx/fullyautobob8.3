from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Gene(BaseModel):
    name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    category: str

class StrategyCard(BaseModel):
    id: str = Field(..., description="Unique identifier for this strategy, e.g., a hash of its genes.")
    name: str
    theme: str
    genes: List[Gene]
    class Config:
        frozen = True

class EdgeCard(BaseModel):
    strategy_card: StrategyCard
    phase: str = Field(default="0_incubation")
    is_active: bool = Field(default=True)
    sim_performance: Dict[str, Any] = Field(default_factory=dict)
    live_performance: Dict[str, Any] = Field(default_factory=dict)
    live_trade_count: int = 0
    live_pnl_usd: float = 0.0
    lineage: List[str] = Field(default_factory=list)
    def get_id(self) -> str:
        return self.strategy_card.id
