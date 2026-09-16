import streamlit as st

from reality_check import RepoCheckError, check_repo, parse_repo_input

st.set_page_config(page_title="Repo Reality Check", page_icon="🔎", layout="centered")

VERDICT_STYLE = {
    "good": ("🟢", "#1a7f37"),
    "warn": ("🟡", "#9a6700"),
    "bad": ("🔴", "#cf222e"),
    "info": ("ℹ️", "#57606a"),
}

st.title("🔎 GitHub Repo Reality Check")
st.caption(
    "Paste a repo and get an instant read on whether it's a real, actively maintained "
    "project or a stale fork/snapshot riding on someone else's numbers."
)

with st.sidebar:
    st.subheader("Settings")
    token = st.text_input(
        "GitHub personal access token (optional)",
        type="password",
        help=(
            "Unauthenticated requests are limited to 60/hour. A free token "
            "(no special scopes needed, just a plain classic token) raises "
            "that to 5000/hour. Never shared, used only for this request."
        ),
    )
    st.markdown(
        "[Create a free token](https://github.com/settings/tokens/new) "
        "(no scopes need to be checked -- public read access is the default)."
    )

repo_input = st.text_input(
    "Repository",
    placeholder="owner/repo  or  https://github.com/owner/repo",
)

if st.button("Check it", type="primary") or repo_input:
    if not repo_input.strip():
        st.stop()
    try:
        owner, name = parse_repo_input(repo_input)
        with st.spinner(f"Checking {owner}/{name}..."):
            report = check_repo(owner, name, token=token or None)
    except RepoCheckError as exc:
        st.error(str(exc))
        st.stop()

    score_color = "#1a7f37" if report.score >= 75 else "#9a6700" if report.score >= 50 else "#cf222e"
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(
            f"<div style='text-align:center'>"
            f"<div style='font-size:3rem;font-weight:700;color:{score_color}'>{report.score}</div>"
            f"<div style='color:{score_color};font-weight:600'>{report.score_label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.subheader(report.full_name)
        if report.description:
            st.write(report.description)
        st.markdown(f"[Open on GitHub]({report.url})")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stars", f"{report.stars:,}")
    c2.metric("Forks", f"{report.forks:,}")
    c3.metric("Contributors", report.contributors if report.contributors is not None else "?")
    c4.metric("Open issues", f"{report.open_issues:,}")

    st.divider()
    st.subheader("Findings")
    for s in report.signals:
        icon, color = VERDICT_STYLE[s.verdict]
        st.markdown(
            f"<div style='margin-bottom:0.6rem'>"
            f"<span style='color:{color};font-weight:600'>{icon} {s.label}</span>"
            f"<div style='color:#57606a;margin-left:1.4rem'>{s.detail}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if not report.signals:
        st.info("No strong signals either way -- a genuinely quiet, unremarkable repo.")

    st.divider()
    with st.expander("How the score works"):
        st.write(
            "Each check below contributes +1 (good), -1 (mixed/warn), or -2 (bad) to a raw "
            "score, which is then rescaled to 0-100. This is a set of transparent heuristics "
            "over public GitHub metadata, **not proof of anything** -- always use judgment, "
            "especially for borderline scores. Checks: fork snapshot detection, recency of "
            "last push, archived status, license presence, contributor count, commit velocity "
            "(last 90 days), PR responsiveness, and star-to-fork ratio."
        )

st.divider()
st.caption(
    "Free to use, no signup. Rate-limited to 60 checks/hour per visitor without a token "
    "(GitHub's own limit, not this app's)."
)
