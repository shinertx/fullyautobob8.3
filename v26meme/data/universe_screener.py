from typing import List, Dict
from loguru import logger
import ccxt

COMMON = {'XBT': 'BTC', 'BCC': 'BCH'}

def to_canonical(symbol: str) -> str:
    base, quote = symbol.split('/')
    base = COMMON.get(base, base)
    quote = COMMON.get(quote, quote)
    if quote == 'USDT': quote = 'USD'
    return f"{base}_{quote}_SPOT"

def volume_usd(t: Dict) -> float:
    qv = t.get('quoteVolume')
    try:
        if qv not in (None, 0, '0'): return float(qv)
    except Exception:
        pass
    bv, last = t.get('baseVolume'), (t.get('last') or t.get('close') or 0)
    try:
        return float(bv) * float(last) if (bv and last) else 0.0
    except Exception:
        return 0.0

class UniverseScreener:
    def __init__(self, exchanges: List[str], screener_cfg: dict):
        self.exchanges = {ex: getattr(ccxt, ex)() for ex in exchanges}
        self.cfg = screener_cfg

    def get_active_universe(self) -> List[str]:
        tickers = []
        for name, ex in self.exchanges.items():
            try:
                t = ex.fetch_tickers()
                tickers.extend(t.values())
            except Exception as e:
                logger.error(f"fetch_tickers failed on {name}: {e}")

        if not tickers:
            logger.error("No tickers fetched; screener empty.")
            return []

        best: Dict[str, float] = {}
        for t in tickers:
            sym = t.get('symbol')
            if not sym or (not sym.endswith('/USD') and not sym.endswith('/USDT')): 
                continue
            vol = volume_usd(t)
            price = t.get('last') or t.get('close') or 0
            if vol > self.cfg['min_24h_volume_usd'] and price > self.cfg['min_price']:
                canon = to_canonical(sym)
                best[canon] = max(vol, best.get(canon, 0.0))

        if not best:
            logger.warning("Screener filters removed all tickers.")
            return []

        selected = sorted(best.items(), key=lambda kv: kv[1], reverse=True)[: self.cfg['max_symbols']]
        universe = [k for k, _ in selected]
        logger.success(f"Screener selected {len(universe)} symbols: {universe}")
        return universe
