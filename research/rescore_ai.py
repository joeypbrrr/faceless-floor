#!/usr/bin/env python3
"""One-off: re-score the existing data/live.json candidates under the AI-generated = faceless rule (Nov 7 2026).
Uses only public pages: re-reads each deep-dived short's watch page (description + YouTube 'How this was made' label)
and each YouTube candidate's channel page (about text). Face-frame results, views, likes, engagement are reused as collected.
Writes research/rescore/ai-rescore-<date>.json; does not touch data/live.json (the hourly cycle publishes)."""
import json, os, re, sys, copy
sys.path.insert(0, os.path.dirname(__file__))
import pipeline as P

src = json.load(open(P.OUT))
before = {c['key']: {'faceless': c['faceless']['verdict'], 'qualified': bool(c.get('qualified'))} for c in src['candidates']}
CACHE = os.path.join(P.ROOT, 'research/rescore/ai-rescore-cache.json')
cached = '--cached' in sys.argv and os.path.exists(CACHE)
cands = json.load(open(CACHE)) if cached else copy.deepcopy(src['candidates'])
for i, c in enumerate([] if cached else cands):
    if c['platform'] != 'YouTube': c['ai_generated'] = None; continue
    if c.get('recent'):
        for v in c['recent']:
            w = P.watch(v['video_id'])
            if w: v['description'] = w['description']; v['synthetic_label'] = w['synthetic_label']
    elif c.get('description') is None:
        t = P.fetch(f'https://www.youtube.com/{c["handle"]}/shorts', 'YouTube channel pages', marker='ytInitialData')
        d = P.yt_initial(t) if t else None
        md = P.walk(d, 'channelMetadataRenderer', []) if d else []
        if md: c['description'] = (md[0].get('description') or '')[:500]; c['name'] = md[0].get('title') or c['name']
    print(i, c['handle'], file=sys.stderr)
if not cached: json.dump(cands, open(CACHE, 'w'), ensure_ascii=False)
rows = []
for c in cands:
    if c['platform'] == 'YouTube': P.apply_faceless(c, P.REVIEWS)
    else: c['ai_generated'] = {'value': 'unknown', 'evidence': 'No public video text readable on this platform.', 'tells': []}
    P.qualify(c)
    b = before[c['key']]
    rows.append({'handle': c['handle'], 'platform': c['platform'], 'name': c.get('name'), 'deep_dived': bool(c.get('recent')),
                 'ai_generated': c['ai_generated'], 'faceless_before': b['faceless'], 'faceless_after': c['faceless']['verdict'],
                 'faceless_evidence': c['faceless']['evidence'], 'qualified_before': b['qualified'], 'qualified_after': c['qualified'],
                 'not_qualified_because': c['not_qualified_because'], 'followers': (c.get('followers') or {}).get('display'),
                 'median_views': c.get('median_views'), 'like_rate': c.get('like_rate'), 'socialblade': c.get('socialblade'),
                 'latest_upload': c.get('latest_upload'), 'url': c.get('url') or (f'https://www.youtube.com/{c["handle"]}' if c['platform'] == 'YouTube' else None)})
out = {'rescored_at': P.iso(), 'source_snapshot': src['updated_at'], 'rule': 'AI-generated content counts as faceless (see DISCOVERY.md); real human face still fails', 'sources': P.SOURCES, 'rows': rows}
os.makedirs(os.path.join(P.ROOT, 'research/rescore'), exist_ok=True)
fn = os.path.join(P.ROOT, 'research/rescore/ai-rescore-2026-11-07.json')
json.dump(out, open(fn, 'w'), indent=1, ensure_ascii=False)
print('wrote', fn)
