import json, time
from pathlib import Path
from typing import List

class ScreenerStore:
    def __init__(self, snapshot_dir: str = "data/screener_snapshots"):
        self.dir = Path(snapshot_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
    def save(self, universe: List[str]):
        ts = int(time.time())
        fp = self.dir / f"{ts}.json"
        fp.write_text(json.dumps({"ts": ts, "universe": universe}))
        return ts, str(fp)
    def load_all(self):
        items = []
        for p in sorted(self.dir.glob("*.json")):
            try:
                items.append(json.loads(p.read_text()))
            except Exception:
                pass
        return items
