# GitHub Repo Reality Check

Paste a GitHub repo and get an instant, transparent report: is it a real,
actively maintained project, or a stale fork/snapshot riding on someone
else's stars? Built to catch exactly the kind of thing that took several
manual GitHub API checks to spot by hand — automated into one lookup.

## What it checks

- Whether it's a fork that only ever got one push (a snapshot, not a
  maintained project) — and if so, shows the real parent's stats instead
- Days since the last push, and whether it's archived
- License presence
- Contributor count (bus factor)
- Commit velocity over the last 90 days
- Open PR responsiveness (how long the oldest open PR has been waiting)
- Star-to-fork ratio outliers

Every finding is shown with its own plain-language explanation — this is a
transparent set of heuristics over public GitHub metadata, not a black-box
score, and it says so in the app.

## Run it locally

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Deploy for free (Streamlit Community Cloud)

1. Push this folder to a **public** GitHub repo (Community Cloud's free
   tier requires the source repo to be public).
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click **New app**, point it at this repo and `app.py`.
3. Deploy. You get a free `<something>.streamlit.app` URL — that's your
   live product, no server to manage, no cost.

## Real limitations, stated plainly

- Unauthenticated GitHub API calls are capped at 60/hour **per visitor's
  IP** — fine for personal use and early testing, but will bottleneck real
  traffic. Each visitor can paste in their own free personal access token
  (sidebar) to raise their own limit to 5000/hour; the app never stores or
  transmits it anywhere except directly to GitHub's API for that request.
- The score is a heuristic signal, not a certainty — always documented
  as such in the app itself, and the "How the score works" section shows
  exactly what it is and isn't.
- No payment/monetization is wired up yet. This is the MVP: validate that
  people actually find it useful before adding a paywall.

## Possible next steps (not built yet)

- A paid tier: bulk checks (paste many repos at once), or scheduled
  monitoring that alerts you if a dependency you rely on goes stale.
- Star-history velocity check (GitHub exposes `starred_at` timestamps via
  a special API media type) to flag sudden, suspicious star spikes —
  skipped for the MVP because it costs many more API calls per check on
  popular repos.
- A simple API endpoint (not just the Streamlit UI) for programmatic use.
