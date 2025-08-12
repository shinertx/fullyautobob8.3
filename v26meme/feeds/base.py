from abc import ABC, abstractmethod
from typing import Dict, List

class Feed(ABC):
    @abstractmethod
    def scores_by_ticker(self, tickers: List[str]) -> Dict[str, List[dict]]:
        ...
