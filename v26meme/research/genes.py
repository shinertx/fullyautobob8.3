from __future__ import annotations
import pandas as pd
from typing import Dict, Any

def entry_rsi_oversold(df: pd.DataFrame, period: int = 14, level: int = 30) -> pd.Series:
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi < level

def entry_bollinger_breakout(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.Series:
    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    return df['close'] > upper_band

def exit_take_profit(df: pd.DataFrame, entry_price: float, profit_pct: float = 5.0) -> bool:
    return df['close'].iloc[-1] >= entry_price * (1 + profit_pct / 100)

def exit_stop_loss(df: pd.DataFrame, entry_price: float, loss_pct: float = 2.0) -> bool:
    return df['close'].iloc[-1] <= entry_price * (1 - loss_pct / 100)

def filter_high_volume(df: pd.DataFrame, lookback: int = 30) -> bool:
    if len(df) < lookback: return False
    return df['volume'].iloc[-1] > df['volume'].rolling(window=lookback).mean().iloc[-1]

GENE_POOL: Dict[str, Dict[str, Any]] = {
    "entry_rsi_oversold": {"callable": entry_rsi_oversold, "category": "entry", "params": {"period": [7, 14, 21], "level": [20, 25, 30]}, "theme": "mean_reversion"},
    "entry_bollinger_breakout": {"callable": entry_bollinger_breakout, "category": "entry", "params": {"period": [20], "std_dev": [2.0, 2.5]}, "theme": "momentum"},
    "exit_take_profit": {"callable": exit_take_profit, "category": "exit_tp", "params": {"profit_pct": [3.0, 5.0, 8.0]}},
    "exit_stop_loss": {"callable": exit_stop_loss, "category": "exit_sl", "params": {"loss_pct": [1.5, 2.0, 3.0]}},
    "filter_high_volume": {"callable": filter_high_volume, "category": "filter", "params": {"lookback": [30, 60]}}
}
