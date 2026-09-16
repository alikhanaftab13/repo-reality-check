"""Core analysis logic for GitHub Repo Reality Check.

Pure functions, independent of the Streamlit UI, so they can be tested and
reused (e.g. from a future API endpoint) without dragging in the UI layer.

All GitHub calls go through `_get()`, which accepts an optional token to
raise the rate limit from 60/hour (unauthenticated) to 5000/hour.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

API_ROOT = "https://api.github.com"
TIMEOUT = 15


class RepoCheckError(Exception):
    """Raised for user-facing failures: bad input, 404, rate limit, etc."""


def _headers(token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(path: str, token: str | None, params: dict | None = None) -> requests.Response:
    try:
        resp = requests.get(f"{API_ROOT}{path}", headers=_headers(token), params=params, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise RepoCheckError(f"Network error contacting GitHub: {exc}") from exc

    if resp.status_code == 404:
        raise RepoCheckError("Repository not found (check the owner/name spelling, or it may be private).")
    if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
        reset = resp.headers.get("X-RateLimit-Reset")
        reset_str = ""
        if reset:
            reset_str = f" Resets at {datetime.fromtimestamp(int(reset), tz=timezone.utc).strftime('%H:%M UTC')}."
        raise RepoCheckError(
            "GitHub API rate limit hit."
            + (" Add a personal access token in the sidebar to raise the limit to 5000/hour." if not token else "")
            + reset_str
        )
    if resp.status_code >= 400:
        raise RepoCheckError(f"GitHub API error {resp.status_code}: {resp.text[:200]}")
    return resp


def parse_repo_input(text: str) -> tuple[str, str]:
    """Accepts 'owner/repo', a full https://github.com/owner/repo URL, or
    the same with a trailing slash / .git / extra path segments."""
    text = text.strip()
    if not text:
        raise RepoCheckError("Enter a repository, e.g. torvalds/linux")
    text = text.removeprefix("https://").removeprefix("http://").removeprefix("github.com/")
    text = text.removesuffix(".git").removesuffix("/")
    parts = [p for p in text.split("/") if p]
    if len(parts) < 2:
        raise RepoCheckError("Expected the form owner/repo (e.g. torvalds/linux) or a full GitHub URL.")
    return parts[0], parts[1]


def _paginated_count(path: str, token: str | None, params: dict) -> int:
    """Reads the total count off the `last` page in the Link header instead
    of walking every page -- one request instead of N for large repos."""
    params = {**params, "per_page": 1}
    resp = _get(path, token, params=params)
    link = resp.headers.get("Link", "")
    if 'rel="last"' not in link:
        return len(resp.json())
    for part in link.split(","):
        if 'rel="last"' in part:
            url = part.split(";")[0].strip(" <>")
            qs = url.split("page=")[-1].split("&")[0]
            return int(qs)
    return len(resp.json())


def _days_ago(iso_ts: str) -> int:
    ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - ts).days


@dataclass
class Signal:
    label: str
    verdict: str  # "good" | "warn" | "bad" | "info"
    detail: str


@dataclass
class RepoReport:
    full_name: str
    description: str
    url: str
    is_fork: bool
    parent_full_name: str | None
    stars: int
    forks: int
    open_issues: int
    license_name: str | None
    archived: bool
    pushed_at: str
    created_at: str
    contributors: int | None
    commits_last_90d: int | None
    open_prs: int | None
    oldest_open_pr_days: int | None
    signals: list[Signal] = field(default_factory=list)
    score: int = 0
    score_label: str = ""


def _score_and_label(signals: list[Signal]) -> tuple[int, str]:
    weights = {"good": 1, "warn": -1, "bad": -2, "info": 0}
    raw = sum(weights[s.verdict] for s in signals)
    scored = [s for s in signals if s.verdict != "info"]
    if not scored:
        return 50, "Not enough data"
    # normalize to 0-100 around a neutral midpoint of 50
    max_possible = len(scored) * 1
    min_possible = len(scored) * -2
    pct = (raw - min_possible) / (max_possible - min_possible)
    score = round(pct * 100)
    if score >= 75:
        label = "Looks healthy"
    elif score >= 50:
        label = "Mixed signals"
    elif score >= 25:
        label = "Several red flags"
    else:
        label = "Mostly red flags"
    return score, label


def check_repo(owner: str, name: str, token: str | None = None) -> RepoReport:
    repo = _get(f"/repos/{owner}/{name}", token).json()

    signals: list[Signal] = []

    is_fork = bool(repo.get("fork"))
    parent = repo.get("parent")
    parent_full_name = parent["full_name"] if parent else None

    created_at = repo["created_at"]
    pushed_at = repo["pushed_at"]
    created_to_pushed_days = (
        datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        - datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    ).days

    if is_fork:
        if created_to_pushed_days <= 1:
            signals.append(Signal(
                "Fork activity",
                "bad",
                f"This is a fork of {parent_full_name} that was pushed to only once, on the day it was "
                "created -- consistent with a snapshot/mirror with no independent work of its own, "
                "not an actively maintained project in its own right.",
            ))
        else:
            signals.append(Signal(
                "Fork activity",
                "info",
                f"This is a fork of {parent_full_name}, with {created_to_pushed_days} days between "
                "creation and its last push -- check the parent separately if you want the real, "
                "canonical project.",
            ))
        if parent:
            try:
                parent_repo = _get(f"/repos/{parent_full_name}", token).json()
                parent_pushed_days = _days_ago(parent_repo["pushed_at"])
                signals.append(Signal(
                    "Parent project",
                    "info",
                    f"Parent {parent_full_name}: {parent_repo['stargazers_count']:,} stars, "
                    f"last pushed {parent_pushed_days} days ago.",
                ))
            except RepoCheckError:
                pass

    days_since_push = _days_ago(pushed_at)
    if days_since_push <= 30:
        signals.append(Signal("Recent activity", "good", f"Last push was {days_since_push} days ago."))
    elif days_since_push <= 180:
        signals.append(Signal("Recent activity", "warn", f"Last push was {days_since_push} days ago -- slowing down."))
    else:
        signals.append(Signal("Recent activity", "bad", f"Last push was {days_since_push} days ago -- looks abandoned or finished."))

    if repo.get("archived"):
        signals.append(Signal("Archived", "bad", "GitHub itself marks this repository as archived (read-only, no longer maintained)."))

    if not repo.get("license"):
        signals.append(Signal("License", "warn", "No license file detected -- legally risky to depend on or build a business on."))
    else:
        signals.append(Signal("License", "good", f"Licensed under {repo['license']['name']}."))

    stars = repo["stargazers_count"]
    forks = repo["forks_count"]

    contributors: int | None = None
    try:
        contributors = _paginated_count(f"/repos/{owner}/{name}/contributors", token, {"anon": "false"})
        if contributors == 1:
            signals.append(Signal("Contributors", "warn", "Only 1 contributor -- a single point of failure (bus factor of one)."))
        elif contributors <= 3:
            signals.append(Signal("Contributors", "warn", f"Only {contributors} contributors."))
        else:
            signals.append(Signal("Contributors", "good", f"{contributors} contributors."))
    except RepoCheckError:
        pass

    commits_last_90d: int | None = None
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
        commits_last_90d = _paginated_count(f"/repos/{owner}/{name}/commits", token, {"since": since})
        if commits_last_90d == 0:
            signals.append(Signal("Commit velocity", "bad", "Zero commits in the last 90 days."))
        elif commits_last_90d < 5:
            signals.append(Signal("Commit velocity", "warn", f"Only {commits_last_90d} commits in the last 90 days."))
        else:
            signals.append(Signal("Commit velocity", "good", f"{commits_last_90d} commits in the last 90 days."))
    except RepoCheckError:
        pass

    open_prs: int | None = None
    oldest_open_pr_days: int | None = None
    try:
        pulls = _get(f"/repos/{owner}/{name}/pulls", token, {"state": "open", "per_page": 100, "sort": "created", "direction": "asc"}).json()
        open_prs = _paginated_count(f"/repos/{owner}/{name}/pulls", token, {"state": "open"})
        if pulls:
            oldest_open_pr_days = _days_ago(pulls[0]["created_at"])
            if oldest_open_pr_days > 180:
                signals.append(Signal(
                    "PR responsiveness",
                    "warn",
                    f"Oldest open PR has been waiting {oldest_open_pr_days} days -- maintainer may be slow to review/merge.",
                ))
    except RepoCheckError:
        pass

    star_fork_ratio_flag = forks > 0 and (stars / max(forks, 1)) > 200 and stars > 1000
    if star_fork_ratio_flag:
        signals.append(Signal(
            "Star-to-fork ratio",
            "warn",
            f"{stars:,} stars but only {forks:,} forks ({stars / max(forks,1):.0f}:1) -- unusually lopsided for "
            "a real developer tool; can be a genuine sign of a broad non-developer audience, or a sign of "
            "inflated/purchased stars. Not conclusive on its own.",
        ))

    score, score_label = _score_and_label(signals)

    return RepoReport(
        full_name=repo["full_name"],
        description=repo.get("description") or "",
        url=repo["html_url"],
        is_fork=is_fork,
        parent_full_name=parent_full_name,
        stars=stars,
        forks=forks,
        open_issues=repo["open_issues_count"],
        license_name=repo["license"]["name"] if repo.get("license") else None,
        archived=bool(repo.get("archived")),
        pushed_at=pushed_at,
        created_at=created_at,
        contributors=contributors,
        commits_last_90d=commits_last_90d,
        open_prs=open_prs,
        oldest_open_pr_days=oldest_open_pr_days,
        signals=signals,
        score=score,
        score_label=score_label,
    )
