from __future__ import annotations
from typing import Dict, Any, Tuple

class Policy:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg["risk"]
        self.exec_cfg = cfg["execution"]

    def can_place_order(self, portfolio_ctx: Dict[str, Any], order_ctx: Dict[str, Any]) -> Tuple[bool, str]:
        if portfolio_ctx.get("portfolio_drawdown", 0.0) >= self.cfg["portfolio_dd_limit"]:
            return False, "PORTFOLIO_DD_LIMIT"
        if portfolio_ctx.get("daily_drawdown", 0.0) >= self.cfg["daily_dd_limit"]:
            return False, "DAILY_DD_LIMIT"
        if portfolio_ctx.get("cash_fraction", 1.0) < self.cfg["reserve_fraction"]:
            return False, "RESERVE_FRACTION_LOW"
        if order_ctx.get("estimated_slippage_bps", 0.0) > self.exec_cfg["max_allowed_slippage_bps"]:
            return False, "EXECUTION_SLIPPAGE_BREAKER"
        return True, "OK"
