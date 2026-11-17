# Kumi social agents (updated 2026-11-17)

Repo layout (public GitHub repo kumi-social, working branch claude/project-thread-0ts6vo):
- pipeline/ — svgcards.py (SVG cards, current style), svg2png.js, publish.py; render.py/card.html = old W46-start style, not used
- weeks/<YYYY-Www>/week.json + <slug>.svg (source, editable) + <slug>.png (what is published)
- queue.json — every post ever scheduled, with approved/status/ids
- used.json — phrase ids already posted or drafted (never repeat within 6 months)

## Weekly batch (scheduled task, Sunday ~09:45 Israel)
1. Read /mnt/project-files/content/word-partners-content.json and used.json. Pick 5 posts for Wed/Thu/Sat/Mon/Tue,
   mixing rubrics from the Notion schema: «Как сказать…?», «Ловушка», «Квиз», «Подборка» (+ «Знакомство с Kumi» now and then).
   Prefer items with a typical Russian-calque mistake. Only phrases, translations and example sentences from the base.
2. Captions in Elena's voice (see W46 texts in queue.json): short lines, ❌/✅, one example + Russian translation,
   question or «Сохраните», 5 hashtags. «Kumi»/326/«первые 30 бесплатно» in at most 2 of 5. threads_text ≤ 500 chars, no hashtags.
   No politics, no country comparisons, «для тех, кто говорит по-русски», never «для русских».
3. week.json with layout + card per post (layouts: swap, versus, pair, quiz, list; vary them and the colours).
   python3 pipeline/svgcards.py weeks/<w>/week.json && node pipeline/svg2png.js weeks/<w>; look at every PNG, fix overflow.
4. Append to queue.json with approved=false, status=draft. Commit + push.
5. Copy SVG+PNG+captions to /mnt/project-files/smm/<week>/ and show Elena a contact sheet + texts in the project thread; ask for «Ок».

## Approval
Only Elena's own message saying Ок (or listing which posts are OK / edits) counts. Apply edits and re-show.
On approval: approved=true in queue.json; add a row per post to Notion «Контент для соцсетей (одобренное)»
(collection://16262d91-f3b5-4dd0-aa04-d98efe4bbd95): Статус «Всё одобрено», both checkboxes, Дата одобрения, Рубрика, Уровень,
Фраза, Площадки, Порядок, caption + image (raw GitHub URL) + SVG link in the body. Then schedule one one-shot publish per post.

## Publish (one-shot per approved post, at publish_at = 17:00 UTC ≈ 19:00 Israel)
git pull; MEDIA_BASE=https://raw.githubusercontent.com/altmanhellen/kumi-social/<branch> SLUGS=<slug> python3 pipeline/publish.py queue.json;
commit queue.json; set the Notion row to «Опубликовано» with date + link; report failures in the thread.

## Analyst (with the weekly run)
Threads insights (graph.threads.net) + IG insights when available; one short note on what to make more of.
