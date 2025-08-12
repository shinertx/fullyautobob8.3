import yaml, time, pandas as pd, ccxt
from pathlib import Path
from loguru import logger

def load_config(path):
    with open(path, "r") as f: 
        return yaml.safe_load(f)

def get_exchange(exchange_id):
    try:
        return getattr(ccxt, exchange_id)()
    except Exception as e:
        logger.error(f"Failed to init {exchange_id}: {e}")
        return None

def harvest(cfg, symbol_map):
    logger.info("Starting Data Lakehouse harvester...")
    lake_path = Path("./data")
    tf = cfg['harvester_universe']['timeframe']
    days = cfg['harvester_universe']['initial_harvest_days']
    preferred = cfg['execution'].get('primary_exchange', cfg['data_source']['exchanges'][0])
    ex = get_exchange(preferred)
    tf_ms = ex.parse_timeframe(tf) * 1000

    for symbol in cfg['harvester_universe']['symbols']:
        ex_symbol = symbol_map.get(symbol, {}).get(preferred)
        if not ex_symbol:
            logger.warning(f"No mapping for {symbol} on {preferred}")
            continue
        logger.info(f"Harvesting {symbol} ({ex_symbol}) on {preferred}...")
        since = ex.milliseconds() - 86400000 * days
        last = None
        all_ = []
        try:
            while since < ex.milliseconds():
                ohlcv = ex.fetch_ohlcv(ex_symbol, tf, since, limit=1000)
                if not ohlcv:
                    break
                if last is not None and ohlcv[-1][0] <= last:
                    break
                last = ohlcv[-1][0]
                all_.extend(ohlcv)
                since = last + tf_ms
                time.sleep(ex.rateLimit / 1000)
        except Exception as e:
            logger.error(f"Fetch failed for {symbol}: {e}")
            continue

        if not all_:
            logger.warning(f"No data for {symbol}")
            continue

        df = pd.DataFrame(all_, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.drop_duplicates(subset=['timestamp']).set_index('timestamp').sort_index()
        outdir = lake_path / tf
        outdir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(outdir / f"{symbol}.parquet")
        logger.success(f"Saved {len(df)} rows for {symbol} to Lakehouse.")

if __name__ == "__main__":
    cfg = load_config("configs/config.yaml")
    symbols = load_config("configs/symbols.yaml")
    harvest(cfg, symbols)
