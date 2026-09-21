# 2gether

A small social network built with Django and vanilla JavaScript — no frontend
framework, no CSS framework, no component library.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # optional: demo people, posts and activity
python manage.py runserver
```

Open http://127.0.0.1:8000. The seed command creates six accounts —
`mira`, `tomas`, `anjali`, `kenji`, `noor`, `erin` — all with the password
`gather2gether`. Demo imagery is generated locally by Pillow; nothing is
downloaded and no stock photography is used.

```bash
python manage.py test               # 18 tests: ownership, constraints, feeds
python manage.py createsuperuser    # /admin
```

## How it's put together

```
config/      settings, root URLs, friendly 403/404/500 handlers
accounts/    Profile, Follow, auth, profiles, people lists, search
posts/       Post, Like, Comment, feeds, composer endpoints
notifications/ Notification + the unread badge context processor
common/      image validation and downscaling, shared request helpers
templates/   base shell, partials, one file per page
static/css/  tokens → base → layout → components → pages
static/js/   one ES module per behaviour, all bound by delegation
```

**Data rules are enforced in the database, not just in views.** A like is
unique per (user, post); a follow edge is unique and cannot point at itself;
a post must carry text or an image. Each is a `UniqueConstraint` or
`CheckConstraint`, so a race or a stray script can't get around it.

**Authorization is checked server-side on every mutating view.** Only a post's
author can delete it. A comment can be removed by its author or by the author
of the post it sits under. Every mutation is `@login_required` and `@require_POST`.

**Uploads are re-encoded, never trusted.** `common/images.py` verifies the
bytes really are an image of an allowed type, rejects anything over 5 MB,
honours EXIF rotation, and downscales to a 1600px edge before saving.
Animated GIFs pass through so they aren't flattened to a single frame.

**Nothing reloads the page.** Likes, follows, comments, deletion, search,
pagination and the notification badge all go through `fetch()`. Comment
threads and feed pages are rendered by Django and returned as HTML, so the
markup for a post exists in exactly one file.

## The design

Two circles overlapping — that's the name, the logo, and the active-nav
marker. The palette is a cool sage ground with a single pine accent that
carries every action; vermilion appears in exactly one place, a like.
Typography is Bricolage Grotesque for display and Instrument Sans for
everything else.

Tokens live in `static/css/tokens.css`: colour, type scale, spacing, radius,
shadow and three motion durations — 170ms when a state flips, 300ms when
something appears, 520ms when a region changes.

Dark mode is designed separately rather than inverted: surfaces lighten as
they come forward, and borders carry structure that shadows can't. The choice
is stored in `localStorage` and applied before first paint, so there's no
flash. Until someone chooses, it follows the system setting.

Mobile isn't the desktop layout scaled down. Below 720px the left rail is
replaced by a compact top bar that steps aside as you scroll down and returns
the moment you scroll up, plus a five-slot bottom tab bar with the composer in
the centre. The composer opens as a bottom sheet. Safe-area insets are
respected top and bottom.

`prefers-reduced-motion` removes decorative animation — the entrance
sequence, the like burst, the skeleton sweep — while keeping the state changes
that tell you what happened.

## Notes for production

SQLite and `DEBUG=1` are development defaults. Before deploying: set
`DJANGO_SECRET_KEY` and `DJANGO_DEBUG=0` (which switches on HSTS, secure
cookies and SSL redirect), point `DATABASES` at Postgres, run
`collectstatic`, and serve `MEDIA_ROOT` from object storage rather than the
application server.
