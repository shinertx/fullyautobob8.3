from __future__ import annotations
import pandas as pd, numpy as np
from typing import Dict, Any, Tuple
from v26meme.core.dsl import StrategyCard
from v26meme.research.genes import GENE_POOL

def run_backtest(df: pd.DataFrame, card: StrategyCard, fees_bps: int, slippage_bps: int) -> Dict[str, Any]:
    if df.empty: return {"error": "DataFrame is empty"}
    entry_gene = next(g for g in card.genes if g.category == 'entry')
    tp_gene = next(g for g in card.genes if g.category == 'exit_tp')
    sl_gene = next(g for g in card.genes if g.category == 'exit_sl')
    signals = GENE_POOL[entry_gene.name]['callable'](df, **entry_gene.params)
    returns, in_trade, entry_price = [], False, 0.0
    fee, slippage = (fees_bps / 10000.0), (slippage_bps / 10000.0)
    for i in range(len(df)):
        if not in_trade and signals.iloc[i]:
            in_trade, entry_price = True, df['close'].iloc[i] * (1 + slippage)
        if in_trade:
            price = df['close'].iloc[i]
            if price >= entry_price * (1 + tp_gene.params['profit_pct'] / 100) or \
               price <= entry_price * (1 - sl_gene.params['loss_pct'] / 100):
                exit_price = price * (1 - slippage)
                returns.append((exit_price - entry_price) / entry_price - (2 * fee))
                in_trade = False
    if not returns: return {"n_trades": 0}
    rs = pd.Series(returns)
    eq = (1 + rs).cumprod()
    dd = (eq - eq.cummax()) / eq.cummax()
    down_std = rs[rs < 0].std()
    sortino = rs.mean() / down_std if down_std > 0 else 0.0
    means = [rs.sample(frac=1.0, replace=True).mean() for _ in range(1000)]
    return {
        "n_trades": len(rs), "win_rate": (rs > 0).mean(), "avg_return": rs.mean(),
        "sortino": sortino * np.sqrt(252) if not np.isnan(sortino) else 0, "mdd": dd.min(),
        "expectancy": rs.mean(), "ci_lower_bound": np.percentile(means, 2.5), "ci_upper_bound": np.percentile(means, 97.5)
    }
