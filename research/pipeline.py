#!/usr/bin/env python3
"""Faceless Floor research cycle. Public, unauthenticated sources only.
No logins, no API keys, no CAPTCHA/Cloudflare bypass: a blocked source is logged and skipped.
Never estimates numbers: anything not read from a source stays null/"unknown"."""
import json, re, time, html, statistics, os, sys, random, traceback
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ET = ZoneInfo('America/New_York')
CFG = json.load(open(os.path.join(ROOT, 'config/discovery.json')))
OUT = os.path.join(ROOT, 'data/live.json')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
S = requests.Session(); S.headers.update({'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
CHALLENGE = re.compile(r'Just a moment\.\.\.|cf-challenge|challenge-platform|/captcha|g-recaptcha', re.I)
REVIEWS = json.load(open(os.path.join(ROOT, 'config/reviews.json'))).get('reviews', {})
MODEL = os.path.join(ROOT, 'research/models/face_detection_yunet_2023mar.onnx')

def now(): return datetime.now(ET)
def iso(d=None): return (d or now()).isoformat(timespec='seconds')
def et_label(d=None): return (d or now()).strftime('%-I:%M %p ET, %b %-d')

SOURCES = {}   # name -> {status, detail, url, at, ok, fail}
FEED = []
AGENT_STATE = {}
BLOCKED_HOSTS = set()

def log_source(name, ok, url, detail=''):
    s = SOURCES.setdefault(name, {'name': name, 'ok': 0, 'fail': 0, 'url': url, 'status': 'reachable', 'detail': '', 'at': iso()})
    s['ok' if ok else 'fail'] += 1; s['at'] = iso()
    if not ok: s['detail'] = detail; s['url'] = url
    s['status'] = 'reachable' if s['ok'] and not s['fail'] else ('partial' if s['ok'] else 'blocked')

def fetch(url, source, marker=None, timeout=20):
    host = url.split('/')[2]
    if host in BLOCKED_HOSTS: return None
    time.sleep((3.0 if 'reddit.com' in host else 0.35) + random.random() * 0.3)
    try:
        r = S.get(url, timeout=timeout, allow_redirects=True)
    except Exception as e:
        log_source(source, False, url, f'network error: {type(e).__name__}'); return None
    if r.status_code == 429:
        BLOCKED_HOSTS.add(host); log_source(source, False, url, 'HTTP 429 rate limited — host skipped for the rest of this cycle'); return None
    if r.status_code != 200:
        log_source(source, False, url, f'HTTP {r.status_code}'); return None
    t = r.text
    from urllib.parse import urlparse
    if urlparse(r.url).path in ('', '/') and urlparse(url).path not in ('', '/'):
        log_source(source, False, url, f'redirected to the site homepage ({r.url[:60]}) — content not publicly available'); return None
    if CHALLENGE.search(t[:20000]) and (marker is None or marker not in t):
        log_source(source, False, url, 'bot challenge / CAPTCHA page (not bypassed)'); return None
    if marker and marker not in t:
        log_source(source, False, url, f'page loaded but expected data missing (login wall or JS-only); redirected to {r.url[:80]}' if r.url != url else 'page loaded but expected data missing (login wall or JS-only)'); return None
    log_source(source, True, url); return t

def act(agent, action, finding=None, status='ok'):
    a = AGENT_STATE[agent]; a['last_action'] = action; a['status'] = status; a['at'] = iso()
    if finding is not None: a['last_finding'] = finding
    FEED.append({'at': iso(), 't': now().strftime('%-I:%M %p'), 'agent': agent, 'who': a['name'], 'msg': action + (f' — {finding}' if finding else ''), 'status': status})

# ---------------- agents ----------------
FIRST = ['Ada','Bram','Cleo','Dex','Eira','Fitz','Gus','Hana','Ivo','Juno','Kai','Lux','Milo','Nia','Oren','Pia','Quin','Rhea','Sol','Tess','Uma','Vic','Wren','Xan','Yara','Zed','Arlo','Bea','Cy','Dot','Eli','Faye','Gio','Hux','Ines','Jax','Kit','Lena','Max','Noor','Otto','Pax','Rue','Sage','Theo','Uri','Vera','Wes','Yuki','Zia']
TRAITS = ['meticulous','restless','skeptical','cheerful','quiet','competitive','curious','blunt','patient','relentless']
TEAMS = [('TikTok scouts',8),('YouTube Shorts scouts',7),('Instagram Reels scouts',7),('Meme page scouts',5),('Faceless niche scouts',10),('Why-it-works analysts',7),('Engagement verifiers',4),('Floor lead',2)]
def build_agents():
    ags = []; n = 0
    ws = CFG['web_search']
    for team, count in TEAMS:
        for i in range(count):
            n += 1; aid = f'agent-{n:02d}'
            if team == 'TikTok scouts':
                task = (f'Web-search TikTok profiles: "{ws["tiktok_queries"][i]}", then read each public profile' if i < 4 else
                        f'Check same-handle TikTok profiles for YouTube candidates, slice {i-3} of 4' if i < 7 else 'Probe TikTok tag/discover pages and Creative Center; log access')
            elif team == 'YouTube Shorts scouts':
                task = f'YouTube channel search: "{CFG["youtube_channel_search"][i]["q"]}"'
            elif team == 'Instagram Reels scouts':
                task = (f'Web-search Instagram pages: "{ws["instagram_queries"][i]}"' if i < 3 else
                        f'Check same-handle Instagram profiles for candidates, slice {i-2} of 3' if i < 6 else 'Probe Instagram tag pages + Social Blade Instagram; log access')
            elif team == 'Meme page scouts':
                task = f'Scan YouTube #{CFG["youtube_hashtag_pages"][i]["tag"]} hashtag page for viral Shorts'
            elif team == 'Faceless niche scouts':
                q = CFG['youtube_viral_shorts_search'][i]; task = f'Viral Shorts search "{q["q"]}" ({q["niche"]})'
            elif team == 'Why-it-works analysts':
                task = f'Deep-dive candidate channels (slice {i+1} of 7): uploads, views, likes, hooks, face check'
            elif team == 'Engagement verifiers':
                task = f'Real-vs-fake check (slice {i+1} of 4): like/view, comments, Social Blade 14-day views'
            else:
                task = ('Read Reddit niche discussions (public RSS) + web-search faceless roundups' if i == 0 else 'Rank verified Top 10 and publish the snapshot')
            ags.append({'id': aid, 'name': f'{FIRST[n-1]} · Agent {n:02d}', 'team': team, 'personality': TRAITS[n % len(TRAITS)], 'task': task,
                        'status': 'idle', 'last_action': 'Waiting for its first cycle', 'last_finding': None, 'at': None})
    return ags

# ---------------- parsers ----------------
def yt_initial(t):
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', t, re.S)
    if not m: return None
    try: return json.loads(m.group(1))
    except Exception: return None

def walk(o, key, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key: out.append(v)
            walk(v, key, out)
    elif isinstance(o, list):
        for x in o: walk(x, key, out)
    return out

def parse_views_text(s):
    """Returns (exact_or_None, display). YouTube abbreviates; abbreviated values are kept as display text only."""
    if not s: return None, None
    m = re.search(r'([\d,.]+)\s*(thousand|million|billion|K|M|B)?\s*views', s, re.I)
    if not m: return None, None
    num, unit = m.group(1), m.group(2)
    return (int(num.replace(',', '')) if not unit else None), (num + (' ' + unit if unit else '') + ' views')

def abbrev_to_floor(display):
    """Lower bound from an abbreviated YouTube count (e.g. '2.1 million views' >= 2,100,000). Used only for ordering, never shown as a measurement."""
    if not display: return 0
    m = re.search(r'([\d,.]+)\s*(thousand|million|billion|K|M|B)?', display, re.I)
    if not m: return 0
    v = float(m.group(1).replace(',', '')); u = (m.group(2) or '').lower()
    return int(v * {'thousand':1e3,'k':1e3,'million':1e6,'m':1e6,'billion':1e9,'b':1e9}.get(u, 1))

def shorts_from_page(d):
    res = []
    for v in walk(d, 'shortsLockupViewModel', []):
        j = json.dumps(v)
        vid = re.search(r'"videoId": "([\w-]{11})"', j)
        acc = v.get('accessibilityText', '')
        if not vid: continue
        title = acc.rsplit(',', 1)[0] if ',' in acc else acc
        _, disp = parse_views_text(acc)
        res.append({'video_id': vid.group(1), 'title': title, 'views_display': disp, 'views_floor': abbrev_to_floor(disp)})
    for v in walk(d, 'videoRenderer', []):
        vid = v.get('videoId'); vt = (v.get('viewCountText') or {}).get('simpleText') or ''
        if not vid: continue
        title = ''.join(r.get('text', '') for r in (v.get('title') or {}).get('runs', []))
        _, disp = parse_views_text(vt)
        res.append({'video_id': vid, 'title': title, 'views_display': disp, 'views_floor': abbrev_to_floor(disp)})
    seen = set(); out = []
    for r in res:
        if r['video_id'] not in seen: seen.add(r['video_id']); out.append(r)
    return out

def watch(video_id, source='YouTube watch pages'):
    t = fetch(f'https://www.youtube.com/watch?v={video_id}', source, marker='"videoDetails"')
    if not t: return None
    g = lambda p: (re.search(p, t) or [None, None])[1]
    likes = g(r'"likeCount":"(\d+)"') or g(r'like this video along with ([\d,]+) other')
    comments = g(r'"contextualInfo":\{"runs":\[\{"text":"([\d,.KM]+)"')
    owner = g(r'"ownerProfileUrl":"http://www\.youtube\.com/(@[^"]+)"') or g(r'"canonicalBaseUrl":"/(@[^"]+)"')
    desc = g(r'"shortDescription":"((?:[^"\\]|\\.)*)"') or ''
    try: desc = json.loads('"' + desc + '"')
    except Exception: pass
    return {'video_id': video_id, 'url': f'https://www.youtube.com/shorts/{video_id}', 'title': html.unescape(g(r'"title":"((?:[^"\\]|\\.)*)","lengthSeconds"') or ''),
            'views': int(g(r'"viewCount":"(\d+)"') or 0) or None, 'likes': int(likes.replace(',', '')) if likes else None,
            'comments_display': comments, 'comments': int(comments.replace(',', '')) if comments and comments.replace(',', '').isdigit() else None,
            'published': g(r'"publishDate":"([^"]+)"'), 'length_s': int(g(r'"lengthSeconds":"(\d+)"') or 0) or None,
            'channel_id': g(r'"channelId":"(UC[\w-]{22})"'), 'channel_name': html.unescape(g(r'"ownerChannelName":"((?:[^"\\]|\\.)*)"') or ''),
            'handle': owner, 'description': desc[:600], 'source': 'YouTube watch page', 'read_at': iso()}

_det = None; _rec = None
REC_MODEL = os.path.join(ROOT, 'research/models/face_recognition_sface_2021dec.onnx')
def faces_in(url):
    """Returns list of face feature vectors found in a public video frame thumbnail (None if unreadable)."""
    global _det, _rec
    import cv2, numpy as np
    try:
        r = S.get(url, timeout=15)
        if r.status_code != 200: return None
        img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
        if img is None: return None
        h, w = img.shape[:2]
        if _det is None: _det = cv2.FaceDetectorYN.create(MODEL, '', (w, h), 0.8, 0.3, 50); _rec = cv2.FaceRecognizerSF.create(REC_MODEL, '')
        _det.setInputSize((w, h)); _, f = _det.detect(img)
        if f is None: return []
        return [_rec.feature(_rec.alignCrop(img, row)) for row in f]
    except Exception:
        return None

def recurring_person(per_video):
    """per_video: list of lists of features. Returns max number of distinct videos one identity appears in (SFace cosine >= 0.363)."""
    import cv2
    nodes = [(vi, f) for vi, fs in enumerate(per_video) for f in fs]
    parent = list(range(len(nodes)))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if _rec.match(nodes[i][1], nodes[j][1], cv2.FaceRecognizerSF_FR_COSINE) >= 0.363: parent[find(i)] = find(j)
    groups = {}
    for i, (vi, _) in enumerate(nodes): groups.setdefault(find(i), set()).add(vi)
    return max((len(g) for g in groups.values()), default=0)

# ---------------- cycle ----------------
def main():
    started = now()
    agents = build_agents()
    for a in agents: AGENT_STATE[a['id']] = a
    by_team = {}
    for a in agents: by_team.setdefault(a['team'], []).append(a['id'])
    cands = {}  # key: handle lower
    def cand(handle, platform='YouTube', **kw):
        if not handle: return None
        handle = handle if handle.startswith('@') else '@' + handle
        k = platform + ':' + handle.lower()
        c = cands.setdefault(k, {'key': k, 'platform': platform, 'handle': handle, 'name': None, 'found_by': [], 'niche': None, 'signals': [], 'best_short_floor': 0})
        for kk, vv in kw.items():
            if vv is not None and not c.get(kk): c[kk] = vv
        return c

    # 1. directory reachability
    lead = by_team['Floor lead']
    dirs = []
    for d in CFG['directories']:
        t = fetch(d['url'], 'Directory: ' + d['name'], marker=d['marker'])
        st = SOURCES.get('Directory: ' + d['name'], {})
        dirs.append({**{k: d[k] for k in ('name', 'url', 'use')}, 'status': 'reachable' if t else 'blocked', 'detail': st.get('detail', ''), 'checked_at': iso()})
    ok = sum(1 for d in dirs if d['status'] == 'reachable')
    act(lead[1], f'Checked {len(dirs)} public directories/sources', f'{ok} reachable, {len(dirs)-ok} blocked or unavailable')

    # 2. YouTube channel search (Shorts scouts)
    for aid, q in zip(by_team['YouTube Shorts scouts'], CFG['youtube_channel_search']):
        t = fetch('https://www.youtube.com/results?search_query=' + quote_plus(q['q']) + '&sp=EgIQAg%253D%253D', 'YouTube search', marker='channelRenderer')
        d = yt_initial(t) if t else None
        if not d: act(aid, f'Channel search "{q["q"]}"', 'source failed (logged)', 'blocked'); continue
        found = []
        for ch in walk(d, 'channelRenderer', []):
            handle = (ch.get('subscriberCountText') or {}).get('simpleText', '')
            base = json.dumps(ch.get('navigationEndpoint', {}))
            m = re.search(r'"canonicalBaseUrl": "/(@[^"]+)"', base)
            handle = m.group(1) if m else (handle if handle.startswith('@') else None)
            subs = ((ch.get('videoCountText') or {}).get('accessibility') or {}).get('accessibilityData', {}).get('label')
            c = cand(handle, name=(ch.get('title') or {}).get('simpleText'), channel_id=ch.get('channelId'), niche=q['q'])
            if c: c['found_by'].append(aid); c['signals'].append(f'channel search "{q["q"]}" ({subs or "subs n/a"})'); found.append(handle)
        act(aid, f'Channel search "{q["q"]}"', f'{len(found)} channels: ' + ', '.join(found[:4]) if found else 'no channels parsed')

    # 3. viral Shorts searches (niche scouts) + hashtag pages (meme scouts)
    def shorts_job(aid, url, label, niche):
        t = fetch(url, 'YouTube search' if 'results' in url else 'YouTube hashtag pages', marker='shortsLockupViewModel' if 'results' in url else 'videoRenderer')
        d = yt_initial(t) if t else None
        if not d: act(aid, label, 'source failed (logged)', 'blocked'); return
        shorts = sorted(shorts_from_page(d), key=lambda s: -s['views_floor'])[:3]
        names = []
        for s in shorts:
            w = watch(s['video_id'])
            if not w or not w['handle']: continue
            c = cand(w['handle'], name=w['channel_name'], channel_id=w['channel_id'], niche=niche)
            c['found_by'].append(aid); c['signals'].append(f'viral short {w["views"]:,} views ({label})' if w['views'] else f'short via {label}')
            c['best_short_floor'] = max(c['best_short_floor'], w['views'] or 0); names.append(f'{w["handle"]} ({w["views"]:,} views)' if w['views'] else w['handle'])
        act(aid, label, '; '.join(names) if names else 'no channels resolved')
    for aid, q in zip(by_team['Faceless niche scouts'], CFG['youtube_viral_shorts_search']):
        shorts_job(aid, 'https://www.youtube.com/results?search_query=' + quote_plus(q['q']), f'Viral Shorts search "{q["q"]}"', q['niche'])
    for aid, h in zip(by_team['Meme page scouts'], CFG['youtube_hashtag_pages']):
        shorts_job(aid, 'https://www.youtube.com/hashtag/' + h['tag'], f'#{h["tag"]} hashtag page', h['niche'])

    # 4. Reddit RSS + roundup web search (lead 1)
    threads = []
    subs = CFG['reddit']['subs']; k = CFG['reddit'].get('per_cycle', 2); h0 = (now().hour * k) % len(subs)
    for sub in (subs + subs)[h0:h0 + k]:
        for term in CFG['reddit']['search_terms'][:1]:
            t = fetch(f'https://www.reddit.com/r/{sub}/search.rss?q={quote_plus(term)}&restrict_sr=1&sort=top&t=month', 'Reddit public RSS', marker='<feed')
            if not t: continue
            for e in re.findall(r'<entry>(.*?)</entry>', t, re.S)[:6]:
                ti = re.search(r'<title>(.*?)</title>', e, re.S); li = re.search(r'<link href="([^"]+)"', e); up = re.search(r'<updated>([^<]+)', e)
                if ti and li and li.group(1) not in {x['url'] for x in threads}:
                    threads.append({'sub': sub, 'term': term, 'title': html.unescape(ti.group(1)), 'url': li.group(1), 'updated': up.group(1) if up else None})
                for h in re.findall(r'youtube\.com/(@[\w.\-]{3,30})', html.unescape(e)):
                    c = cand(h, niche='mentioned on Reddit'); c['found_by'].append(lead[0]); c['signals'].append(f'mentioned in r/{sub}')
    act(lead[0], f'Read Reddit RSS (r/' + ', r/'.join((subs + subs)[h0:h0 + k]) + ')', f'{len(threads)} niche threads' + (f', e.g. “{threads[0]["title"][:70]}”' if threads else ''))
    def bing(q, aid, platform):
        t = fetch('https://lite.duckduckgo.com/lite/?q=' + quote_plus(q), 'DuckDuckGo Lite search', marker='result-link')
        if not t: t = fetch('https://www.bing.com/search?q=' + quote_plus(q) + '&count=30', 'Bing web search', marker='<cite')
        if not t: return []
        txt = html.unescape(t)
        txt = re.sub(r'%40', '@', txt); txt = re.sub(r'%2F', '/', txt)
        pat = {'YouTube': r'youtube\.com(?:/| › )(@[\w.\-]{3,30})', 'TikTok': r'tiktok\.com(?:/| › )(@[\w.]{2,24})', 'Instagram': r'instagram\.com(?:/| › )([\w.]{3,30})'}[platform]
        hs = []
        for h in re.findall(pat, txt):
            h = h.rstrip('.'); hl = h.lower().lstrip('@')
            if hl in ('explore','reel','reels','p','accounts','tags','tag','discover','about','popular') or h in hs: continue
            hs.append(h)
        return hs[:8]
    for q in CFG['web_search']['roundup_queries']:
        for h in bing(q, lead[0], 'YouTube'):
            c = cand(h, niche='faceless roundup'); c['found_by'].append(lead[0]); c['signals'].append(f'listed in web results for "{q}"')

    # 5. deep dive YouTube candidates (analysts)
    yt = [c for c in cands.values() if c['platform'] == 'YouTube']
    yt.sort(key=lambda c: (-c['best_short_floor'], -len(c['signals'])))
    for sd in CFG.get('seeds', []):
        if sd.get('platform') == 'YouTube':
            c = cand(sd['handle'], niche=sd.get('niche')); c['found_by'].append('seed'); c['signals'].append('tracked seed: ' + sd['reason']); c['seed'] = True
    yt = [c for c in cands.values() if c['platform'] == 'YouTube']
    yt.sort(key=lambda c: (not c.get('seed'), -c['best_short_floor'], -len(c['signals'])))
    deep = yt[:34]
    analysts = by_team['Why-it-works analysts']
    for i, c in enumerate(deep):
        aid = analysts[i % len(analysts)]
        t = fetch(f'https://www.youtube.com/{c["handle"]}/shorts', 'YouTube channel pages', marker='ytInitialData')
        d = yt_initial(t) if t else None
        if not d: c['deep'] = 'failed'; act(aid, f'Deep-dive {c["handle"]}', 'channel page failed (logged)', 'blocked'); continue
        subs = re.search(r'"([\d.,]+[KMB]?) subscribers"', t)
        c['followers'] = {'display': subs.group(1) if subs else None, 'source': f'YouTube channel page (rounded by YouTube)', 'url': f'https://www.youtube.com/{c["handle"]}', 'read_at': iso()}
        md = walk(d, 'channelMetadataRenderer', [])
        if md: c['name'] = md[0].get('title') or c['name']; c['description'] = (md[0].get('description') or '')[:500]; c['channel_id'] = md[0].get('externalId') or c.get('channel_id')
        c['url'] = f'https://www.youtube.com/{c["handle"]}'
        shorts = shorts_from_page(d)[:6]
        if not shorts:
            t2 = fetch(f'https://www.youtube.com/{c["handle"]}/videos', 'YouTube channel pages', marker='ytInitialData')
            d2 = yt_initial(t2) if t2 else None
            shorts = shorts_from_page(d2)[:6] if d2 else []
        vids = [w for w in (watch(s['video_id']) for s in shorts) if w]
        c['recent'] = vids
        frames = []; per_video = []
        for v in vids:
            fv = []
            for k in (1, 2, 3):
                fs = faces_in(f'https://i.ytimg.com/vi/{v["video_id"]}/hq{k}.jpg')
                if fs is not None: frames.append(len(fs)); fv.extend(fs)
            per_video.append(fv)
        c['face_frames'] = {'checked': len(frames), 'with_face': sum(1 for n in frames if n > 0), 'videos': len(vids),
                            'max_videos_same_person': recurring_person(per_video) if any(per_video) else 0}
        views = [v['views'] for v in vids if v['views']]
        c['median_views'] = int(statistics.median(views)) if views else None
        act(aid, f'Deep-dive {c["handle"]}', f'{c["followers"]["display"] or "?"} subs; {len(vids)} recent shorts read; median {c["median_views"]:,} views; faces in {c["face_frames"]["with_face"]}/{len(frames)} frames' if c['median_views'] else f'{len(vids)} recent shorts read')

    # 6. engagement verification + Social Blade (verifiers)
    verifiers = by_team['Engagement verifiers']
    for i, c in enumerate([c for c in deep if c.get('recent')]):
        aid = verifiers[i % len(verifiers)]
        vids = c['recent']; reasons = []; verdict = 'pass'
        rates = [v['likes'] / v['views'] for v in vids if v.get('likes') and v.get('views')]
        c['like_rate'] = round(statistics.median(rates), 4) if rates else None
        withc = sum(1 for v in vids if (v.get('comments') or 0) > 0 or (v.get('comments_display') and v['comments_display'] != '0'))
        if c['like_rate'] is None: verdict = 'unknown'; reasons.append('likes hidden or unreadable')
        elif c['like_rate'] < 0.005: verdict = 'suspicious'; reasons.append(f'very low like rate {c["like_rate"]:.2%} (possible bought views)')
        elif c['like_rate'] > 0.25: verdict = 'suspicious'; reasons.append(f'abnormally high like rate {c["like_rate"]:.2%} (possible bought likes)')
        else: reasons.append(f'median like rate {c["like_rate"]:.2%} is in the normal 0.5–25% band')
        if withc < 2: verdict = 'suspicious' if verdict == 'pass' else verdict; reasons.append(f'comments present on only {withc}/{len(vids)} sampled shorts')
        else: reasons.append(f'comments present on {withc}/{len(vids)} sampled shorts')
        sb = fetch(f'https://socialblade.com/youtube/handle/{c["handle"].lstrip("@").lower()}', 'Social Blade (YouTube)', marker='Daily Channel Metrics')
        c['socialblade'] = None
        if sb:
            txt = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>', ' ', sb, flags=re.S))))
            rows = re.findall(r'(\d{4}-\d{2}-\d{2}) (?:--|[+-][\d,.KM]+) [\d.,KMB]+ (?:--|\+?([\d,]+)) ([\d,]+)', txt)
            gains = [int(g.replace(',', '')) for _, g, _ in rows if g]
            if rows:
                c['socialblade'] = {'days': len(rows), 'views_gained': sum(gains), 'first': rows[0][0], 'last': rows[-1][0], 'url': f'https://socialblade.com/youtube/handle/{c["handle"].lstrip("@").lower()}', 'read_at': iso()}
                if sum(gains) <= 0: verdict = 'suspicious' if verdict == 'pass' else verdict; reasons.append('Social Blade shows no view growth in its daily table')
                else: reasons.append(f'Social Blade: +{sum(gains):,} channel views over {len(rows)} days ({rows[0][0]} → {rows[-1][0]})')
        if not c['socialblade']: reasons.append('Social Blade daily table unavailable this cycle')
        c['engagement_check'] = {'verdict': verdict, 'reasons': reasons, 'checked_at': iso(), 'by': aid}
        act(aid, f'Verified {c["handle"]}', f'{verdict}: ' + '; '.join(reasons[:2]))

    # 7. TikTok + Instagram scouts
    tt = by_team['TikTok scouts']; ig = by_team['Instagram Reels scouts']
    def tiktok_profile(h):
        t = fetch(f'https://www.tiktok.com/{h}', 'TikTok public profile pages', marker='"followerCount"')
        if not t: return None
        g = lambda p: (re.search(p, t) or [None, None])[1]
        return {'followers': int(g(r'"followerCount":(\d+)') or 0), 'hearts': int(g(r'"heartCount":(\d+)') or 0), 'videos': int(g(r'"videoCount":(\d+)') or 0),
                'nickname': html.unescape(g(r'"nickname":"((?:[^"\\]|\\.)*)"') or ''), 'url': f'https://www.tiktok.com/{h}', 'read_at': iso(), 'source': 'TikTok public profile page'}
    for i, q in enumerate(CFG['web_search']['tiktok_queries']):
        hs = bing(q, tt[i], 'TikTok'); got = []
        for h in hs[:4]:
            p = tiktok_profile(h if h.startswith('@') else '@' + h)
            if p:
                c = cand(h, 'TikTok', name=p['nickname'], niche=q.replace('site:tiktok.com ', ''), url=p['url']); c['tiktok'] = p; c['found_by'].append(tt[i])
                c['followers'] = {'value': p['followers'], 'display': f'{p["followers"]:,}', 'source': 'TikTok public profile page', 'url': p['url'], 'read_at': p['read_at']}
                got.append(f'{c["handle"]} {p["followers"]:,} followers')
        act(tt[i], f'Web search "{q}"', '; '.join(got) if got else (f'{len(hs)} profile links found, none readable' if hs else 'no TikTok profile links in results'))
    for sd in CFG.get('seeds', []):
        if sd.get('platform') == 'TikTok':
            p = tiktok_profile(sd['handle'])
            c = cand(sd['handle'], 'TikTok', niche=sd.get('niche'), url=sd['url']); c['seed'] = True; c['found_by'].append('seed'); c['signals'].append('tracked seed: ' + sd['reason'])
            if p:
                c['tiktok'] = p; c['name'] = p['nickname']
                c['followers'] = {'value': p['followers'], 'display': f'{p["followers"]:,}', 'source': 'TikTok public profile page', 'url': p['url'], 'read_at': p['read_at']}
    top_yt = [c for c in deep if c.get('recent')][:12]
    for j in range(3):
        aid = tt[4 + j]; got = []
        for c in top_yt[j::3]:
            p = tiktok_profile(c['handle'])
            if p:
                match = p['nickname'].strip().lower() == (c.get('name') or '').strip().lower()
                c['tiktok_same_handle'] = {**p, 'nickname_matches_youtube_name': match, 'note': 'Same handle exists on TikTok; ownership is confirmed only if the display name matches' }
                got.append(f'{c["handle"]}: {p["followers"]:,} followers' + (' (name matches)' if match else ' (different name — may be another owner)'))
        act(aid, 'Checked same-handle TikTok profiles', '; '.join(got) if got else 'no same-handle TikTok profiles readable')
    for url, name in [('https://www.tiktok.com/tag/redditstories', 'TikTok tag pages'), ('https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en', 'TikTok Creative Center')]:
        fetch(url, name, marker='"uniqueId"' if 'tag' in url else 'hashtag_name')
    act(tt[7], 'Probed TikTok tag page + Creative Center', ', '.join(f'{n}: {SOURCES[n]["status"]}' for n in ('TikTok tag pages', 'TikTok Creative Center') if n in SOURCES))
    for i, q in enumerate(CFG['web_search']['instagram_queries']):
        hs = bing(q, ig[i], 'Instagram'); got = []
        for h in hs[:3]:
            t = fetch(f'https://www.instagram.com/{h.lstrip("@")}/', 'Instagram public profile pages', marker='edge_followed_by')
            c = cand(h, 'Instagram', niche=q.replace('site:instagram.com ', ''), url=f'https://www.instagram.com/{h.lstrip("@")}/'); c['found_by'].append(ig[i])
            got.append(h)
        act(ig[i], f'Web search "{q}"', (f'{len(got)} pages found ({", ".join(got)}); profile stats behind login wall' if got else 'no Instagram links in results'), 'ok' if got else 'ok')
    for j in range(3):
        aid = ig[3 + j]; n_ok = 0
        for c in top_yt[j::3][:2]:
            if fetch(f'https://www.instagram.com/{c["handle"].lstrip("@")}/', 'Instagram public profile pages', marker='edge_followed_by'): n_ok += 1
        st = SOURCES.get('Instagram public profile pages', {}).get('status', 'unknown')
        act(aid, 'Checked same-handle Instagram profiles', f'{n_ok} readable; source status: {st}', 'blocked' if not n_ok else 'ok')
    fetch('https://www.instagram.com/explore/tags/memes/', 'Instagram hashtag pages', marker='edge_hashtag')
    fetch('https://socialblade.com/instagram/user/natgeo', 'Social Blade (Instagram)', marker='followers')
    act(ig[6], 'Probed Instagram tag pages + Social Blade Instagram', ', '.join(f'{n}: {SOURCES[n]["status"]}' for n in ('Instagram hashtag pages', 'Social Blade (Instagram)') if n in SOURCES))

    # 8. analysis, qualification, ranking (lead 2)
    for c in cands.values():
        vids = c.get('recent') or []
        ff = c.get('face_frames')
        if ff and ff['checked'] >= 6 and ff.get('videos', 0) >= 3:
            rp = ff['max_videos_same_person']
            if ff['with_face'] == 0: verdict, ev = 'yes', f'No faces in any of {ff["checked"]} frames sampled from the {ff["videos"]} latest shorts.'
            elif rp >= 3: verdict, ev = 'no', f'The same person/character appears in {rp} of the {ff["videos"]} latest shorts (on-camera host).'
            elif rp == 2: verdict, ev = 'unclear', f'Faces in {ff["with_face"]}/{ff["checked"]} frames; one person recurs in 2 of {ff["videos"]} shorts.'
            else: verdict, ev = 'yes', f'Faces in {ff["with_face"]}/{ff["checked"]} frames, but no person recurs across shorts (stock/clip footage, no host).'
            c['faceless'] = {'verdict': verdict, 'method': 'automated', 'evidence': ev + ' Method: automated OpenCV YuNet face detection + SFace identity matching on YouTube frame thumbnails (hq1–hq3).'}
        else:
            c['faceless'] = {'verdict': 'unknown', 'evidence': 'Not enough public frames checked (needs ≥6 frames from ≥3 recent videos; not available for this platform/source).'}
        rv = REVIEWS.get(c['handle'])
        if rv: c['faceless'] = {'verdict': rv['faceless'], 'method': 'manual review', 'evidence': f'Manual review ({rv["reviewed_at"][:10]}): {rv["evidence"]}', 'automated': c['faceless']}
        text = ' '.join([c.get('description') or ''] + [v.get('description') or '' for v in vids]).lower()
        routes = []
        if re.search(r'amzn\.to|amazon\.com', text): routes.append('Amazon affiliate links in descriptions')
        if re.search(r'linktr\.ee|beacons\.ai|stan\.store|gumroad|shopify|etsy\.com|\.store\b|merch', text): routes.append('own store / link-in-bio product links')
        if re.search(r'patreon|ko-fi|buymeacoffee', text): routes.append('fan support (Patreon/Ko-fi)')
        if re.search(r'business|sponsor|inquir', text): routes.append('sponsorship inquiries invited')
        c['monetization'] = {'routes': routes or ['YouTube Shorts ad-revenue share (Partner Program status is not publicly visible)'] if c['platform'] == 'YouTube' else (routes or ['unknown']),
                             'evidence': 'Read from public channel/video descriptions' if routes else 'No commercial links found in public descriptions'}
        if vids:
            ds = sorted([datetime.fromisoformat(v['published']) for v in vids if v.get('published')])
            lens = [v['length_s'] for v in vids if v.get('length_s')]
            titles = [v['title'] for v in vids if v.get('title')]
            why = []
            if len(ds) >= 2:
                span = max((ds[-1] - ds[0]).total_seconds() / 86400, 0.01); why.append(f'Posting cadence: {len(ds)} shorts in {span:.1f} days (latest {ds[-1].astimezone(ET).strftime("%b %-d")}).')
            if lens: why.append(f'Length: {min(lens)}–{max(lens)} s per short (median {int(statistics.median(lens))} s).')
            if c.get('median_views'): why.append(f'Recent reach: median {c["median_views"]:,} views on the latest {len(vids)} shorts' + (f', median like rate {c["like_rate"]:.1%}.' if c.get('like_rate') else '.'))
            hooks = []
            if sum('?' in t for t in titles) >= 2: hooks.append('question titles')
            if sum(bool(re.search(r'\d', t)) for t in titles) >= 2: hooks.append('numbers in titles')
            if sum(bool(re.search(r'#\w', t)) for t in titles) >= 2: hooks.append('hashtags in titles')
            if sum(bool(re.search(r'\b(POV|AITA|WIBTA|TIFU)\b', t, re.I)) for t in titles) >= 1: hooks.append('Reddit-style framing (AITA/POV/TIFU)')
            if sum(t.isupper() for t in titles if len(t) > 8) >= 1: hooks.append('all-caps hooks')
            if titles: why.append('Title hooks: ' + (', '.join(hooks) if hooks else 'plain descriptive titles') + f'. Example: “{titles[0][:80]}”.')
            c['why_it_works'] = why
            c['replication_note'] = (f'Copy the format only: ~{int(statistics.median(lens)) if lens else "?"} s vertical {c.get("niche") or "faceless"} shorts, '
                                     f'same hook style ({", ".join(hooks) if hooks else "direct titles"}), similar cadence. Write original scripts and use our own or licensed footage — never repost their clips.')
            c['latest_upload'] = ds[-1].isoformat() if ds else None
    QUAL = {'min_median_views': 100000, 'max_days_since_upload': 14, 'min_shorts_sampled': 4}
    top = []
    for c in cands.values():
        why_not = []
        vids = c.get('recent') or []
        if c['platform'] != 'YouTube': why_not.append('no public per-video view counts on this platform from reachable sources')
        if len([v for v in vids if v.get('views') and v.get('likes') is not None]) < QUAL['min_shorts_sampled']: why_not.append('fewer than 4 recent shorts with exact views + likes')
        if (c.get('median_views') or 0) < QUAL['min_median_views']: why_not.append(f'median recent views below {QUAL["min_median_views"]:,}')
        if c.get('latest_upload'):
            age = (now() - datetime.fromisoformat(c['latest_upload'])).days
            if age > QUAL['max_days_since_upload']: why_not.append(f'latest upload {age} days ago')
        if c['faceless']['verdict'] != 'yes': why_not.append(f'faceless check: {c["faceless"]["verdict"]}')
        if (c.get('engagement_check') or {}).get('verdict') != 'pass': why_not.append(f'engagement check: {(c.get("engagement_check") or {}).get("verdict", "not run")}')
        if not (c.get('followers') or {}).get('display'): why_not.append('follower count not read')
        c['qualified'] = not why_not; c['not_qualified_because'] = why_not
        if c['qualified']: top.append(c)
    top.sort(key=lambda c: -c['median_views'])
    top = top[:10]
    for i, c in enumerate(top): c['rank'] = i + 1
    act(lead[1], 'Ranked verified Top 10', f'{len(top)} of {len(cands)} candidates qualify' + (f'; #1 {top[0]["handle"]} (median {top[0]["median_views"]:,} views)' if top else ''))

    for a in agents:
        if a['status'] == 'idle': a['last_action'] = 'No work assigned this cycle'; a['at'] = iso()
    finished = now()
    nxt = os.environ.get('NEXT_CYCLE_EPOCH')
    snapshot = {
        'mode': 'live', 'updated_at': iso(finished), 'updated_label': et_label(finished), 'cycle_started': iso(started),
        'next_cycle_at': datetime.fromtimestamp(int(nxt), ET).isoformat(timespec='seconds') if nxt else None,
        'qualification': {**QUAL, 'faceless': 'no person recurs on camera in ≥2 of the 6 latest shorts (automated face detection + identity matching), or a dated manual review', 'engagement': 'like rate 0.5–25%, comments on ≥2 sampled shorts, no flat Social Blade growth'},
        'counts': {'candidates': len(cands), 'deep_dived': len([c for c in cands.values() if c.get('recent')]), 'qualified': len(top),
                   'by_platform': {p: sum(1 for c in cands.values() if c['platform'] == p) for p in ('YouTube', 'TikTok', 'Instagram')}},
        'top10': top, 'candidates': sorted(cands.values(), key=lambda c: (not c.get('qualified'), -(c.get('median_views') or 0), -(c.get('followers') or {}).get('value', 0))),
        'agents': agents, 'feed': FEED[::-1][:120], 'sources': sorted(SOURCES.values(), key=lambda s: (s['status'] == 'reachable', s['name'])),
        'directories': dirs, 'reddit_threads': threads[:30],
        'discovery': {'checked_at': CFG['checked_at'], 'youtube_channel_search': [q['q'] for q in CFG['youtube_channel_search']],
                      'youtube_viral_shorts_search': [q['q'] for q in CFG['youtube_viral_shorts_search']], 'youtube_hashtags': ['#' + h['tag'] for h in CFG['youtube_hashtag_pages']],
                      'web_search': CFG['web_search'], 'reddit_subs': ['r/' + s for s in CFG['reddit']['subs']], 'seeds': CFG.get('seeds', [])},
        'policy': 'Public, unauthenticated sources only. No logins, accounts, keys or bot-check bypass. Unknown numbers stay unknown. Replication copies formats, never content.'
    }
    for c in snapshot['candidates']:
        for v in c.get('recent') or []: v.pop('description', None)
    tmp = OUT + '.tmp'; json.dump(snapshot, open(tmp, 'w'), indent=1, ensure_ascii=False); os.replace(tmp, OUT)
    print(f'cycle done {et_label(finished)}: {len(cands)} candidates, {snapshot["counts"]["deep_dived"]} deep-dived, {len(top)} qualified; sources: ' +
          ', '.join(f'{s["name"]}={s["status"]}' for s in SOURCES.values()))

if __name__ == '__main__':
    main()
