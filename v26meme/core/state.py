import json, time
import redis
from loguru import logger

class StateManager:
    def __init__(self, host='localhost', port=6379):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)
        try:
            self.r.ping()
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            raise

    def set(self, key, value): self.r.set(key, json.dumps(value))
    def get(self, key):
        val = self.r.get(key)
        return json.loads(val) if val else None

    def get_portfolio(self):
        return self.get('portfolio') or {'cash': 200.0, 'equity': 200.0, 'positions': {}}
    def set_portfolio(self, portfolio): self.set('portfolio', portfolio)

    def log_historical_equity(self, equity: float):
        ts = int(time.time())
        self.r.zadd('equity_curve', {json.dumps({'ts': ts, 'equity': equity}): ts})

    def get_equity_curve(self):
        return [json.loads(v) for v in self.r.zrange('equity_curve', 0, -1)]

    def get_active_alphas(self): return self.get('active_alphas') or []
    def set_active_alphas(self, alphas): self.set('active_alphas', alphas)

    def record_alpha_pnl(self, alpha_id: str, pnl: float):
        self.r.hincrbyfloat('alpha_pnl', alpha_id, pnl)
    def get_all_alpha_pnl(self):
        pnl = self.r.hgetall('alpha_pnl')
        return {k: float(v) for k, v in pnl.items()}
