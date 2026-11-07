#!/usr/bin/env python3
"""Offline checks for TikTok parsing and the English / partial gates."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tiktok
import pipeline as P

def test_extract_and_language():
    html = '''<a href="https://www.tiktok.com/@oneminmicro/video/7184000866746158338">x</a>
    <a href="https://www.tiktok.com/@Oneminmicro">profile</a> tiktok.com › @askthereddit › video › 7085114951253167402'''
    handles, videos = tiktok.extract_refs(html)
    assert 'oneminmicro' in handles and 'askthereddit' in videos
    assert videos['askthereddit'] == ['https://www.tiktok.com/@askthereddit/video/7085114951253167402']
    en = {'text_language': 'en', 'caption_language': 'en', 'description': 'Welcome Jesus into your home and share this blessing with your family today please', 'url': 'https://www.tiktok.com/@believerdaily/video/1'}
    en['detector'] = tiktok.detect_lang(en['description'])
    verdict = tiktok.language_verdict('Sharing Christ love daily. Join for scripture and faith stories with us', 'pt', [en])
    assert verdict['verdict'] == 'english', verdict
    fr = {'text_language': 'fr', 'caption_language': 'fr', 'description': 'Bienvenue dans cette histoire de chats triste pour toute la famille aujourd hui', 'url': 'u', 'detector': {'lang': 'fr', 'prob': 0.99}}
    assert tiktok.language_verdict('Je partage des histoires de chats tristes chaque jour avec ma famille', 'fr', [fr])['verdict'] == 'not_english'
    clash = {'text_language': 'pt', 'caption_language': None, 'description': 'Welcome Jesus into your home and share this blessing with your family today please and again tomorrow morning with everyone', 'url': 'u'}
    clash['detector'] = {'lang': 'en', 'prob': 0.99}
    mixed = tiktok.language_verdict('Sharing Christ love daily. Join for scripture and faith stories with us', 'pt', [clash])
    assert mixed['verdict'] == 'unverified', mixed
    short = {'text_language': 'en', 'caption_language': None, 'description': 'Stay unique ! #catsoftiktok #cat #aiart #ai #poorcat', 'url': 'u', 'detector': {'lang': 'ca', 'prob': 1.0}}
    assert tiktok.language_verdict('Cats and more cats every single day for you', 'en', [short])['verdict'] == 'english'

def test_oembed_reduced_payload():
    raw = '{"version":"1.0","type":"video","provider_name":"TikTok","embed_product_id":"7357355293254225184","embed_type":"video"}'
    oe = tiktok.parse_oembed(raw)
    assert oe['embed_product_id'] == '7357355293254225184' and oe['author_name'] is None

def test_partial_cannot_qualify():
    c = {'platform': 'TikTok', 'language': {'verdict': 'english'}, 'coverage': 'partial', 'coverage_note': 'partial: 1 verified',
         'activity_verified': False, 'recent': [{'views': 22800000, 'likes': 3500000}], 'median_views': 22800000,
         'faceless': {'verdict': 'yes'}, 'engagement_check': {'verdict': 'pass'}, 'followers': {'display': '733,294'}}
    assert P.qualify(c) is False
    assert any(x.startswith('partial:') for x in c['not_qualified_because'])
    assert any('activity' in x for x in c['not_qualified_because'])

def test_saved_pages():
    root = '/tmp/ttprobe'
    if not os.path.exists(os.path.join(root, 'hype.html')):
        print('skip saved-page fixtures'); return
    rows = tiktok.parse_hypeauditor(open(os.path.join(root, 'hype.html'), errors='replace').read(), 'https://hypeauditor.com/top-tiktok/', 'global', None, 'now', 50)
    assert len(rows) == 50 and rows[0]['followers'] and rows[0]['avg_views_30d']
    video = tiktok.parse_video(open(os.path.join(root, 'video.html'), errors='replace').read(), 'https://www.tiktok.com/@believerdaily/video/7244190446103104774')
    assert video['views'] == 22800000 and video['text_language'] == 'en' and video['author'] == 'believerdaily'
    profile = tiktok.parse_profile(open(os.path.join(root, 'profile.html'), errors='replace').read(), 'believerdaily')
    assert profile['followers'] == 733294 and profile['item_list_count'] == 0

if __name__ == '__main__':
    test_extract_and_language(); test_partial_cannot_qualify(); test_saved_pages()
    print('ok')
