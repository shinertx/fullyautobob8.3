import pandas as pd
from typing import List, Dict
from v26meme.research.feature_factory import FeatureFactory
from v26meme.research.sentiment_features import from_events_to_series, base_from_canonical
from v26meme.labs.simlab import SimLab, _evaluate_formula
from v26meme.data.lakehouse import Lakehouse

def dynamic_universe_oos(lakehouse: Lakehouse, timeframe: str, snapshots: List[dict],
                         formula: list, features: List[str], horizon_bars: int = 8,
                         feed_scores: Dict[str, List[dict]] | None = None):
    ff = FeatureFactory()
    sim = SimLab(18, 5)
    returns = []

    for snap in snapshots:
        ts = pd.to_datetime(snap['ts'], unit='s')
        for canon in snap.get('universe', []):
            df = lakehouse.get_data(canon, timeframe)
            if df.empty or df.index.max() <= ts: 
                continue
            df_feat = ff.create(df.copy())
            if feed_scores is not None:
                coin = base_from_canonical(canon)
                s = from_events_to_series(df_feat.index, feed_scores.get(coin, []))
                df_feat['sentiment_ewm'] = s
                if 'sentiment_ewm' not in features:
                    features = features + ['sentiment_ewm']
            for f in features:
                mu = df_feat[f].rolling(200, min_periods=50).mean().shift(1)
                sd = df_feat[f].rolling(200, min_periods=50).std().shift(1)
                df_feat[f] = (df_feat[f] - mu) / sd
            df_feat = df_feat.dropna()
            if df_feat.empty:
                continue
            # align to last known bar before snapshot
            try:
                t0 = df_feat.index[df_feat.index.get_indexer([ts], method='pad')][0]
            except Exception:
                continue
            start_idx = df_feat.index.get_loc(t0)
            end_idx = min(start_idx + horizon_bars, len(df_feat)-1)
            if end_idx <= start_idx:
                continue
            window = df_feat.iloc[start_idx:end_idx+1].copy()
            if not _evaluate_formula(window.iloc[0], formula):
                continue
            entry = float(window['close'].iloc[1]) * (1 + sim.slippage) if len(window) > 1 else float(window['close'].iloc[0])
            exit_ = float(window['close'].iloc[-1]) * (1 - sim.slippage)
            ret = ((exit_ - entry) / entry) - (2 * sim.fee)
            returns.append(ret)

    ser = pd.Series(returns, dtype=float)
    if ser.empty:
        return {"n_trades": 0, "win_rate": 0.0, "avg_return": 0.0, "sharpe": 0.0, "sortino": 0.0, "mdd": 0.0}

    eq = (1+ser).cumprod()
    dd = (eq - eq.cummax()) / eq.cummax()
    down_std = ser[ser < 0].std()
    return {
        "n_trades": int(ser.shape[0]),
        "win_rate": float((ser > 0).mean()),
        "avg_return": float(ser.mean()),
        "sharpe": float(ser.mean() / ser.std()) if ser.std() else 0.0,
        "sortino": float(ser.mean() / down_std) if down_std else 0.0,
        "mdd": float(dd.min())
    }
