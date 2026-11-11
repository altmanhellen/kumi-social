"""Publish approved posts whose time has come.
Auth: tokens are injected by the environment's network secrets as 'Authorization: Bearer ...'
     for graph.instagram.com, graph.threads.net and graph.facebook.com (no tokens in code or env). Env: MEDIA_BASE (public base URL of the images, e.g. raw GitHub URL).
queue.json: list of posts with fields slug, image (file name), caption, threads_text, publish_at (ISO UTC),
            approved (bool, set only after Elena's OK), status ('pending'|'published'|'failed'), ids.
            Facebook Page results are kept apart: facebook_status ('published'|'failed'),
            facebook_post_id or facebook_error. A post with facebook_post_id is never sent to Facebook again.
Usage: python3 publish.py queue.json [--dry]
Only posts with approved==true and publish_at <= now are published. Nothing else is touched.
"""
import json, os, sys, time, urllib.request, urllib.parse, datetime
IG = 'https://graph.instagram.com/v21.0'
TH = 'https://graph.threads.net/v1.0'
FB_PAGE_ID = '1471238842734444'  # Facebook Page "Kumi English App"
FB_PHOTOS = f'https://graph.facebook.com/v27.0/{FB_PAGE_ID}/photos'

def call(url, params, method='POST'):
    params = {k: v for k, v in params.items() if not (k == 'access_token' and not v)}
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url if method == 'POST' else url + '?' + data.decode(), data=data if method == 'POST' else None, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def wait_ready(base, cid, token, field='status_code'):
    for _ in range(30):
        s = call(f'{base}/{cid}', {'fields': field, 'access_token': token}, 'GET')
        if s.get(field) in ('FINISHED', None): return
        if s.get(field) == 'ERROR': raise RuntimeError(f'container {cid} error')
        time.sleep(5)

def post_instagram(img_url, caption):
    t = os.environ.get('IG_TOKEN', '')
    c = call(f'{IG}/me/media', {'image_url': img_url, 'caption': caption, 'access_token': t})
    wait_ready(IG, c['id'], t)
    return call(f'{IG}/me/media_publish', {'creation_id': c['id'], 'access_token': t})['id']

def post_threads(img_url, text):
    t = os.environ.get('THREADS_TOKEN', '')
    c = call(f'{TH}/me/threads', {'media_type': 'IMAGE', 'image_url': img_url, 'text': text, 'access_token': t})
    wait_ready(TH, c['id'], t, 'status')
    return call(f'{TH}/me/threads_publish', {'creation_id': c['id'], 'access_token': t})['id']

def post_facebook(img_url, caption):
    # No access_token: the network secret for graph.facebook.com adds the Authorization header.
    r = call(FB_PHOTOS, {'url': img_url, 'message': caption})
    return r.get('post_id') or r['id']

def main(qpath, dry=False):
    q = json.load(open(qpath)); now = datetime.datetime.now(datetime.timezone.utc)
    base = os.environ.get('MEDIA_BASE', '').rstrip('/')
    for p in q:
        if not p.get('approved'):
            if dry: print('skip (not approved)', p['slug'])
            continue
        if datetime.datetime.fromisoformat(p['publish_at']) > now:
            if dry: print('skip (not due yet)', p['slug'], p['publish_at'])
            continue
        need_main = p.get('status') != 'published'
        need_fb = 'facebook_post_id' not in p
        if not need_main and not need_fb: continue
        url = f"{base}/{p['image']}"
        if dry:
            ids = p.get('ids', {})
            print('would publish', p['slug'], url)
            if need_main:
                if 'instagram' not in ids: print(f'  instagram: POST {IG}/me/media fields=image_url,caption image_url={url} -> POST {IG}/me/media_publish')
                if 'threads' not in ids: print(f'  threads:   POST {TH}/me/threads fields=media_type,image_url,text image_url={url} -> POST {TH}/me/threads_publish')
            if need_fb: print(f'  facebook:  POST {FB_PHOTOS} fields=url,message url={url}')
            continue
        if need_main:
            ids = p.setdefault('ids', {})
            try:
                if 'instagram' not in ids: ids['instagram'] = post_instagram(url, p['caption'])
                if 'threads' not in ids: ids['threads'] = post_threads(url, p['threads_text'])
                p['status'] = 'published'; p['published_at'] = now.isoformat()
            except Exception as e:
                p['status'] = 'failed'; p['error'] = str(e)[:500]
            json.dump(q, open(qpath, 'w'), ensure_ascii=False, indent=1)
        if need_fb:
            try:
                p['facebook_post_id'] = post_facebook(url, p['caption'])
                p['facebook_status'] = 'published'; p.pop('facebook_error', None)
            except Exception as e:
                p['facebook_status'] = 'failed'; p['facebook_error'] = str(e)[:500]
            json.dump(q, open(qpath, 'w'), ensure_ascii=False, indent=1)
        print(p['slug'], p.get('status'), p.get('ids', {}), 'facebook:', p.get('facebook_status'), p.get('facebook_post_id', ''))

if __name__ == '__main__':
    main(sys.argv[1], '--dry' in sys.argv)
