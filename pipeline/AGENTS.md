# Kumi social agents

Repo layout (public GitHub repo kumi-social):
- pipeline/ — render.py, shot.js, publish.py, refresh_tokens.py, templates/card.html
- weeks/<YYYY-Www>/week.json + rendered PNGs
- queue.json — every post ever scheduled, with approved/status/ids
- used.json — phrase ids already posted (never repeat within 6 months)

## Editor + designer (weekly, Sunday 07:00 UTC)
1. Read /mnt/project-files/content/word-partners-content.json and used.json. Pick 5 B1–B2 items that have a common Russian-calque mistake (do/make, strong/heavy, etc.). Only phrases, translations and examples from the base; never invent examples.
2. For each write: hook (Russian phrase, lower case), bad (the typical wrong English calque), why (one sentence, ≤ 70 chars), caption (Instagram, format of /mnt/project-files/smm/posts/captions.md, «для тех, кто говорит по-русски», exact number 326, CTA in ≤ 1 of 3 posts strong), threads_text (same, no hashtags or one). No politics, no country comparisons.
3. publish_at: Mon/Tue/Wed/Thu/Sat 16:00 UTC (≈19:00 Israel). Render with render.py, commit week folder, append to queue.json with approved=false.
4. Post a preview (contact sheet PNG + captions) to Elena in the project thread and ask for «Ок».

## Approval
Only Elena's own message saying Ок (or listing which posts are OK) sets approved=true. Edits she asks for are applied and re-shown. Never publish an unapproved post.

## Publisher (daily 16:05 UTC)
git pull; python3 pipeline/publish.py queue.json; commit queue.json; report failures in the thread.
Posts go to Instagram, Threads and the Facebook Page "Kumi English App" (id 1471238842734444). Facebook results live in facebook_status / facebook_post_id / facebook_error, separate from Instagram/Threads; an entry with facebook_post_id is never re-posted. Check with --dry first.

## Analyst (Monday)
Pull IG/Threads insights for last week's posts (reach, saves, shares) + App Store Connect campaign numbers if Elena shares them; one short note on what to make more of.
