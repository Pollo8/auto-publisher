import datetime as dt
import json
import pathlib

import pandas as pd
from pytrends.request import TrendReq

# ── параметры ───────────────────────────────────────────────────────────────────
SEEDS = pathlib.Path("topics/seed_keywords.txt").read_text("utf-8").splitlines()
TODAY = dt.date.today().isoformat()
QUEUE = pathlib.Path(f"topics/queue_{TODAY}.json")

pytrends = TrendReq(hl="ru-RU", tz=180)
ideas: list[str] = []

# ── основной цикл ───────────────────────────────────────────────────────────────
for kw in SEEDS:
    pytrends.build_payload([kw], timeframe="now 7-d", geo="")
    try:
        rel_dict = pytrends.related_queries()
        rel = rel_dict.get(kw)
        if (
            rel
            and isinstance(rel.get("rising"), pd.DataFrame)
            and not rel["rising"].empty
        ):
            ideas += rel["rising"]["query"].head(5).tolist()
        else:
            ideas.append(kw)
    except Exception:
        ideas.append(kw)

# ── сохраняем очередь ───────────────────────────────────────────────────────────
QUEUE.write_text(json.dumps(ideas, ensure_ascii=False, indent=2), "utf-8")
print(f"Collected {len(ideas)} ideas → {QUEUE}")
