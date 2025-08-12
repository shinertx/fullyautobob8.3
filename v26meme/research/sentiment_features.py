import pandas as pd
from typing import List, Dict

def from_events_to_series(df_index: pd.DatetimeIndex, events: List[dict], halflife_bars: int = 24) -> pd.Series:
    if not events:
        return pd.Series(0.0, index=df_index)
    ev = pd.DataFrame(events)
    ev['ts'] = pd.to_datetime(ev['ts'], unit='s')
    ev = ev.set_index('ts').sort_index()
    s = ev['score'].resample(df_index.inferred_freq or '1H').mean().fillna(0.0)
    s = s.reindex(df_index, method='ffill').fillna(0.0)
    return s.ewm(halflife=halflife_bars, adjust=False).mean().shift(1)

def base_from_canonical(canon: str) -> str:
    return canon.split('_')[0]
