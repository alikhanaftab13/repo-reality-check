"""Manual smoke test against real repos with known-in-advance answers,
from the actual investigation earlier in this session -- confirms the
scoring logic produces sane, correctly-directed results before trusting
it in the UI."""

from reality_check import check_repo

CASES = [
    ("Autom8AI", "Open-Higgsfield-AI"),   # expect: flagged stale snapshot fork
    ("JustVugg", "colibri"),               # expect: healthy, active
    ("Anil-matcha", "Open-Generative-AI"), # expect: healthy, very active, popular
]

for owner, name in CASES:
    print(f"\n{'='*70}\n{owner}/{name}\n{'='*70}")
    report = check_repo(owner, name)
    print(f"Score: {report.score}/100 -- {report.score_label}")
    print(f"Fork: {report.is_fork} (parent: {report.parent_full_name})")
    print(f"Stars: {report.stars:,}  Forks: {report.forks:,}  Contributors: {report.contributors}")
    print(f"Commits last 90d: {report.commits_last_90d}  Open PRs: {report.open_prs}")
    for s in report.signals:
        print(f"  [{s.verdict.upper():4}] {s.label}: {s.detail}")
