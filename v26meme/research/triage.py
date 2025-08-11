from __future__ import annotations
from typing import Dict, Any

def calculate_fitness(sim_stats: Dict[str, Any]) -> float:
    if not sim_stats or sim_stats.get("n_trades", 0) < 10: return 0.0
    sortino = sim_stats.get("sortino", 0.0)
    mdd = sim_stats.get("mdd", 1.0)
    drawdown_penalty = max(0, (mdd - 0.2) * 5)
    fitness = sortino * (1 - drawdown_penalty)
    return max(0.0, fitness)
