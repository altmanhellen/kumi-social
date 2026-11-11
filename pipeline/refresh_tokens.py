"""Refresh long-lived tokens (run monthly). Prints new tokens; Elena (or the env) must store them."""
import os, json, urllib.request
for name, url in (('IG_TOKEN', 'https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token='),
                  ('THREADS_TOKEN', 'https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token=')):
    t = os.environ.get(name)
    if t:
        with urllib.request.urlopen(url + t, timeout=30) as r:
            print(name, 'expires_in', json.load(r).get('expires_in'))
