#!/usr/bin/env python3
"""design-for-you triage: URL normalize, dup/graveyard check, loose gallery gate,
optional LLM covers, skill track, security admission gates, STATUS.md generation.
Shared by local Skill and Actions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
import yaml
from bs4 import BeautifulSoup

import security_admission as secu

ROOT = Path(__file__).resolve().parents[1]
SITES_PATH = ROOT / "sites.yaml"
VIDEOS_PATH = ROOT / "videos.yaml"
SKILLS_PATH = ROOT / "skills.yaml"
GRAVEYARD_PATH = ROOT / "graveyard.yaml"
STATUS_PATH = ROOT / "STATUS.md"

# Web track
SEAT_QUOTAS = {
    "product-flow": 10,
    "component": 12,
    "landing": 8,
    "system": 4,
}
CANDIDATE_CAP = 20
CORE_CAP = 30
VALID_KINDS = frozenset({"product-flow", "component", "landing", "system"})

# Video track (independent seats; does not compete with web)
VIDEO_KINDS = frozenset({"ui-motion", "launch-demo", "storyboard", "gen-style"})
VIDEO_SEAT_QUOTAS = {
    "ui-motion": 4,
    "launch-demo": 6,
    "storyboard": 4,
    "gen-style": 4,
}
VIDEO_CANDIDATE_CAP = 12
VIDEO_CORE_CAP = 18

# Skill track (first-class; no invented seat quota; security-gated)
SKILL_KINDS = frozenset({"design-skill"})
VALID_TRACKS = frozenset({"web", "video", "skill"})

STRIP_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "ref",
    "ref_src",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}

GALLERY_HINT_WORDS = re.compile(
    r"\b(gallery|inspirations?|showcase|screenshots?|examples?|"
    r"components?|patterns?|templates?|browse|search|filter|"
    r"categories?|tags?|collections?|directory|explore|"
    r"画廊|灵感|样例|组件|筛选|分类)\b",
    re.I,
)

USER_AGENT = (
    "design-for-you-triage/1.0 (+https://github.com/Bububuger/design-for-you; research)"
)


def load_yaml(path: Path) -> Any:
    if not path.exists():
        return [] if path.name != "graveyard.yaml" else {"sites": []}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data is not None else []


def save_yaml(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )


def domain_of(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def normalize_url(url: str, follow_redirects: bool = True, timeout: int = 15) -> str:
    """Strip tracking params; optionally follow redirects to final URL.

    Blocks non-public / link-local / decimal-IP hosts before network I/O.
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if not secu.is_allowed_fetch_url(url):
        raise ValueError(f"fetch_url_blocked:{url}")

    final = url
    if follow_redirects:
        try:
            resp = requests.get(
                url,
                allow_redirects=True,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT},
            )
            final = resp.url or url
            if not secu.is_allowed_fetch_url(final):
                raise ValueError(f"fetch_redirect_blocked:{final}")
        except requests.RequestException:
            final = url

    parsed = urlparse(final)
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in STRIP_QUERY_KEYS
    ]
    cleaned = parsed._replace(
        scheme=parsed.scheme or "https",
        netloc=parsed.netloc.lower(),
        query=urlencode(query),
        fragment="",
    )
    out = urlunparse(cleaned)
    # Prefer trailing slash on bare origins for consistency
    if cleaned.path in ("",) and not cleaned.query:
        out = urlunparse(cleaned._replace(path="/"))
    return out


def list_sites() -> list[dict]:
    data = load_yaml(SITES_PATH)
    return data if isinstance(data, list) else []


def list_videos() -> list[dict]:
    data = load_yaml(VIDEOS_PATH)
    return data if isinstance(data, list) else []


def list_skills() -> list[dict]:
    data = load_yaml(SKILLS_PATH)
    return data if isinstance(data, list) else []


def list_pool(track: str = "web") -> list[dict]:
    track = (track or "web").lower()
    if track == "video":
        return list_videos()
    if track == "skill":
        return list_skills()
    return list_sites()


def pool_path(track: str = "web") -> Path:
    track = (track or "web").lower()
    if track == "video":
        return VIDEOS_PATH
    if track == "skill":
        return SKILLS_PATH
    return SITES_PATH


def list_graveyard() -> list[dict]:
    data = load_yaml(GRAVEYARD_PATH)
    if isinstance(data, dict):
        # Shared graveyard; historically "sites" key — also accept "entries".
        return list(data.get("sites") or data.get("entries") or [])
    if isinstance(data, list):
        return data
    return []


def save_graveyard(entries: list[dict]) -> None:
    save_yaml(GRAVEYARD_PATH, {"sites": entries})


def github_repo_key(url: str) -> str | None:
    """Normalize github.com / www.github.com URLs to owner/repo (lower, no .git)."""
    raw = (url or "").strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host != "github.com":
        return None
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        return None
    owner = parts[0].lower()
    repo = parts[1].lower()
    if repo.endswith(".git"):
        repo = repo[: -len(".git")]
    return f"{owner}/{repo}"


def urls_match(a: str, b: str) -> bool:
    if a.rstrip("/") == b.rstrip("/"):
        return True
    ga, gb = github_repo_key(a), github_repo_key(b)
    # Any github.com URL: match only by owner/repo, never by bare domain.
    if ga is not None or gb is not None:
        return ga is not None and gb is not None and ga == gb
    return domain_of(a) == domain_of(b)


def _track_for_where(where: str) -> str:
    if where == "videos":
        return "video"
    if where == "skills":
        return "skill"
    return "web"


def _entry_urls(site: dict) -> list[str]:
    urls: list[str] = []
    if site.get("url"):
        urls.append(site["url"])
    src = site.get("source") or {}
    if isinstance(src, dict):
        for key in ("install_locator", "catalog_url", "skill_md_url", "index_url"):
            if src.get(key):
                urls.append(src[key])
    for alias in site.get("aliases") or []:
        if alias:
            urls.append(alias)
    return urls


def _dup_in_pool(url: str, sites: list[dict], where: str) -> dict | None:
    for site in sites:
        for candidate in _entry_urls(site):
            if urls_match(url, candidate) or secu.locators_match(url, candidate):
                return {
                    "where": where,
                    "id": site.get("id"),
                    "status": site.get("status"),
                    "track": _track_for_where(where),
                }
    return None


def find_duplicate(url: str, track: str | None = None) -> dict | None:
    """Check pool(s) + shared graveyard with track-aware policy.

    - skill: only skills.yaml + graveyard entries with track=skill
    - web/video: sites + videos (shared inspiration URL uniqueness) + non-skill graveyard
    """
    d = domain_of(url)
    if track == "skill":
        order = [("skills", list_skills())]
    elif track == "video":
        order = [("videos", list_videos()), ("sites", list_sites())]
    elif track == "web":
        order = [("sites", list_sites()), ("videos", list_videos())]
    else:
        order = [
            ("sites", list_sites()),
            ("videos", list_videos()),
            ("skills", list_skills()),
        ]
    for where, sites in order:
        hit = _dup_in_pool(url, sites, where)
        if hit:
            return hit
    for g in list_graveyard():
        g_track = g.get("track")
        if track == "skill":
            if g_track != "skill":
                continue
        elif track in ("web", "video"):
            if g_track == "skill":
                continue
        elif g_track == "skill":
            continue
        if g.get("url") and (
            urls_match(url, g["url"]) or secu.locators_match(url, g["url"])
        ):
            return {"where": "graveyard", "reason": g.get("reason"), "entry": g}
        gd = g.get("domain") or domain_of(g.get("url", "") or "")
        if not gd or gd != d:
            continue
        # github.com domain alone must not collide every repo; need URL key.
        if gd in ("github.com", "www.github.com"):
            continue
        # Skill package hosts: require URL match, not bare domain collision.
        if gd in ("uizze.sh", "skills.sh"):
            continue
        return {"where": "graveyard", "reason": g.get("reason"), "entry": g}
    return None


def fetch_html(url: str, timeout: int = 20) -> tuple[str | None, int | None, str | None]:
    if not secu.is_allowed_fetch_url(url):
        return None, None, f"fetch_url_blocked:{url}"
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        if resp.url and not secu.is_allowed_fetch_url(resp.url):
            return None, None, f"fetch_redirect_blocked:{resp.url}"
        return resp.text, resp.status_code, resp.url
    except requests.RequestException as e:
        return None, None, str(e)


def loose_gallery_gate(html: str, url: str) -> dict:
    """Loose gallery structure check. Uncertain → needs_human, never hard reject here."""
    soup = BeautifulSoup(html or "", "html.parser")
    text = soup.get_text(" ", strip=True)[:8000]
    links = soup.find_all("a", href=True)
    cardsish = 0
    for a in links:
        href = a.get("href") or ""
        if href.startswith("#") or href.startswith("javascript:"):
            continue
        cardsish += 1

    has_hint = bool(GALLERY_HINT_WORDS.search(text)) or bool(
        GALLERY_HINT_WORDS.search(html[:50000] if html else "")
    )
    has_search = bool(
        soup.find("input", attrs={"type": "search"})
        or soup.find("input", attrs={"name": re.compile(r"search|q|query", re.I)})
        or soup.find(attrs={"role": "search"})
    )
    nav_or_filter = bool(
        soup.find("nav")
        or soup.find(class_=re.compile(r"filter|tag|categor|facet|chip", re.I))
    )

    score = 0
    reasons: list[str] = []
    if has_hint:
        score += 2
        reasons.append("hint_words")
    if has_search:
        score += 2
        reasons.append("search_ui")
    if nav_or_filter:
        score += 1
        reasons.append("nav_or_filter")
    if cardsish >= 12:
        score += 2
        reasons.append(f"links>={cardsish}")
    elif cardsish >= 6:
        score += 1
        reasons.append(f"links={cardsish}")

    # GitHub repos: treat as gallery-ish if README-heavy design collections
    if "github.com" in domain_of(url):
        score += 1
        reasons.append("github_repo")

    if score >= 3:
        verdict = "pass"
    elif score >= 1:
        verdict = "needs_human"
    else:
        # Still needs_human — do NOT auto-graveyard on weak HTML (SPA / gated)
        verdict = "needs_human"
        reasons.append("weak_html_or_spa")

    return {
        "verdict": verdict,
        "score": score,
        "reasons": reasons,
        "link_count": cardsish,
    }


# Contrastive / negated mentions of landing — must not set kind=landing (#14 FP).
NEGATED_LANDING_RE = re.compile(
    r"(?:"
    r"不是(?:又一个|一个|单纯的?|普通的?)?.{0,16}(?:落地页|landing(?:\s*pages?)?)"
    r"|并非.{0,16}(?:落地页|landing(?:\s*pages?)?)"
    r"|而非.{0,16}(?:落地页|landing(?:\s*pages?)?)"
    r"|别把.{0,20}(?:当|成).{0,10}(?:落地页|landing(?:\s*pages?)?)"
    r"|不要(?:把)?.{0,16}(?:当|成).{0,10}(?:落地页|landing(?:\s*pages?)?)"
    r"|别当.{0,10}(?:落地页|landing(?:\s*pages?)?)"
    r"|not\s+(?:just\s+)?(?:another\s+)?(?:a\s+)?landing(?:\s*pages?)?"
    r"|isn'?t\s+(?:just\s+)?(?:another\s+)?(?:a\s+)?landing(?:\s*pages?)?"
    r"|rather\s+than\s+(?:a\s+)?(?:ordinary\s+)?landing(?:\s*pages?)?"
    r")",
    re.I,
)

# Positive gallery/marketing signals only (avoid bare "landing" / negated 落地页).
LANDING_POSITIVE_KEYS = (
    "落地页画廊",
    "落地页合集",
    "落地页灵感",
    "落地页陈列",
    "落地页站点",
    "营销落地页",
    "landing page gallery",
    "landing pages gallery",
    "landing page showcase",
    "landing pages showcase",
    "landing gallery",
    "landing showcase",
    "landing page inspiration",
    "marketing landing",
    "landing pages",
    "landing page",
    "落地页",
)

EXPLICIT_KIND_RE = re.compile(
    r"(?:^|\n)\s*kind\s*[:=]\s*([a-z0-9-]+)\b",
    re.I,
)
EXPLICIT_TRACK_RE = re.compile(
    r"(?:^|\n)\s*track\s*[:=]\s*(web|video|skill)\b",
    re.I,
)
EXPLICIT_COVERS_RE = re.compile(
    r"(?:^|\n)\s*covers\s*[:=]\s*\[?([^\n\]]+)\]?",
    re.I,
)
EXPLICIT_LICENSE_NOTE_RE = re.compile(
    r"(?:^|\n)\s*license_note\s*[:=]\s*(.+)$",
    re.I | re.M,
)

VIDEO_KIND_HINTS = {
    "launch-demo": ["launch-demo", "launch demo", "product launch", "发布视频", "演示视频", "demo reel"],
    "storyboard": ["storyboard", "分镜", "叙事", "narrative board"],
    "gen-style": ["gen-style", "gen style", "sora", "runway", "kling", "生成视频", "生成风格"],
    "ui-motion": ["ui-motion", "ui motion", "micro-interaction", "动效", "motion design", "interface animation"],
}


def scrub_negated_landing_mentions(text: str) -> str:
    """Remove contrastive spans so 落地页 inside 不是…落地页… does not match."""
    return NEGATED_LANDING_RE.sub(" ", text or "")


def kinds_for_track(track: str) -> frozenset[str]:
    if track == "video":
        return VIDEO_KINDS
    if track == "skill":
        return SKILL_KINDS
    return VALID_KINDS


def parse_explicit_labels(reason: str, track: str | None = None) -> dict[str, Any]:
    """Honor explicit track/kind/covers/license_note in the issue body when present."""
    out: dict[str, Any] = {}
    if not reason:
        return out
    tm = EXPLICIT_TRACK_RE.search(reason)
    if tm:
        out["track"] = tm.group(1).lower()
    resolved_track = (track or out.get("track") or "web").lower()
    if resolved_track not in VALID_TRACKS:
        resolved_track = "web"
    allowed = kinds_for_track(resolved_track)
    km = EXPLICIT_KIND_RE.search(reason)
    if km:
        kind = km.group(1).lower()
        if kind in allowed:
            out["kind"] = kind
    cm = EXPLICIT_COVERS_RE.search(reason)
    if cm:
        raw = cm.group(1).strip().strip("[]")
        covers = [
            c.strip().strip("'\"")
            for c in re.split(r"[,，、]", raw)
            if c.strip().strip("'\"")
        ]
        if covers:
            out["covers"] = covers
    lm = EXPLICIT_LICENSE_NOTE_RE.search(reason)
    if lm:
        note = lm.group(1).strip().strip("'\"")
        if note:
            out["license_note"] = note
    return out


def rule_video_kind_from_text(text: str, reason: str = "") -> str:
    blob = f"{text}\n{reason}".lower()
    for kind, keys in VIDEO_KIND_HINTS.items():
        if any(k in blob for k in keys):
            return kind
    return "ui-motion"


def rule_covers_from_text(text: str, reason: str = "") -> list[str]:
    blob = f"{text}\n{reason}".lower()
    landing_blob = scrub_negated_landing_mentions(blob)
    lexicon = {
        "data-table": ["data table", "datatable", "表格", "table"],
        "filter-builder": ["filter builder", "query builder", "筛选"],
        "dashboard": ["dashboard", "看板"],
        "settings": ["settings", "设置"],
        "billing": ["billing", "pricing", "usage"],
        "empty-state": ["empty state", "空状态"],
        "onboarding": ["onboarding", "引导"],
        "skeleton": ["skeleton", "loading"],
        "chat": ["chat", "message"],
        "agent-flow": ["agent", "tool call", "approval"],
        "bento-grid": ["bento"],
        "navbar": ["navbar", "header", "navigation"],
        "footer": ["footer", "页脚"],
        "cta": ["cta", "call to action"],
        "design-md": ["design.md", "design tokens", "tokens"],
        "micro-interaction": ["micro-interaction", "animation", "motion"],
        "form": ["form", "表单"],
        "dialog": ["dialog", "modal"],
        "sidebar": ["sidebar"],
        "command-palette": ["command palette", "cmdk"],
        "user-feedback": ["user-feedback", "user feedback", "用户反馈"],
    }
    found: list[str] = []
    for tag, keys in lexicon.items():
        if any(k in blob for k in keys):
            found.append(tag)
    # landing-page: scrub negations first; match positive/gallery-oriented keys only
    if any(k in landing_blob for k in LANDING_POSITIVE_KEYS):
        found.append("landing-page")
    return found[:12]


def llm_covers_and_hint(
    url: str, html_snippet: str, reason: str, track: str = "web"
) -> dict | None:
    """Optional LLM assist. Returns None if no key / failure → caller falls back."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if track == "video":
        kind_line = (
            "kind (one of ui-motion|launch-demo|storyboard|gen-style).\n"
            "Prefer launch-demo for product launch/demo reels, ui-motion for UI animation, "
            "storyboard for narrative boards, gen-style for generative video style refs."
        )
        role = "video-inspiration libraries / demo reels for a retrieval pool"
    else:
        kind_line = (
            "kind (one of product-flow|component|landing|system).\n"
            "If this is a plain marketing landing for a single product (not a multi-case "
            "gallery), set covers to [] and kind to landing."
        )
        role = "design-inspiration gallery sites for a retrieval pool"
    prompt = (
        f"You label {role}.\n"
        f"URL: {url}\n"
        f"Track: {track}\n"
        f"Submitter reason: {reason}\n"
        f"HTML/text snippet:\n{html_snippet[:6000]}\n\n"
        "Reply JSON only with keys: covers (array of short kebab-case tags), "
        "search_hint (one Chinese or English sentence on how to search in-site), "
        f"{kind_line}"
    )

    try:
        if openai_key:
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model=os.environ.get("DESIGN_POOL_LLM_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Return valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            raw = resp.choices[0].message.content or "{}"
        elif anthropic_key:
            import anthropic

            client = anthropic.Anthropic(api_key=anthropic_key)
            msg = client.messages.create(
                model=os.environ.get(
                    "DESIGN_POOL_LLM_MODEL", "claude-3-5-haiku-latest"
                ),
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = "".join(
                b.text for b in msg.content if getattr(b, "type", None) == "text"
            )
        else:
            return None

        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:  # noqa: BLE001 — degrade to rules
        print(f"[triage] LLM assist failed: {e}", file=sys.stderr)
        return None


def slug_id(url: str, name: str | None = None) -> str:
    if name:
        s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        if s:
            return s[:48]
    host = domain_of(url).split(".")[0]
    return re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")[:48] or "site"


def seat_counts(sites: list[dict] | None = None, track: str = "web") -> dict:
    track = (track or "web").lower()
    if track not in VALID_TRACKS:
        track = "web"
    if sites is None:
        sites = list_pool(track)
    if track == "skill":
        # No invented quota — counts only.
        by_status: dict[str, int] = {}
        for s in sites:
            st = s.get("status") or "unknown"
            by_status[st] = by_status.get(st, 0) + 1
        return {
            "track": "skill",
            "total": len(sites),
            "by_status": by_status,
            "core_total": by_status.get("core", 0),
            "candidate_total": by_status.get("candidate", 0),
            "pending_review_total": by_status.get("pending-review", 0)
            + by_status.get("pending_review", 0),
            "blocked_total": by_status.get("blocked", 0),
            "candidate_cap": None,
            "core_cap": None,
            "quota": None,
        }
    quotas = VIDEO_SEAT_QUOTAS if track == "video" else SEAT_QUOTAS
    default_kind = "ui-motion" if track == "video" else "component"
    core = [s for s in sites if s.get("status") == "core"]
    cand = [s for s in sites if s.get("status") == "candidate"]
    by_kind: dict[str, int] = {k: 0 for k in quotas}
    for s in core:
        k = s.get("kind") or default_kind
        by_kind[k] = by_kind.get(k, 0) + 1
    return {
        "track": track,
        "core_total": len(core),
        "candidate_total": len(cand),
        "by_kind": by_kind,
        "candidate_cap": VIDEO_CANDIDATE_CAP if track == "video" else CANDIDATE_CAP,
        "core_cap": VIDEO_CORE_CAP if track == "video" else CORE_CAP,
    }


def _seat_table_rows(counts: dict, quotas: dict[str, int], core_cap: int, cand_cap: int) -> list[str]:
    by = counts["by_kind"]
    lines: list[str] = [
        "| 分类 | 配额 | 已用 | 余量 | 状态 |",
        "| :--- | ---: | ---: | ---: | :--- |",
    ]
    for kind, quota in quotas.items():
        used = by.get(kind, 0)
        rem = quota - used
        if rem < 0:
            status = "**超配 · 冻结新增**"
        elif rem == 0:
            status = "满席"
        else:
            status = "有空位"
        rem_s = f"**{rem}**" if rem < 0 else str(rem)
        lines.append(f"| {kind} | {quota} | {used} | {rem_s} | {status} |")
    lines += [
        f"| **Core 合计** | **≤{core_cap}** | **{counts['core_total']}** | — | — |",
        f"| candidate 池 | {cand_cap} | {counts['candidate_total']} | "
        f"{cand_cap - counts['candidate_total']} | "
        f"{'有空位' if counts['candidate_total'] < cand_cap else '满'} |",
    ]
    return lines


def generate_status_md(
    miss_terms: list[str] | None = None,
    freeze_landing: bool = True,
) -> str:
    web = seat_counts(track="web")
    video = seat_counts(track="video")
    skill = seat_counts(track="skill")
    lines = [
        "# Design For You 缺口悬赏单",
        "",
        f"> 自动生成于 {date.today().isoformat()}。",
    ]
    if freeze_landing:
        lines.append(
            "> **暂不接收普通 `landing`（整站/营销落地页）新站。** landing 席位已超配或接近满席，冻结新增（仅 Web 轨）。"
        )
    lines.append(
        "> **新 Web / Skill 入库需已提交的 security admission review**（见 `security-reviews/`）；"
        "Issue 正文自称 approved 无效。存量 web/video 按 legacy-unreviewed 兼容，不批量盖章安全。"
    )
    lines += [
        "",
        "## Web 席位余量（Core）",
        "",
    ]
    lines += _seat_table_rows(web, SEAT_QUOTAS, CORE_CAP, CANDIDATE_CAP)
    lines += [
        "",
        "## Video 席位余量（Core）",
        "",
    ]
    lines += _seat_table_rows(video, VIDEO_SEAT_QUOTAS, VIDEO_CORE_CAP, VIDEO_CANDIDATE_CAP)
    lines += [
        "",
        "## Skill 资源（无席位配额 · 仅计数）",
        "",
        "| 状态 | 数量 |",
        "| :--- | ---: |",
        f"| candidate | {skill.get('candidate_total', 0)} |",
        f"| core | {skill.get('core_total', 0)} |",
        f"| pending-review | {skill.get('pending_review_total', 0)} |",
        f"| blocked | {skill.get('blocked_total', 0)} |",
        f"| **合计** | **{skill.get('total', 0)}** |",
        "",
        "投喂：Issue 正文加 `track: skill`；标题=install locator。须先有绑定内容完整性的 review 文件。",
        "",
        "## 首期定向悬赏（高优 · Web）",
        "",
        "投喂：Issue 标题=URL，标签=`inbox`，正文=原因/`covers`（默认 `track: web`）。",
        "",
        "### 1. B2B / SaaS 数据密集型界面库",
        "",
        "缺：`data-table`、`filter-builder` / `query-builder`、`settings`、`billing` / `usage`。",
        "",
        "### 2. 开发者工具 / 可观测与控制台",
        "",
        "缺：`log-viewer`、`trace-waterfall`、`chart` / `time-series`、`cli` / `terminal-ui`、`alert-rule`。",
        "",
        "### 3. 边缘与状态设计专精站",
        "",
        "缺：`empty-state`、`onboarding-checklist`、`skeleton` / `loading`、`permission-denied`。",
        "",
        "### 4. AI / Agent 原生交互实录",
        "",
        "缺：多步审批、Diff 审阅、引用溯源、Canvas / Artifact 动线。",
        "",
        "## 视频轨悬赏（简）",
        "",
        "投喂：Issue 正文加 `track: video` 与 `kind: launch-demo|ui-motion|storyboard|gen-style`。",
        "",
        "- **launch-demo**：产品发布 / demo 成片灵感（席位余量见上表）",
        "- **ui-motion**：界面动效 / micro-interaction 实录",
        "- **storyboard**：分镜 / 叙事结构参考",
        "- **gen-style**：生成视频风格参考",
        "",
        "## 近期未命中交互词",
        "",
    ]
    if miss_terms:
        for t in miss_terms:
            lines.append(f"- `{t}`")
    else:
        lines.append("（尚无 logs 战绩或未汇总；由 health.yml 刷新。）")
    lines.append("")
    return "\n".join(lines)


def refresh_status(miss_terms: list[str] | None = None) -> None:
    STATUS_PATH.write_text(generate_status_md(miss_terms=miss_terms), encoding="utf-8")
    print(f"Wrote {STATUS_PATH}")


def add_to_graveyard(
    url: str,
    reason: str,
    notes: str = "",
    track: str | None = None,
) -> None:
    entries = list_graveyard()
    row: dict[str, Any] = {
        "domain": domain_of(url),
        "url": url,
        "reason": reason,
        "rejected_at": date.today().isoformat(),
        "cooldown_until": f"{date.today().year}-12-31",
        "notes": notes,
    }
    if track:
        row["track"] = track
    entries.append(row)
    save_graveyard(entries)


def _admission_for_entry(
    entry: dict,
    track: str,
    issue_body: str | None = None,
) -> secu.AdmissionResult:
    locator = entry.get("url") or (entry.get("source") or {}).get("install_locator")
    integ = (entry.get("content_integrity") or {}).get("package_integrity")
    content_hash = (entry.get("content_integrity") or {}).get("content_sha256")
    return secu.can_write_candidate(
        track,
        locator=locator,
        package_integrity=integ,
        content_sha256=content_hash,
        resource_id=entry.get("id"),
        issue_body=issue_body,
    )


def add_candidate(
    entry: dict,
    track: str = "web",
    *,
    issue_body: str | None = None,
) -> None:
    """Append a candidate. Gated tracks always require bound security admission.

    There is no public skip/bypass parameter — YAML edits are checked by
    `scripts/validate_pool_security.py` in CI.
    """
    track = (track or "web").lower()
    if track not in VALID_TRACKS:
        track = "web"
    sites = list_pool(track)
    eid = entry.get("id")
    if eid and any(s.get("id") == eid for s in sites):
        raise RuntimeError(f"duplicate_id:{track}:{eid}")
    if track in secu.GATED_TRACKS:
        # Forbid self-labeling legacy on write path.
        marker = (entry.get("security_admission") or "").lower().replace("_", "-")
        if marker == "legacy-unreviewed":
            raise RuntimeError(
                "security_admission_denied:invalid_review:"
                "new_writes_cannot_self_label_legacy_unreviewed"
            )
        adm = _admission_for_entry(entry, track, issue_body=issue_body)
        if not adm.ok:
            raise RuntimeError(f"security_admission_denied:{adm.status}:{adm.reason}")
        entry["security_review_id"] = adm.review_id
        entry["security_admission"] = "reviewed-approve-bound"
    counts = seat_counts(sites, track=track)
    cand_cap = counts.get("candidate_cap")
    if cand_cap is not None and counts["candidate_total"] >= cand_cap:
        raise RuntimeError(f"{track} candidate pool full")
    # landing freeze is web-only (skills never consume web landing seats)
    if track == "web" and entry.get("kind") == "landing":
        raise RuntimeError("landing submissions frozen; refuse ordinary landing")
    if track == "skill":
        entry.setdefault("actual_test_status", "not_tested")
        if entry.get("status") not in (
            "candidate",
            "core",
            "pending-review",
            "blocked",
        ):
            entry["status"] = "candidate"
    sites.append(entry)
    save_yaml(pool_path(track), sites)


def _draft_entry(
    url: str,
    name: str | None,
    kind: str,
    covers: list[str],
    search_hint: str,
    auth: str,
    license_note: str | None = None,
) -> dict:
    entry: dict[str, Any] = {
        "id": slug_id(url, name),
        "name": name or domain_of(url),
        "url": url,
        "aliases": [],
        "status": "candidate",
        "kind": kind,
        "covers": covers,
        "search_hint": search_hint,
        "auth": auth,
        "added_at": date.today().isoformat(),
    }
    if license_note:
        entry["license_note"] = license_note
    return entry


def _apply_security_gate(
    result: dict[str, Any],
    entry: dict,
    track: str,
    reason: str,
    write: bool,
) -> dict[str, Any]:
    """Block candidate/core writes unless a bound review approves (web/skill)."""
    adm = _admission_for_entry(entry, track, issue_body=reason)
    result["security_admission"] = adm.as_dict()
    if adm.ok:
        entry.setdefault("security_review_id", adm.review_id)
        entry.setdefault("security_admission", "reviewed-approve-bound")
        result["entry"] = entry
        result["decision"] = "accept_candidate"
        if write:
            try:
                add_candidate(entry, track=track, issue_body=reason)
                refresh_status()
            except RuntimeError as e:
                err = str(e)
                if err.startswith("security_admission_denied:"):
                    parts = err.split(":", 2)
                    status = parts[1] if len(parts) > 1 else "missing"
                    result["decision"] = (
                        "rejected_security_blocked"
                        if status == "blocked"
                        else "pending_security_review"
                    )
                    result["write_error"] = err
                else:
                    result["decision"] = "needs_human"
                    result["write_error"] = err
        return result

    if adm.status == "blocked":
        result["decision"] = "rejected_security_blocked"
        result["draft"] = entry
        if write:
            add_to_graveyard(
                entry.get("url")
                or (entry.get("source") or {}).get("install_locator")
                or result.get("url", ""),
                "security_blocked",
                notes=f"review={adm.review_id} {adm.reason}",
                track=track,
            )
        return result

    result["decision"] = "pending_security_review"
    result["draft"] = entry
    result["note"] = (
        "no_auto_candidate_without_bound_security_review;"
        "issue_body_cannot_self_assert_approval"
    )
    return result


def triage_skill_locator(
    url: str,
    reason: str = "",
    name: str | None = None,
    write: bool = False,
) -> dict:
    """Skill-track intake: metadata only; requires bound security review to admit.

    Integrity pin comes from the committed review for (track, id, locator).
    Issue-supplied package_integrity is only accepted when it equals that pin;
    it cannot attach a foreign approval to a different locator.
    """
    result: dict[str, Any] = {
        "input_url": url,
        "reason": reason,
        "track": "skill",
    }
    locator = secu.normalize_locator(url)
    result["url"] = locator
    dup = find_duplicate(locator, track="skill")
    if dup:
        result["decision"] = "duplicate"
        result["duplicate"] = dup
        return result

    explicit = parse_explicit_labels(reason, track="skill")
    covers = list(explicit.get("covers") or ["design-skill"])
    skill_id = slug_id(locator, name)
    entry: dict[str, Any] = {
        "id": skill_id,
        "name": name or domain_of(locator) or skill_id,
        "status": "candidate",
        "kind": explicit.get("kind") or "design-skill",
        "source": {"install_locator": locator},
        "url": locator,
        "aliases": [],
        "covers": covers,
        "search_hint": reason.strip() or "track: skill design playbook locator",
        "auth": "none",
        "actual_test_status": "not_tested",
        "added_at": date.today().isoformat(),
    }
    if explicit.get("license_note"):
        entry["license_note"] = explicit["license_note"]

    # Resolve pin ONLY from a review that matches track+id+locator (AND).
    rev = secu.find_matching_review("skill", locator=locator, resource_id=skill_id)
    issue_pin_m = re.search(
        r"(?:^|\n)\s*package_integrity\s*[:=]\s*([a-f0-9]{64})\b",
        reason or "",
        re.I,
    )
    issue_pin = issue_pin_m.group(1).lower() if issue_pin_m else None
    if rev is not None:
        pin = secu.review_pin(rev, "skill")
        if pin:
            if issue_pin and issue_pin != pin:
                result["decision"] = "pending_security_review"
                result["note"] = "issue_package_integrity_does_not_match_review_pin"
                result["draft"] = entry
                result["security_admission"] = {
                    "ok": False,
                    "status": "stale",
                    "reason": "issue_pin_mismatch_vs_committed_review",
                    "review_id": rev.get("id"),
                }
                return result
            entry["content_integrity"] = {
                "algorithm": "sha256",
                "package_integrity": pin,
            }
        # else: evaluate_admission will reject invalid/empty binds_to
    elif issue_pin:
        # Untrusted issue hash without matching review cannot mint approval.
        entry["content_integrity"] = {
            "algorithm": "sha256",
            "package_integrity": issue_pin,
        }

    result["label_source"] = "rules"
    result["gallery_gate"] = {"verdict": "skipped", "reasons": ["skill_track"]}
    return _apply_security_gate(result, entry, "skill", reason, write)


def triage_url(
    url: str,
    reason: str = "",
    name: str | None = None,
    auth_hint: str | None = None,
    write: bool = False,
    track: str | None = None,
) -> dict:
    result: dict[str, Any] = {"input_url": url, "reason": reason}
    try:
        normalized = normalize_url(url)
    except Exception as e:  # noqa: BLE001
        normalized = url.strip()
        result["normalize_error"] = str(e)
    result["url"] = normalized

    # Resolve track early (explicit CLI/arg wins; else issue body; default web).
    explicit_early = parse_explicit_labels(reason)
    resolved_track = (track or explicit_early.get("track") or "web").lower()
    if resolved_track not in VALID_TRACKS:
        resolved_track = "web"
    result["track"] = resolved_track
    allowed_kinds = kinds_for_track(resolved_track)

    if resolved_track == "skill":
        return triage_skill_locator(url, reason=reason, name=name, write=write)

    dup = find_duplicate(normalized, track=resolved_track)
    if dup:
        result["decision"] = "duplicate"
        result["duplicate"] = dup
        return result

    html, status, err_or_final = fetch_html(normalized)
    result["http_status"] = status
    if html is None:
        result["fetch_error"] = err_or_final
        result["decision"] = "needs_human"
        result["note"] = "fetch_failed_do_not_graveyard"
        return result

    if err_or_final and err_or_final.startswith("http"):
        result["url"] = normalize_url(err_or_final, follow_redirects=False)

    gate = loose_gallery_gate(html, result["url"])
    result["gallery_gate"] = gate

    # local_session sites: skip anonymous hard-wall sample open
    auth = auth_hint or "none"
    result["auth"] = auth

    explicit = parse_explicit_labels(reason, track=resolved_track)
    license_note = explicit.get("license_note")
    llm = llm_covers_and_hint(
        result["url"], html[:8000], reason, track=resolved_track
    )
    if llm:
        covers = list(llm.get("covers") or [])
        search_hint = llm.get("search_hint") or reason or "浏览画廊"
        kind = llm.get("kind") or (
            "ui-motion" if resolved_track == "video" else "component"
        )
        if kind not in allowed_kinds:
            kind = (
                rule_video_kind_from_text(html[:4000], reason)
                if resolved_track == "video"
                else "component"
            )
        result["label_source"] = "llm"
    elif resolved_track == "video":
        covers = rule_covers_from_text(html[:4000], reason)
        # Soft video tags from reason/html when rules lexicon is sparse
        for tag, keys in (
            ("launch-demo", VIDEO_KIND_HINTS["launch-demo"]),
            ("ui-motion", VIDEO_KIND_HINTS["ui-motion"]),
            ("storyboard", VIDEO_KIND_HINTS["storyboard"]),
            ("gen-style", VIDEO_KIND_HINTS["gen-style"]),
        ):
            blob = f"{html[:2000]}\n{reason}".lower()
            if any(k in blob for k in keys) and tag not in covers:
                covers.append(tag)
        search_hint = reason.strip() or "浏览视频灵感库并按风格/动效筛选"
        kind = rule_video_kind_from_text(html[:4000], reason)
        result["label_source"] = "rules"
    else:
        covers = rule_covers_from_text(html[:4000], reason)
        search_hint = reason.strip() or "浏览画廊并按标签/搜索筛选"
        kind = "component"
        if any(c in covers for c in ("landing-page",)):
            kind = "landing"
        if "design-md" in covers:
            kind = "system"
        if any(
            c in covers
            for c in ("dashboard", "onboarding", "agent-flow", "settings", "chat")
        ):
            kind = "product-flow"
        result["label_source"] = "rules"

    # Explicit issue-body kind/covers win over rules (and fill gaps for LLM).
    if explicit.get("covers"):
        # Prefer explicit list; keep any extra rule tags that do not contradict.
        merged: list[str] = []
        for c in list(explicit["covers"]) + list(covers):
            if c not in merged:
                merged.append(c)
        covers = merged[:12]
    if explicit.get("kind"):
        kind = explicit["kind"]
        result["explicit_kind"] = True
    if kind not in allowed_kinds:
        kind = "ui-motion" if resolved_track == "video" else "component"

    if result.get("label_source") == "rules" and not covers:
        result["decision"] = "needs_human"
        result["note"] = "weak_covers_no_llm"
        # still attach draft for human
        result["draft"] = _draft_entry(
            result["url"], name, kind, covers, search_hint, auth, license_note
        )
        return result

    # Landing freeze applies to web track only.
    if resolved_track == "web" and kind == "landing":
        result["decision"] = "rejected_landing_freeze"
        if write:
            add_to_graveyard(
                result["url"],
                "landing_freeze",
                notes="ordinary landing frozen at intake",
                track="web",
            )
        return result

    if gate["verdict"] == "needs_human" and result.get("label_source") == "rules":
        # Keep human path unless LLM + strong score
        result["decision"] = "needs_human"
        result["draft"] = _draft_entry(
            result["url"], name, kind, covers, search_hint, auth, license_note
        )
        return result

    entry = _draft_entry(
        result["url"], name, kind, covers, search_hint, auth, license_note
    )
    # Web integrity pin: prefer hash of actually fetched HTML (snapshot evidence).
    # Issue-supplied content_sha256 is advisory and must match fetched bytes if both
    # present — it cannot substitute for a committed review binding.
    if resolved_track == "web" and html:
        fetched_hash = secu.sha256_text(html)
        issue_hash_m = re.search(
            r"(?:^|\n)\s*content_sha256\s*[:=]\s*([a-f0-9]{64})\b",
            reason or "",
            re.I,
        )
        issue_hash = issue_hash_m.group(1).lower() if issue_hash_m else None
        if issue_hash and issue_hash != fetched_hash:
            result["decision"] = "pending_security_review"
            result["note"] = "issue_content_sha256_does_not_match_fetched_html"
            result["draft"] = entry
            result["security_admission"] = {
                "ok": False,
                "status": "stale",
                "reason": "issue_pin_mismatch_vs_fetched_html",
            }
            return result
        entry["content_integrity"] = {
            "algorithm": "sha256",
            "content_sha256": fetched_hash,
        }
        result["content_sha256_source"] = "fetched_html"
    result["entry"] = entry

    if gate["verdict"] == "pass" or result.get("label_source") == "llm":
        if resolved_track in secu.GATED_TRACKS:
            return _apply_security_gate(
                result, entry, resolved_track, reason, write
            )
        result["decision"] = "accept_candidate"
        if write:
            try:
                add_candidate(entry, track=resolved_track, issue_body=reason)
                refresh_status()
            except RuntimeError as e:
                result["decision"] = "needs_human"
                result["write_error"] = str(e)
        return result

    result["decision"] = "needs_human"
    result["draft"] = entry
    return result


def cmd_inbox_from_env() -> int:
    """GitHub Actions helper: read issue title/body, triage, print JSON + markdown comment."""
    url = os.environ.get("ISSUE_TITLE", "").strip()
    body = os.environ.get("ISSUE_BODY", "") or ""
    if not url or not url.startswith("http") and "://" not in url and "." not in url:
        # sometimes URL is only in body
        m = re.search(r"https?://\S+", body)
        if m:
            url = m.group(0).rstrip(").,]")
        else:
            print("::error::No URL in issue title/body")
            out = {
                "decision": "rejected",
                "comment": "未在标题或正文中找到 URL。请把完整 URL 放在标题。",
            }
            print(json.dumps(out, ensure_ascii=False))
            Path("/tmp/triage-result.json").write_text(
                json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return 0

    result = triage_url(url, reason=body, write=True)
    decision = result.get("decision")
    track = result.get("track") or "web"
    if decision == "accept_candidate":
        entry = result.get("entry") or {}
        comment = (
            f"✅ 已入 **{track} candidate**：`{entry.get('id')}`\n"
            f"- track: {track}\n"
            f"- url: {entry.get('url') or (entry.get('source') or {}).get('install_locator')}\n"
            f"- kind: {entry.get('kind')}\n"
            f"- covers: {', '.join(entry.get('covers') or [])}\n"
            f"- security_review: {entry.get('security_review_id') or (result.get('security_admission') or {}).get('review_id')}\n"
            f"- label: {result.get('label_source')}"
        )
    elif decision == "duplicate":
        comment = f"⏭️ 重复：已在池或墓碑中 — `{result.get('duplicate')}`"
    elif decision == "rejected_landing_freeze":
        comment = "🚫 当前冻结普通 landing 新站（Web 轨；见 STATUS.md）。已记入 graveyard（landing_freeze）。"
    elif decision == "pending_security_review":
        adm = result.get("security_admission") or {}
        comment = (
            "🛡️ **pending_security_review**：缺少与内容绑定的已提交 security review，"
            "或 review 已过期/不足。Issue 正文自称 approved **无效**。"
            f"轨：`{track}`。未写入 candidate/core。\n"
            f"- admission: `{adm.get('status')}` — {adm.get('reason')}\n"
            f"- ignored_issue_claims: {adm.get('ignored_issue_claims') or []}\n"
            "请维护者在 `security-reviews/` 提交 review 后再投喂。"
        )
    elif decision == "rejected_security_blocked":
        adm = result.get("security_admission") or {}
        comment = (
            "🚫 **rejected_security_blocked**：存在 conclusion=block 的 security review。"
            f"轨：`{track}`。不可自动入 candidate/core。\n"
            f"- review: `{adm.get('review_id')}` — {adm.get('reason')}"
        )
    elif decision == "needs_human":
        write_err = result.get("write_error")
        extra = f"\n- write_error: {write_err}" if write_err else ""
        comment = (
            "👀 **needs_human**：初筛无法自动确认（弱 HTML / SPA / 缺 covers"
            f"{' / 席位满' if write_err else ''}）。"
            f"轨：`{track}`。不会写入墓碑。请维护者人工看一眼。{extra}\n"
            f"```json\n{json.dumps(result.get('draft') or result, ensure_ascii=False, indent=2)}\n```"
        )
    else:
        comment = f"结论：`{decision}`\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"

    result["comment"] = comment
    Path("/tmp/triage-result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(comment)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="design-for-you triage")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("triage", help="Triage one URL")
    t.add_argument("--url", required=True)
    t.add_argument("--reason", default="")
    t.add_argument("--name", default=None)
    t.add_argument("--auth", default=None)
    t.add_argument(
        "--track",
        choices=["web", "video", "skill"],
        default=None,
        help="Override track (default: parse issue body, else web)",
    )
    t.add_argument("--write", action="store_true")

    sub.add_parser(
        "refresh-status",
        help="Rewrite STATUS.md from sites.yaml + videos.yaml + skills.yaml",
    )
    sub.add_parser("inbox", help="Actions: triage from ISSUE_TITLE/BODY env")

    c = sub.add_parser("counts", help="Print seat counts JSON")
    c.add_argument(
        "--track",
        choices=["web", "video", "skill", "all"],
        default="all",
        help="Which track counts to print (default: all)",
    )

    args = p.parse_args(argv)

    if args.cmd == "refresh-status":
        refresh_status()
        return 0
    if args.cmd == "counts":
        if args.track == "all":
            out = {
                "web": seat_counts(track="web"),
                "video": seat_counts(track="video"),
                "skill": seat_counts(track="skill"),
            }
        else:
            out = seat_counts(track=args.track)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "inbox":
        return cmd_inbox_from_env()
    if args.cmd == "triage":
        out = triage_url(
            args.url,
            reason=args.reason,
            name=args.name,
            auth_hint=args.auth,
            write=args.write,
            track=args.track,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
