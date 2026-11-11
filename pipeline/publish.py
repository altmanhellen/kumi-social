"""Publish approved posts whose time has come.
Auth: tokens are injected by the environment's network secrets as 'Authorization: Bearer ...'
     for graph.instagram.com, graph.threads.net and graph.facebook.com (no tokens in code or env).
Env: MEDIA_BASE (public base URL of the images, e.g. raw GitHub URL).
     ONLY  optional comma list of platforms to handle in this run (instagram,threads,facebook).
     SLUGS optional comma list of post slugs to handle in this run.
queue.json: list of posts with fields slug, image (file name), caption, threads_text, publish_at (ISO UTC),
            approved (bool, set only after Elena's OK), status, ids.
Each platform is handled on its own:
  status_instagram / status_threads / status_facebook  ('published' | 'failed')
  error_instagram  / error_threads  / error_facebook   (last error, removed after success)
  ids.instagram, ids.threads, facebook_post_id         (post ids)
A failure on one platform is recorded and does not stop the others or the script.
A platform that already has an id is never posted again.
status (overall): 'published' when all platforms have an id, 'partial' when some do, 'failed' when none.
Usage: python3 publish.py queue.json [--dry]
Only posts with approved==true and publish_at <= now are published. Nothing else is touched.
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error, datetime
# Instagram goes through the Facebook Graph API: the IG Business account is linked to the Facebook Page,
# and the graph.facebook.com network secret (page token) already works for the Page posts.
IG_USER_ID = '17841412983905507'  # @kumi.english.app
IG = 'https://graph.facebook.com/v27.0'
TH = 'https://graph.threads.net/v1.0'
FB_PAGE_ID = '1471238842734444'  # Facebook Page "Kumi English App"
FB_PHOTOS = f'https://graph.facebook.com/v27.0/{FB_PAGE_ID}/photos'
PLATFORMS = ('instagram', 'threads', 'facebook')
THREADS_MAX = 500  # Threads API rejects longer text (code 100)

def call(url, params, method='POST'):
    params = {k: v for k, v in params.items() if not (k == 'access_token' and not v)}
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url if method == 'POST' else url + '?' + data.decode(), data=data if method == 'POST' else None, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')[:400]
        raise RuntimeError(f'HTTP {e.code}: {body}') from None

def wait_ready(base, cid, token, field='status_code'):
    for _ in range(30):
        s = call(f'{base}/{cid}', {'fields': field, 'access_token': token} if token else {'fields': field}, 'GET')
        if s.get(field) in ('FINISHED', None): return
        if s.get(field) == 'ERROR': raise RuntimeError(f'container {cid} error')
        time.sleep(5)

def post_instagram(img_url, caption):
    # No access_token: the graph.facebook.com network secret adds the Authorization header.
    c = call(f'{IG}/{IG_USER_ID}/media', {'image_url': img_url, 'caption': caption})
    wait_ready(IG, c['id'], None)
    return call(f'{IG}/{IG_USER_ID}/media_publish', {'creation_id': c['id']})['id']

def post_threads(img_url, text):
    t = os.environ.get('THREADS_TOKEN', '')
    c = call(f'{TH}/me/threads', {'media_type': 'IMAGE', 'image_url': img_url, 'text': text, 'access_token': t})
    wait_ready(TH, c['id'], t, 'status')
    return call(f'{TH}/me/threads_publish', {'creation_id': c['id'], 'access_token': t})['id']

def post_facebook(img_url, caption):
    # No access_token: the network secret for graph.facebook.com adds the Authorization header.
    r = call(FB_PHOTOS, {'url': img_url, 'message': caption})
    return r.get('post_id') or r['id']

def get_id(p, plat):
    if plat == 'facebook': return p.get('facebook_post_id')
    return p.get('ids', {}).get(plat)

def set_id(p, plat, pid):
    if plat == 'facebook': p['facebook_post_id'] = pid
    else: p.setdefault('ids', {})[plat] = pid

def migrate(p):
    # Older entries kept Facebook as facebook_status/facebook_error.
    if 'facebook_status' in p: p.setdefault('status_facebook', p.pop('facebook_status'))
    if 'facebook_error' in p: p.setdefault('error_facebook', p.pop('facebook_error'))

def overall(p):
    done = sum(1 for x in PLATFORMS if get_id(p, x))
    return 'published' if done == len(PLATFORMS) else ('partial' if done else 'failed')

def send(plat, p, url):
    if plat == 'instagram': return post_instagram(url, p['caption'])
    if plat == 'threads':
        if len(p['threads_text']) > THREADS_MAX:
            raise RuntimeError(f"threads_text is {len(p['threads_text'])} characters, Threads allows {THREADS_MAX}; not sent")
        return post_threads(url, p['threads_text'])
    return post_facebook(url, p['caption'])

def describe(plat, url):
    if plat == 'instagram': return f'POST {IG}/me/media fields=image_url,caption image_url={url} -> POST {IG}/me/media_publish'
    if plat == 'threads': return f'POST {TH}/me/threads fields=media_type,image_url,text image_url={url} -> POST {TH}/me/threads_publish'
    return f'POST {FB_PHOTOS} fields=url,message url={url}'

def main(qpath, dry=False):
    q = json.load(open(qpath)); now = datetime.datetime.now(datetime.timezone.utc)
    base = os.environ.get('MEDIA_BASE', '').rstrip('/')
    only = [x.strip() for x in os.environ.get('ONLY', '').split(',') if x.strip()] or list(PLATFORMS)
    slugs = {x.strip() for x in os.environ.get('SLUGS', '').split(',') if x.strip()}
    for x in only:
        if x not in PLATFORMS: sys.exit(f'unknown platform in ONLY: {x}')
    for p in q:
        if slugs and p['slug'] not in slugs: continue
        if not p.get('approved'):
            if dry: print('skip (not approved)', p['slug'])
            continue
        if datetime.datetime.fromisoformat(p['publish_at']) > now:
            if dry: print('skip (not due yet)', p['slug'], p['publish_at'])
            continue
        todo = [x for x in only if not get_id(p, x)]
        if not todo: continue
        url = f"{base}/{p['image']}"
        if dry:
            print('would publish', p['slug'], url)
            for x in todo: print(f'  {x}: {describe(x, url)}')
            if 'threads' in todo and len(p['threads_text']) > THREADS_MAX:
                print(f"  WARNING threads_text is {len(p['threads_text'])} characters (max {THREADS_MAX}), Threads will be skipped as failed")
            continue
        migrate(p)
        for x in todo:
            try:
                set_id(p, x, send(x, p, url))
                p[f'status_{x}'] = 'published'; p.pop(f'error_{x}', None)
            except Exception as e:
                p[f'status_{x}'] = 'failed'; p[f'error_{x}'] = str(e)[:500]
            p['status'] = overall(p)
            if p['status'] == 'published': p.setdefault('published_at', now.isoformat())
            json.dump(q, open(qpath, 'w'), ensure_ascii=False, indent=1)
            print(p['slug'], x, p[f'status_{x}'], get_id(p, x) or p.get(f'error_{x}', ''))

if __name__ == '__main__':
    main(sys.argv[1], '--dry' in sys.argv)
