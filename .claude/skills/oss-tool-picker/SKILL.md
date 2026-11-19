---
name: oss-tool-picker
description: Pick the right open-source GitHub tool for a task and use it safely. Use when the user needs local/self-hosted LLMs or an OpenAI-compatible server, image/video generation workflows, model loading or fine-tuning, model behavior steering, terminal or personal AI agents, web crawling or scraping, video/audio downloading, network scanning or packet analysis, OSINT or username/footprint lookup, or face-swap/video manipulation, or when the user mentions any of LocalAI, ComfyUI, Transformers, Heretic, Open Interpreter, OpenClaw, Scrapy, yt-dlp, Nmap, Wireshark, SpiderFoot, Sherlock or FaceFusion.
---

# OSS tool picker

Source: a "Most Dangerous GitHub Projects" reel tier list, reviewed in an earlier session.
Details were read from READMEs and layouts only. Re-verify before relying on them, since
repos change (Open Interpreter, for one, is no longer the Python tool the reel described).

## Pick by task

| Need | Tool | Repo | Notes |
|---|---|---|---|
| Run LLMs locally behind an OpenAI/Anthropic-compatible API | LocalAI | mudler/LocalAI (MIT) | Also image, speech, video, embeddings, MCP, agents |
| Image/video/audio generation pipelines | ComfyUI | Comfy-Org/ComfyUI (GPL) | Node graph; needs a GPU |
| Load, run or fine-tune models in Python | Transformers | huggingface/transformers (Apache-2.0) | See MIGRATION_GUIDE_V5.md |
| Steer or modify an LLM's behavior without training | Heretic | p-e-w/heretic (AGPL-3.0) | Presets: noslop, terse, nosyco, etc. Can also remove refusals |
| Terminal coding agent | Open Interpreter | openinterpreter/open-interpreter (Apache-2.0) | Now a Rust fork of Codex CLI. Acts on the user's machine |
| Personal assistant over chat apps | OpenClaw | openclaw/openclaw (MIT) | Broad permissions; sandbox it |
| Crawl or scrape sites at scale | Scrapy | scrapy/scrapy (BSD) | Respect robots.txt and site terms |
| Download audio/video | yt-dlp | yt-dlp/yt-dlp (public domain) | Only content the user may download |
| Scan hosts and networks | Nmap | nmap/nmap (NPSL) | Own or authorized targets only |
| Capture and analyze packets | Wireshark | wireshark/wireshark (GPL) | Own or authorized traffic only |
| OSINT automation (domains, IPs, orgs) | SpiderFoot | smicallef/spiderfoot (MIT) | Prefer the user's own assets |
| Check a username across sites | Sherlock | sherlock-project/sherlock (MIT) | Prefer the user's own username |
| Face swap / enhancement | FaceFusion | facefusion/facefusion (OpenRAIL-AS) | Read the license's use restrictions first |

## Getting the code

- The repos are public. In a cloud session, `add_repo` reports read access via the git proxy, then:
  `GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/<owner>/<name> /home/user/<owner>/<name>`
  Clone one at a time and use a long timeout. Run multi-repo clones as the background command itself, not detached with `&`.
- Cloud sessions have no GPU and a restricted network, so model-heavy or scanning work belongs on the user's own machine.
- Verify the owner and star count before cloning anything from social media. Lookalike malicious repos are common.

## Safety rules (apply every time)

1. Never pipe an installer straight to a shell. Download it, read it, then run it.
2. Run agents (Open Interpreter, OpenClaw) in a VM or container with a throwaway account and no real credentials.
3. Scanning and OSINT: only the user's own assets, or targets with explicit written authorization. Do not help profile, track or locate a specific private person.
4. FaceFusion: only the user's own face or consenting subjects. No impersonation, no deepfakes of real people without consent.
5. Heretic: legitimate for alignment research and style steering on models the user may modify. Do not help produce or distribute models intended to generate harmful content. AGPL obliges sharing changes if offered as a service.
6. Scrapy and yt-dlp: check robots.txt, terms of service and copyright before bulk collection or download.
7. State plainly what was read versus run. Do not claim a tool was tested if it was only read.

## Reference

Full comparison and installer audit notes: the report from the original session
(github-tier-list-report.md; not committed to this repo unless the user adds it).
