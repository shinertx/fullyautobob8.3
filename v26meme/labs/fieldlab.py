from __future__ import annotations
import os, json
from typing import Dict, Any
from loguru import logger

class FieldLab:
    def __init__(self, state_dir: str):
        self.priors_path = os.path.join(state_dir, "field_priors.json")
        self.priors = self._load_priors()

    def _load_priors(self) -> Dict[str, Any]:
        if os.path.exists(self.priors_path):
            try:
                with open(self.priors_path, "r") as f: return json.load(f)
            except Exception as e: logger.error(f"Could not load field priors: {e}")
        return {"slippage_bps": {"all": 15.0}, "fill_rate_pct": {"all": 80.0}, "fees_bps": {"all": 10.0}}

    def _save_priors(self):
        try:
            with open(self.priors_path, "w") as f: json.dump(self.priors, f, indent=2)
        except IOError as e: logger.error(f"Could not save field priors: {e}")

    def get_priors(self, symbol: str) -> Dict[str, float]:
        return {k: self.priors[k].get(symbol, self.priors[k]["all"]) for k in self.priors}

    def update_from_trade(self, symbol: str, observed_slippage_bps: float, fill_rate_pct: float):
        alpha = 0.1
        for key, val in [("slippage_bps", observed_slippage_bps), ("fill_rate_pct", fill_rate_pct)]:
            current = self.get_priors(symbol)[key]
            self.priors[key][symbol] = (1 - alpha) * current + alpha * val
        logger.info(f"FieldLab updated for {symbol}: {self.priors}")
        self._save_priors()
