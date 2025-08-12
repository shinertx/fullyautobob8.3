from __future__ import annotations
import ccxt, pandas as pd
from typing import Optional, Dict
from loguru import logger

def get_exchange(exchange_id: str, api_keys: Optional[Dict[str, str]] = None) -> ccxt.Exchange:
    try:
        exchange_class = getattr(ccxt, exchange_id)
        params = {'options': {'defaultType': 'spot'}}
        if api_keys:
            params.update(api_keys)
        return exchange_class(params)
    except Exception as e:
        logger.error(f"Failed to initialize exchange {exchange_id}: {e}")
        raise

def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str, timeframe: str = "15m", limit: int = 500) -> Optional[pd.DataFrame]:
    if not exchange.has['fetchOHLCV']: return None
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not ohlcv: return None
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df.set_index("timestamp")
    except Exception as e:
        logger.error(f"Failed to fetch OHLCV for {symbol} on {exchange.id}: {e}")
        return None
