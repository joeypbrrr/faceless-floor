#!/usr/bin/env python3
"""TikTok research for Faceless Floor. Public pages only.

No logins, accounts, cookies, or CAPTCHA bypass. No undocumented TikTok APIs.
Numbers are whatever a public page actually contained; missing stays missing.
Profile HTML exposes follower/like/video totals. userInfo.itemList is empty, so
recent videos are discovered from public article links and DuckDuckGo/Bing HTML,
confirmed with the official oEmbed endpoint, and measured on the public video page
(statsV2.playCount). HypeAuditor ranking averages are a cross-check only.
"""
import os, sys, re, json, html, statistics
from datetime import datetime, timezone
from urllib.parse import quote_plus

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor'))
from langdetect import DetectorFactory, detect_langs, LangDetectException
DetectorFactory.seed = 0

def _pipeline():
    """Use the running pipeline module so source logs land in the snapshot.

    `python3 research/pipeline.py` executes that file as __main__. Importing it
    again under the name pipeline would keep a second copy of SOURCES."""
    main = sys.modules.get('__main__')
    if main is not None and hasattr(main, 'fetch') and hasattr(main, 'SOURCES'):
        return main
    import pipeline
    return pipeline

P = _pipeline()

VIDEO_URL_RE = re.compile(r'https?://(?:www\.)?tiktok\.com/@([A-Za-z0-9._]{2,24})/video/(\d{8,22})', re.I)
LOOSE_VIDEO_RE = re.compile(r'tiktok\.com(?:/| › )@([A-Za-z0-9._]{2,24})(?:/| › )video(?:/| › )(\d{8,22})', re.I)
HANDLE_URL_RE = re.compile(r'https?://(?:www\.)?tiktok\.com/@([A-Za-z0-9._]{2,24})(?![A-Za-z0-9._])', re.I)
LOOSE_HANDLE_RE = re.compile(r'tiktok\.com(?:/| › )@([A-Za-z0-9._]{2,24})(?![A-Za-z0-9._])', re.I)
NICHE_RE = re.compile(r'\b(faceless|voice[\s-]?over|voiceover|reddit|satisfying|quiz|asmr|narrat\w*|text[\s-]?to[\s-]?speech)\b', re.I)
USER_RE = re.compile(r'faceless|reddit|quiz|facts|asmr|voiceover|satisfying|aistory|ai[-_.]?story', re.I)
SKIP_HANDLES = {'explore', 'tag', 'discover', 'music', 'legal', 'about', 'login', 'share', 'search', 'embed', 'live', 'following', 'inbox', 'foryou', 'en'}
MAX_PROFILES = 40
MAX_URLS_PER_ACCOUNT = 8
TIKTOK_GET_CAP = 120
ENGLISH_SHARE = 0.6

def cfg():
    return P.CFG.get('tiktok') or {}

def as_int(value):
    if value is None or value == '': return None
    try: return int(str(value).replace(',', ''))
    except (TypeError, ValueError): return None

def unwrap_nuxt(data, idx, seen=None, depth=0):
    """Resolve a Nuxt 3 devalue payload (public ranking pages ship one)."""
    if depth > 14 or not isinstance(idx, int) or idx < 0 or idx >= len(data):
        return None
    if seen is None: seen = set()
    if idx in seen: return None
    seen = seen | {idx}
    v = data[idx]
    if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], int) and v[0] in ('ShallowReactive', 'Reactive', 'Ref', 'ShallowRef', 'EmptyRef'):
        return unwrap_nuxt(data, v[1], seen, depth + 1)
    if isinstance(v, dict):
        return {k: unwrap_nuxt(data, val, seen, depth + 1) if isinstance(val, int) else val for k, val in v.items()}
    if isinstance(v, list):
        return [unwrap_nuxt(data, x, seen, depth + 1) if isinstance(x, int) else x for x in v]
    return v

def dig(o, *path):
    for p in path:
        if not isinstance(o, dict) or p not in o: return None
        o = o[p]
    return o

def parse_hypeauditor(page_html, source_url, list_name, country, read_at, limit=50):
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', page_html, re.S)
    if not m: return []
    try: data = json.loads(m.group(1))
    except json.JSONDecodeError: return []
    root = unwrap_nuxt(data, 0)
    found = []
    def walk(o):
        if isinstance(o, dict):
            basic, metrics = o.get('basic'), o.get('metrics')
            if isinstance(basic, dict) and basic.get('username') and isinstance(metrics, dict):
                found.append(o); return
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(root)
    rows = []
    for i, o in enumerate(found[:limit], 1):
        b, met = o['basic'], o['metrics']
        rows.append({
            'rank': o.get('_number') if isinstance(o.get('_number'), int) else i,
            'list': list_name, 'country': country, 'username': b.get('username'),
            'fullname': b.get('fullname') or None,
            'description': (b.get('description') or '')[:400],
            'followers': as_int(dig(met, 'subscribers_count', 'value')),
            'avg_views_30d': as_int(dig(met, 'views_avg', 'performance', '30d', 'value')),
            'avg_likes_30d': as_int(dig(met, 'alikes_avg', 'performance', '30d', 'value')),
            'avg_comments_30d': as_int(dig(met, 'comments_avg', 'performance', '30d', 'value')),
            'avg_shares_30d': as_int(dig(met, 'shares_avg', 'performance', '30d', 'value')),
            'last_media_time': b.get('last_media_time') or None,
            'profile_url': f'https://www.tiktok.com/@{b.get("username")}',
            'source_url': source_url, 'read_at': read_at,
            'source': 'HypeAuditor public ranking page',
        })
    return rows

def normalize_html(text):
    text = html.unescape(text or '')
    return text.replace('\\/', '/').replace('%40', '@').replace('%2F', '/').replace('%2f', '/')

def extract_refs(text):
    text = normalize_html(text)
    videos, handles = {}, []
    for rx in (VIDEO_URL_RE, LOOSE_VIDEO_RE):
        for handle, vid in rx.findall(text):
            h = handle.strip('.').lower()
            if h in SKIP_HANDLES: continue
            videos.setdefault(h, [])
            url = f'https://www.tiktok.com/@{h}/video/{vid}'
            if url not in videos[h]: videos[h].append(url)
    seen = set()
    for rx in (HANDLE_URL_RE, LOOSE_HANDLE_RE):
        for handle in rx.findall(text):
            h = handle.strip('.').lower()
            if h in SKIP_HANDLES or h in seen: continue
            seen.add(h); handles.append(h)
    return handles, videos

def detect_lang(text):
    if not text: return None
    cleaned = re.sub(r'https?://\S+', ' ', text)
    cleaned = re.sub(r'[#@]', ' ', cleaned)
    if len(re.findall(r'[A-Za-z]', cleaned)) < 25: return None
    try: langs = detect_langs(cleaned)
    except LangDetectException: return None
    if not langs: return None
    best = langs[0]
    return {'lang': best.lang, 'prob': round(best.prob, 3), 'detector': 'langdetect 1.0.9'}

def video_language(v):
    """One label per video. TikTok's caption language is the label; langdetect only overrides it on a long caption."""
    plat = (v.get('text_language') or '').lower()[:2]
    cap = (v.get('caption_language') or '').lower()[:2]
    det = v.get('detector') or {}
    letters = len(re.findall(r'[A-Za-z]', v.get('description') or ''))
    # Short captions are mostly hashtags; langdetect will call those Catalan or Indonesian.
    det_lang = det.get('lang') if det.get('prob', 0) >= 0.85 and letters >= 80 else None
    platform = plat or cap
    if platform and det_lang and platform != det_lang:
        return None, 'conflict'
    if platform:
        return platform, ('TikTok textLanguage' if plat else 'TikTok caption languageCode')
    if det_lang:
        return det_lang, 'langdetect'
    return None, 'unclassified'

def language_verdict(bio, account_language, videos):
    samples = []
    labels = []
    for v in videos:
        label, how = video_language(v)
        samples.append({'url': v.get('url'), 'label': label, 'how': how, 'text_language': v.get('text_language'),
                        'caption_language': v.get('caption_language'), 'detector': v.get('detector'),
                        'excerpt': (v.get('description') or '')[:160]})
        if label: labels.append(label)
    bio_det = detect_lang(bio or '')
    classified = len(labels)
    english_n = sum(1 for l in labels if l == 'en')
    share = (english_n / classified) if classified else None
    conflicts = sum(1 for s in samples if s['how'] == 'conflict')
    if classified == 0:
        return {'verdict': 'unverified', 'english_videos': 0, 'classified_videos': 0, 'share': None,
                'bio': bio_det, 'account_language_setting': account_language,
                'evidence': 'No video caption was long enough, or labelled, to judge language. The bio alone is not enough.',
                'samples': samples}
    verdict = 'english' if share >= ENGLISH_SHARE else 'not_english'
    bio_note = ''
    if bio_det and bio_det['lang'] != 'en' and bio_det['prob'] >= 0.9 and verdict == 'english':
        bio_note = f' Bio detects as {bio_det["lang"]} ({bio_det["prob"]}); video captions are still the content check.'
    if account_language and not str(account_language).lower().startswith('en'):
        bio_note += f' Profile language setting is {account_language} (account UI language, not the caption verdict).'
    ev = (f'{english_n}/{classified} classified captions are English'
          + (f' ({conflicts} caption(s) had conflicting signals and were not counted as English).' if conflicts else '.')
          + bio_note)
    return {'verdict': verdict, 'english_videos': english_n, 'classified_videos': classified, 'share': round(share, 2),
            'bio': bio_det, 'account_language_setting': account_language, 'evidence': ev.strip(), 'samples': samples[:8]}

def script_json(page, script_id):
    m = re.search(r'<script[^>]*id="%s"[^>]*>(.*?)</script>' % re.escape(script_id), page, re.S)
    if not m: return None
    try: return json.loads(m.group(1))
    except json.JSONDecodeError: return None

def parse_profile(page, handle):
    data = script_json(page, '__UNIVERSAL_DATA_FOR_REHYDRATION__')
    if not data: return None
    ud = ((data.get('__DEFAULT_SCOPE__') or {}).get('webapp.user-detail') or {})
    if ud.get('statusCode') not in (0, None): return {'unavailable': True, 'status': ud.get('statusCode'), 'msg': ud.get('statusMsg')}
    info = ud.get('userInfo') or {}
    user = info.get('user') or {}
    if not user.get('uniqueId'): return {'unavailable': True, 'status': ud.get('statusCode'), 'msg': ud.get('statusMsg') or 'no user'}
    stats = info.get('statsV2') or info.get('stats') or {}
    items = info.get('itemList') if isinstance(info.get('itemList'), list) else []
    bio_link = None
    bl = user.get('bioLink')
    if isinstance(bl, dict): bio_link = bl.get('link') or None
    return {
        'handle': user.get('uniqueId'), 'nickname': user.get('nickname') or None,
        'bio': user.get('signature') or '', 'bio_link': bio_link,
        'account_language': user.get('language') or None,
        'private': bool(user.get('privateAccount') or user.get('secret')),
        'followers': as_int(stats.get('followerCount')), 'hearts': as_int(stats.get('heartCount')),
        'videos': as_int(stats.get('videoCount')), 'item_list_count': len(items),
        'url': f'https://www.tiktok.com/@{user.get("uniqueId")}',
        'read_at': P.iso(), 'source': 'TikTok public profile page',
    }

def parse_oembed(page):
    """Official oEmbed. As of Nov 2026 the payload confirms type, provider, and embed_product_id; author_name and title are absent, and there is no view count."""
    try: data = json.loads(page)
    except json.JSONDecodeError: return None
    if not isinstance(data, dict): return None
    if data.get('type') != 'video' and not data.get('embed_product_id'): return None
    return {'title': data.get('title') or None, 'author_name': data.get('author_name'),
            'author_url': data.get('author_url'), 'embed_product_id': str(data.get('embed_product_id') or '') or None,
            'provider_name': data.get('provider_name')}

def parse_video(page, url):
    data = script_json(page, '__UNIVERSAL_DATA_FOR_REHYDRATION__')
    if not data: return None
    vd = ((data.get('__DEFAULT_SCOPE__') or {}).get('webapp.video-detail') or {})
    if vd.get('statusCode') not in (0, None): return {'unavailable': True, 'status': vd.get('statusCode')}
    item = ((vd.get('itemInfo') or {}).get('itemStruct') or {})
    if not item.get('id'): return {'unavailable': True, 'status': vd.get('statusCode')}
    stats = item.get('statsV2') or item.get('stats') or {}
    video = item.get('video') or {}
    cla = video.get('claInfo') if isinstance(video.get('claInfo'), dict) else {}
    cap = (cla.get('originalLanguageInfo') or {}).get('languageCode')
    if not cap:
        for row in cla.get('captionInfos') or []:
            if row.get('isOriginalCaption') and row.get('languageCode'):
                cap = row['languageCode']; break
    created = as_int(item.get('createTime'))
    published = datetime.fromtimestamp(created, timezone.utc).astimezone(P.ET).isoformat(timespec='seconds') if created else None
    aigc_desc = item.get('AIGCDescription') or ''
    return {
        'video_id': str(item.get('id')), 'url': url,
        'author': (item.get('author') or {}).get('uniqueId'),
        'title': (item.get('desc') or '')[:180], 'description': (item.get('desc') or '')[:600],
        'views': as_int(stats.get('playCount')), 'likes': as_int(stats.get('diggCount')),
        'comments': as_int(stats.get('commentCount')),
        'shares': as_int(stats.get('shareCount')),
        'published': published, 'length_s': as_int(video.get('duration')),
        'text_language': item.get('textLanguage') or None, 'caption_language': cap or None,
        'synthetic_label': bool(item.get('IsAigc') or item.get('ShowAIGC') or aigc_desc),
        'aigc_description': aigc_desc[:200] or None,
        'cover': video.get('cover') or video.get('originCover') or None,
        'labels': item.get('diversificationLabels') if isinstance(item.get('diversificationLabels'), list) else [],
        'source': 'TikTok public video page', 'read_at': P.iso(),
    }

def age_days(iso_s):
    return (P.now() - datetime.fromisoformat(iso_s)).days

def niche_hit(username, description):
    blob = f'{username or ""} {description or ""}'
    return bool(USER_RE.search(username or '') or NICHE_RE.search(blob) or P.AI_TELLS.search(blob))

class Budget:
    def __init__(self): self.n = 0; self.stopped = False
    def fetch(self, url, source, marker=None, timeout=25):
        host = url.split('/')[2]
        if 'tiktok.com' in host:
            if self.n >= TIKTOK_GET_CAP:
                self.stopped = True
                P.log_source(source, False, url, f'stopped at {TIKTOK_GET_CAP} TikTok GETs this pass')
                return None
            self.n += 1
        return P.fetch(url, source, marker=marker, timeout=timeout, cookies=False)

def run(cands, cand, act, scouts, yt_for_same_handle):
    b = Budget()
    limits = []
    read_at = P.iso()
    ranking_lists = []
    rankings = []
    for spec in cfg().get('rankings', []):
        page = b.fetch(spec['url'], 'HypeAuditor TikTok rankings', marker='__NUXT_DATA__', timeout=30)
        rows = parse_hypeauditor(page, spec['url'], spec.get('name'), spec.get('country'), read_at, spec.get('rows', 50)) if page else []
        detail = '' if rows else (P.SOURCES.get('HypeAuditor TikTok rankings', {}).get('detail') or 'no rows parsed')
        if not rows: limits.append(f'{spec.get("name")}: {detail}')
        ranking_lists.append({'name': spec.get('name'), 'url': spec['url'], 'country': spec.get('country'), 'rows': len(rows), 'detail': detail, 'read_at': read_at})
        rankings.extend(rows)
    act(scouts[4], f'Read {len(ranking_lists)} HypeAuditor TikTok rankings',
        f'{len(rankings)} rows' + (f' (expected {sum(s.get("rows", 50) for s in cfg().get("rankings", []))})' if rankings else ' — none parsed'),
        'ok' if rankings else 'blocked')

    by_user = {}
    for row in rankings:
        by_user.setdefault(row['username'].lower(), []).append(row)

    video_urls = {}   # handle -> [url]
    sources = {}      # handle -> [str]
    niches = {}

    def add_handle(handle, source, niche=None):
        h = (handle or '').lstrip('@').strip('.').lower()
        if not h or h in SKIP_HANDLES: return
        sources.setdefault(h, [])
        if source not in sources[h]: sources[h].append(source)
        if niche and h not in niches: niches[h] = niche

    def add_videos(found, source):
        for h, urls in found.items():
            add_handle(h, source)
            bucket = video_urls.setdefault(h, [])
            for u in urls:
                if u not in bucket: bucket.append(u)

    article_reports = []
    for art in cfg().get('articles', []):
        page = b.fetch(art['url'], 'TikTok niche articles', marker=art.get('marker'), timeout=25)
        status = 'reachable' if page else (P.SOURCES.get('TikTok niche articles', {}).get('detail') or 'unavailable')
        handles, found = extract_refs(page or '')
        for h in handles: add_handle(h, art['url'], art.get('niche'))
        add_videos(found, art['url'])
        article_reports.append({'url': art['url'], 'niche': art.get('niche'), 'status': 'ok' if page else 'blocked', 'detail': '' if page else status,
                                'handles': len(handles), 'video_urls': sum(len(v) for v in found.values())})
    act(scouts[5], f'Read {len(article_reports)} public niche pages',
        f'{sum(a["video_urls"] for a in article_reports)} video URLs, {len(sources)} handles mentioned',
        'ok' if any(a['status'] == 'ok' for a in article_reports) else 'blocked')

    for row in cfg().get('niche_handles', []):
        add_handle(row.get('handle'), row.get('source') or 'config niche handle', row.get('niche'))
    for sd in P.CFG.get('seeds', []):
        if sd.get('platform') == 'TikTok':
            add_handle(sd.get('handle'), 'seed: ' + (sd.get('reason') or ''), sd.get('niche'))

    promoted = 0
    for row in rankings:
        if niche_hit(row['username'], row.get('description') or ''):
            add_handle(row['username'], f'HypeAuditor {row["list"]} bio/name screen', 'faceless/AI screen')
            promoted += 1
            row['promoted'] = True
        else:
            row['promoted'] = False

    queries = P.CFG.get('web_search', {}).get('tiktok_queries', [])
    search_blocked = {'ddg': False, 'bing': False}
    search_video_hits = 0

    def search_html(query):
        if not search_blocked['ddg']:
            page = b.fetch('https://lite.duckduckgo.com/lite/?q=' + quote_plus(query), 'DuckDuckGo Lite search', marker='result-link', timeout=20)
            if page: return page, 'DuckDuckGo Lite'
            search_blocked['ddg'] = True
            detail = P.SOURCES.get('DuckDuckGo Lite search', {}).get('detail') or 'unavailable'
            if 'DuckDuckGo' not in ' '.join(limits): limits.append(f'DuckDuckGo Lite: {detail}')
        if not search_blocked['bing']:
            page = b.fetch('https://www.bing.com/search?q=' + quote_plus(query) + '&count=30', 'Bing web search', marker='<cite', timeout=20)
            if page: return page, 'Bing'
            search_blocked['bing'] = True
            detail = P.SOURCES.get('Bing web search', {}).get('detail') or 'unavailable'
            if not any(x.startswith('Bing ') for x in limits): limits.append(f'Bing: {detail}')
        return None, None

    for i, q in enumerate(queries):
        page, engine = search_html(q)
        handles, found = extract_refs(page or '')
        niche = q.replace('site:tiktok.com ', '')
        for h in handles: add_handle(h, f'web search "{q}"', niche)
        before = search_video_hits
        add_videos(found, f'web search "{q}"')
        search_video_hits += sum(len(v) for v in found.values())
        aid = scouts[i] if i < 4 else scouts[0]
        act(aid, f'Web search "{q}"',
            (f'{engine}: {len(handles)} profiles, {sum(len(v) for v in found.values())} video URLs' if page else 'no results (logged)'),
            'ok' if page else 'blocked')
        if page and not handles and not found and 'no TikTok URLs' not in ' '.join(limits):
            limits.append(f'{engine} returned a page for "{q}" but no tiktok.com profile or /video/ URL')

    # A couple of per-account video searches, then stop if the engines are not returning /video/ URLs.
    video_queries_tried = 0
    for h in list(video_urls)[:2] + [h for h in sources if h not in video_urls][:2]:
        if video_queries_tried >= 3 or (search_blocked['ddg'] and search_blocked['bing']): break
        if len(video_urls.get(h, [])) >= 6: continue
        video_queries_tried += 1
        q = f'site:tiktok.com/@{h}/video'
        page, engine = search_html(q)
        _, found = extract_refs(page or '')
        add_videos(found, f'web search "{q}"')
        if page and not found and video_queries_tried == 1:
            limits.append(f'{engine} site:tiktok.com/@handle/video search returned no video URLs (not bypassed)')
    if search_video_hits == 0 and video_queries_tried:
        limits.append('Recent-video search did not yield /video/ URLs; discovery fell back to links in public articles')

    ordered = sorted(sources, key=lambda h: (0 if video_urls.get(h) else 1, 0 if any(s.startswith('seed:') for s in sources[h]) else 1, -len(video_urls.get(h, [])), -len(sources[h])))
    deferred = ordered[MAX_PROFILES:]
    ordered = ordered[:MAX_PROFILES]
    if deferred: limits.append(f'{len(deferred)} handles deferred (profile cap {MAX_PROFILES})')

    profiles = {}
    screened = []
    english = []

    def remember_profile(h):
        if h in profiles: return profiles[h]
        page = b.fetch(f'https://www.tiktok.com/@{h}', 'TikTok public profile pages', marker='webapp.user-detail', timeout=25)
        if not page:
            profiles[h] = None
            return None
        profiles[h] = parse_profile(page, h)
        return profiles[h]

    sb_note = {'done': False, 'text': None}
    def socialblade_note():
        if not sb_note['done']:
            sb_note['done'] = True
            page = b.fetch('https://socialblade.com/tiktok/user/zachking', 'Social Blade (TikTok)', marker='followers', timeout=20)
            if page: sb_note['text'] = 'Social Blade TikTok page loaded; its YouTube-style daily view table is not on this page, so it was not used as a view count'
            else: sb_note['text'] = 'Social Blade daily table unavailable this cycle'
        return sb_note['text']

    for h in ordered:
        if b.stopped: break
        prof = remember_profile(h)
        if not prof or prof.get('unavailable'):
            screened.append({'handle': '@' + h, 'reason': 'profile_unavailable', 'sources': sources[h][:4],
                             'detail': (prof or {}).get('msg') or P.SOURCES.get('TikTok public profile pages', {}).get('detail') or 'profile not readable'})
            continue
        if prof.get('private'):
            screened.append({'handle': '@' + prof['handle'], 'reason': 'private_account', 'sources': sources[h][:4]})
            continue
        urls = video_urls.get(h, [])[:MAX_URLS_PER_ACCOUNT]
        videos, unread = [], []
        for url in urls:
            if b.stopped: break
            oe_page = b.fetch('https://www.tiktok.com/oembed?url=' + quote_plus(url), 'TikTok oEmbed', marker='"type":"video"', timeout=20)
            oe = parse_oembed(oe_page) if oe_page else None
            page = b.fetch(url, 'TikTok public video pages', marker='webapp.video-detail', timeout=25)
            if not page:
                unread.append(url + ' (page not readable)')
                continue
            v = parse_video(page, url)
            if not v or v.get('unavailable'):
                unread.append(url + f' (video page status {((v or {}).get("status"))})')
                continue
            if (v.get('author') or '').lower() != prof['handle'].lower():
                unread.append(url + f' (author @{v.get("author")} does not match)')
                continue
            if oe and oe.get('embed_product_id') and oe['embed_product_id'] != v['video_id']:
                unread.append(url + f' (oEmbed id {oe["embed_product_id"]} does not match)')
                continue
            if oe and oe.get('author_url') and prof['handle'].lower() not in oe['author_url'].lower():
                unread.append(url + ' (oEmbed author does not match)')
                continue
            v['oembed'] = ({k: oe[k] for k in ('title', 'author_name', 'author_url')} if oe else None)
            v['oembed_read_at'] = P.iso() if oe else None
            v['detector'] = detect_lang(v.get('description') or '')
            v['discovered_from'] = next((s for s in sources[h] if 'tiktok.com/@' not in s), sources[h][0] if sources[h] else None)
            if v.get('comments') is not None: v['comments_display'] = f'{v["comments"]:,}'
            videos.append(v)
        videos.sort(key=lambda v: v.get('published') or '', reverse=True)
        lang = language_verdict(prof.get('bio') or '', prof.get('account_language'), videos)
        print(f'tiktok @{prof["handle"]} followers={prof.get("followers")} videos_found={len(videos)} lang={lang["verdict"]}', file=sys.stderr, flush=True)
        if lang['verdict'] != 'english':
            screened.append({'handle': '@' + prof['handle'], 'name': prof.get('nickname'), 'reason': 'not_english' if lang['verdict'] == 'not_english' else 'language_unverified',
                             'followers': prof.get('followers'), 'videos_on_profile': prof.get('videos'), 'video_urls_found': len(urls),
                             'unreadable_videos': unread[:4],
                             'language': {k: lang[k] for k in ('verdict', 'evidence', 'bio', 'account_language_setting', 'english_videos', 'classified_videos')},
                             'sources': sources[h][:4], 'profile_url': prof['url']})
            continue
        measured = [v for v in videos if v.get('views') is not None and v.get('likes') is not None and v.get('published')]
        recent = [v for v in measured if age_days(v['published']) <= P.QUAL['max_days_since_upload']]
        if len(recent) >= P.QUAL['tiktok_min_videos']:
            sample, coverage = recent[:P.QUAL['tiktok_min_videos']], 'full'
        else:
            sample, coverage = measured[:P.QUAL['tiktok_min_videos']], ('partial' if measured else 'none')
        views = [v['views'] for v in sample if v.get('views') is not None]
        median = int(statistics.median(views)) if views else None
        activity = bool(recent)
        newest = sample[0]['published'] if sample else (videos[0]['published'] if videos else None)
        if coverage == 'full':
            coverage_note = f'{len(sample)} public videos with views and likes, all dated within {P.QUAL["max_days_since_upload"]} days'
        elif sample:
            coverage_note = (f'partial: {len(sample)} verified public video(s), {len(recent)} dated within {P.QUAL["max_days_since_upload"]} days '
                             f'(a full qualifier needs {P.QUAL["tiktok_min_videos"]} that recent). Profile itemList length was {prof["item_list_count"]}.')
        else:
            coverage_note = f'partial: no public /video/ URL with a readable playCount. Profile lists {prof.get("videos")} videos but itemList length was {prof["item_list_count"]}.'
        frames, per_video, checked_videos = [], [], 0
        for v in sample:
            if not v.get('cover'): per_video.append([]); continue
            feats = P.faces_in(v['cover'], cookies=False)
            if feats is None:
                per_video.append([]); continue
            frames.append(len(feats)); per_video.append(feats); checked_videos += 1
        c = cand(prof['handle'], 'TikTok', name=prof.get('nickname'), niche=niches.get(h), url=prof['url'])
        c['name'] = prof.get('nickname')
        c['niche'] = niches.get(h) or c.get('niche')
        c['url'] = prof['url']
        c['description'] = (prof.get('bio') or '') + (('\n' + prof['bio_link']) if prof.get('bio_link') else '')
        c['found_by'] = list(dict.fromkeys((c.get('found_by') or []) + [scouts[6], scouts[7]]))
        for s in sources[h][:6]:
            if s not in c['signals']: c['signals'].append(s)
        if any(s.startswith('seed:') for s in sources[h]): c['seed'] = True
        if prof.get('followers') is not None:
            c['followers'] = {'value': prof['followers'], 'display': f'{prof["followers"]:,}', 'source': prof['source'], 'url': prof['url'], 'read_at': prof['read_at']}
        c['tiktok'] = {k: prof[k] for k in ('followers', 'hearts', 'videos', 'nickname', 'bio', 'bio_link', 'url', 'read_at', 'source', 'item_list_count', 'account_language')}
        c['recent'] = sample
        c['median_views'] = median
        c['best_short_floor'] = max([v['views'] or 0 for v in sample], default=0)
        c['coverage'] = coverage
        c['coverage_note'] = coverage_note
        c['activity_verified'] = activity
        c['language'] = lang
        c['latest_upload'] = newest
        hits = by_user.get(prof['handle'].lower()) or []
        if hits:
            primary = next((r for r in hits if r.get('country') in (None, '')), hits[0])
            c['hypeauditor'] = {'lists': [r['list'] for r in hits], 'followers': primary.get('followers'),
                                'avg_views_30d': primary.get('avg_views_30d'), 'avg_likes_30d': primary.get('avg_likes_30d'),
                                'avg_comments_30d': primary.get('avg_comments_30d'), 'avg_shares_30d': primary.get('avg_shares_30d'),
                                'last_media_time': primary.get('last_media_time'), 'source_url': primary.get('source_url'),
                                'read_at': primary.get('read_at'),
                                'note': 'HypeAuditor public ranking averages for this username. Not used as the per-video median or as the activity check.'}
        else:
            c['hypeauditor'] = None
        c['face_frames'] = {'checked': len(frames), 'with_face': sum(1 for n in frames if n > 0), 'videos': checked_videos,
                            'max_videos_same_person': P.recurring_person(per_video) if any(per_video) else 0,
                            'note': 'One public cover image per verified video. Not YouTube hq1–hq3 frames.'}
        for v in sample:
            v.pop('cover', None)
        rates = [v['likes'] / v['views'] for v in sample if v.get('likes') is not None and v.get('views')]
        c['like_rate'] = round(statistics.median(rates), 4) if rates else None
        withc = sum(1 for v in sample if (v.get('comments') or 0) > 0)
        reasons, verdict = [], 'pass'
        if c['like_rate'] is None: verdict = 'unknown'; reasons.append('likes hidden or unreadable')
        elif c['like_rate'] < 0.005: verdict = 'suspicious'; reasons.append(f'very low like rate {c["like_rate"]:.2%} (possible bought views)')
        elif c['like_rate'] > 0.25: verdict = 'suspicious'; reasons.append(f'abnormally high like rate {c["like_rate"]:.2%} (possible bought likes)')
        else: reasons.append(f'median like rate {c["like_rate"]:.2%} is in the normal 0.5–25% band')
        if sample and withc < 2: verdict = 'suspicious' if verdict == 'pass' else verdict; reasons.append(f'comments present on only {withc}/{len(sample)} sampled videos')
        elif sample: reasons.append(f'comments present on {withc}/{len(sample)} sampled videos')
        c['socialblade'] = None
        reasons.append(socialblade_note())
        c['engagement_check'] = {'verdict': verdict, 'reasons': reasons, 'checked_at': P.iso(), 'by': scouts[6]}
        c['notes'] = ' '.join([
            coverage_note,
            lang['evidence'],
            'Newest verified upload ' + newest + '.' if newest else 'No verified upload date.',
            (f'HypeAuditor 30-day avg views {c["hypeauditor"]["avg_views_30d"]:,}.' if c.get('hypeauditor') and c['hypeauditor'].get('avg_views_30d') is not None else 'Not in the HypeAuditor top-50 lists read this pass.'),
            'Web search was not a source of /video/ URLs this pass.' if search_video_hits == 0 else '',
        ]).strip()
        english.append(c)

    act(scouts[6], 'Read public video pages and oEmbed',
        f'{b.n} TikTok GETs, {sum(len(c.get("recent") or []) for c in english)} verified videos on {len(english)} English accounts',
        'blocked' if b.stopped else 'ok')

    got = []
    for yc in yt_for_same_handle or []:
        if b.stopped: break
        h = (yc.get('handle') or '').lstrip('@').lower()
        if not h: continue
        prof = remember_profile(h)
        if not prof or prof.get('unavailable') or prof.get('followers') is None: continue
        match = (prof.get('nickname') or '').strip().lower() == (yc.get('name') or '').strip().lower()
        yc['tiktok_same_handle'] = {'followers': prof['followers'], 'hearts': prof.get('hearts'), 'videos': prof.get('videos'),
                                    'nickname': prof.get('nickname'), 'url': prof['url'], 'read_at': prof['read_at'], 'source': prof['source'],
                                    'nickname_matches_youtube_name': match,
                                    'note': 'Same handle exists on TikTok; ownership is confirmed only if the display name matches'}
        got.append(f'{yc["handle"]}: {prof["followers"]:,} followers' + (' (name matches)' if match else ' (different name — may be another owner)'))
    for url, name, marker in (('https://www.tiktok.com/tag/redditstories', 'TikTok tag pages', '"uniqueId"'),
                              ('https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en', 'TikTok Creative Center', 'hashtag_name')):
        b.fetch(url, name, marker=marker, timeout=20)
    probe = ', '.join(f'{n}: {P.SOURCES[n]["status"]}' for n in ('TikTok tag pages', 'TikTok Creative Center') if n in P.SOURCES)
    act(scouts[7], 'Screened language and checked same-handle profiles',
        ('; '.join(got) if got else 'no same-handle TikTok profiles readable') + (f'. {probe}' if probe else ''),
        'ok')

    non_en = sum(1 for s in screened if s['reason'] == 'not_english')
    unver = sum(1 for s in screened if s['reason'] == 'language_unverified')
    limits.append(f'Profile itemList does not list recent videos; per-video views exist only for URLs found on public pages.')
    if b.stopped: limits.append(f'Stopped after {TIKTOK_GET_CAP} TikTok GETs')
    # Rankings are evidence. Keep the fields the site and the PR summary need; drop nothing measured.
    return {
        'read_at': read_at,
        'rankings_count': len(rankings),
        'ranking_lists': ranking_lists,
        'rankings': rankings,
        'promoted_from_rankings': promoted,
        'articles': article_reports,
        'english_verified': len(english),
        'screened_count': len(screened),
        'screened_not_english': non_en,
        'screened_language_unverified': unver,
        'screened': screened,
        'video_urls_from_search': search_video_hits,
        'tiktok_gets': b.n,
        'limits': limits,
        'rules': 'Scored like YouTube. English-only. coverage=full only with 6 verified videos dated within 14 days. HypeAuditor avg views are not the median.',
    }
