import pandas as pd
import numpy as np

class FeatureFactory:
    def create(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return df
        out = df.copy()
        out['return_1p'] = out['close'].pct_change()
        out['volatility_20p'] = out['return_1p'].rolling(20).std() * np.sqrt(20)
        out['momentum_10p'] = out['close'].pct_change(10)
        delta = out['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        out['rsi_14'] = 100 - (100 / (1 + rs))
        out['sma_50'] = out['close'].rolling(50).mean()
        out['close_vs_sma50'] = (out['close'] - out['sma_50']) / out['sma_50']
        return out.dropna()
