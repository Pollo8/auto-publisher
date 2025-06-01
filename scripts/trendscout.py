import datetime as dt, json, pathlib
from pytrends.request import TrendReq

SEEDS  = pathlib.Path('topics/seed_keywords.txt').read_text('utf-8').splitlines()
TODAY  = dt.date.today().isoformat()
queue  = pathlib.Path(f'topics/queue_{TODAY}.json')

pytrends = TrendReq(hl='ru-RU', tz=180)
ideas = []

for kw in SEEDS:
    pytrends.build_payload([kw], timeframe='now 7-d', geo='')
    related = pytrends.related_queries()[kw]['rising'][:5]
    ideas += [row['query'] for _, row in related.iterrows()]

queue.write_text(json.dumps(ideas, ensure_ascii=False, indent=2), 'utf-8')
print(f'Collected {len(ideas)} ideas → {queue}')