from loguru import logger
import time

class RiskManager:
    def __init__(self, state, cfg):
        self.state, self.cfg = state, cfg['risk']
        self._ensure_day_anchor()

    def _ensure_day_anchor(self):
        ref = self.state.get('risk:day_anchor')
        now = int(time.time())
        if not ref or now - ref.get('ts',0) > 86400:
            eq = self.state.get_portfolio().get('equity', 200.0)
            self.state.set('risk:day_anchor', {'ts': now, 'equity': eq})
            self.state.set('risk:halted', False)

    def enforce(self, symbol_weights: dict, equity: float) -> dict:
        self._ensure_day_anchor()
        start_equity = self.state.get('risk:initial_equity') or equity
        if not self.state.get('risk:initial_equity'):
            self.state.set('risk:initial_equity', start_equity)
        if equity < start_equity * (1.0 - self.cfg['equity_floor_pct']):
            self.state.set('risk:halted', True)
            logger.error("Equity floor breached. Halting trading.")
            return {}

        day_anchor = self.state.get('risk:day_anchor') or {'equity': equity}
        dd = (equity - day_anchor['equity']) / max(1e-9, day_anchor['equity'])
        if dd <= -self.cfg['daily_stop_pct']:
            self.state.set('risk:halted', True)
            logger.warning(f"Daily stop hit ({dd:.2%}). Halting trading.")
            return {}

        if self.state.get('risk:halted'):
            logger.warning("Risk halted. Skipping new exposure.")
            return {}

        capped = {}
        total = 0.0
        for sym, w in symbol_weights.items():
            w = max(0.0, min(float(w), self.cfg['max_symbol_weight']))
            capped[sym] = w
            total += w
        if total > self.cfg['max_gross_weight'] and total > 0:
            scale = self.cfg['max_gross_weight'] / total
            capped = {k: v*scale for k,v in capped.items()}
        return capped
