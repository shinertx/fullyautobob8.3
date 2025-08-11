from __future__ import annotations
import math, random
from typing import Dict, Any, List

class BanditAllocator:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.scores: Dict[str, Dict[str, float]] = {}
        self.pulls: Dict[str, Dict[str, int]] = {}

    def update_score(self, strategy_id: str, regime: str, reward: float):
        self.scores.setdefault(regime, {})
        self.pulls.setdefault(regime, {})
        current_score = self.scores[regime].get(strategy_id, 0.0)
        n_pulls = self.pulls[regime].get(strategy_id, 0)
        self.scores[regime][strategy_id] = (current_score * n_pulls + reward) / (n_pulls + 1)
        self.pulls[regime][strategy_id] = n_pulls + 1

    def get_weights(self, edges: List[Dict[str, Any]], regime: str) -> Dict[str, float]:
        if not edges or regime not in self.scores:
            return {e['id']: 1.0 / len(edges) if edges else 0 for e in edges}
        total_pulls = sum(self.pulls[regime].values())
        ucb_scores = {}
        for edge in edges:
            edge_id = edge['id']
            if edge_id not in self.scores[regime]:
                ucb_scores[edge_id] = float('inf')
                continue
            avg_reward = self.scores[regime][edge_id]
            n_pulls = self.pulls[regime][edge_id]
            bonus = self.cfg['exploration'] * math.sqrt(math.log(total_pulls + 1) / n_pulls)
            ucb_scores[edge_id] = avg_reward + bonus
        total_ucb = sum(ucb_scores.values())
        if total_ucb == 0 or total_ucb == float('inf'):
            return {e['id']: 1.0 / len(edges) if edges else 0 for e in edges}
        return {k: v / total_ucb for k, v in ucb_scores.items()}
