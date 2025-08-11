from __future__ import annotations
import pandas as pd
import numpy as np

def label_regime(df: pd.DataFrame, vol_window=30, trend_window=30) -> str:
    if df.empty or len(df) < max(vol_window, trend_window):
        return "unknown"
    close = df['close']
    returns = close.pct_change()
    vol = returns.rolling(vol_window).std().iloc[-1]
    vol_q75 = returns.rolling(len(df) // 2).std().quantile(0.75)
    if vol > vol_q75:
        return "high_vol"
    trend = np.polyfit(range(trend_window), close.tail(trend_window).values, 1)[0]
    normalized_trend = trend / close.iloc[-trend_window]
    if normalized_trend > 0.0005:
        return "trend_up"
    if normalized_trend < -0.0005:
        return "trend_down"
    return "chop"
