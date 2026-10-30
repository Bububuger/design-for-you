#!/usr/bin/env python3
"""design-for-you triage: URL normalize, dup/graveyard check, loose gallery gate,
optional LLM covers, STATUS.md generation. Shared by local Skill and Actions.
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

ROOT = Path(__file__).resolve().parents[1]
SITES_PATH = ROOT / "sites.yaml"
GRAVEYARD_PATH = ROOT / "graveyard.yaml"
STATUS_PATH = ROOT / "STATUS.md"

SEAT_QUOTAS = {
    "product-flow": 10,
    "component": 12,
    "landing": 8,
    "system": 4,
}
CANDIDATE_CAP = 20
CORE_CAP = 30

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
    """Strip tracking params; optionally follow redirects to final URL."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

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


def list_graveyard() -> list[dict]:
    data = load_yaml(GRAVEYARD_PATH)
    if isinstance(data, dict):
        return list(data.get("sites") or [])
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


def find_duplicate(url: str) -> dict | None:
    d = domain_of(url)
    for site in list_sites():
        if urls_match(url, site.get("url", "")):
            return {"where": "sites", "id": site.get("id"), "status": site.get("status")}
        for alias in site.get("aliases") or []:
            if urls_match(url, alias):
                return {"where": "sites", "id": site.get("id"), "status": site.get("status")}
    for g in list_graveyard():
        if g.get("url") and urls_match(url, g["url"]):
            return {"where": "graveyard", "reason": g.get("reason"), "entry": g}
        gd = g.get("domain") or domain_of(g.get("url", "") or "")
        if not gd or gd != d:
            continue
        # github.com domain alone must not collide every repo; need URL key.
        if gd in ("github.com", "www.github.com"):
            continue
        return {"where": "graveyard", "reason": g.get("reason"), "entry": g}
    return None


def fetch_html(url: str, timeout: int = 20) -> tuple[str | None, int | None, str | None]:
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
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


def rule_covers_from_text(text: str, reason: str = "") -> list[str]:
    blob = f"{text}\n{reason}".lower()
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
        "landing-page": ["landing", "落地页"],
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
    }
    found: list[str] = []
    for tag, keys in lexicon.items():
        if any(k in blob for k in keys):
            found.append(tag)
    return found[:12]


def llm_covers_and_hint(
    url: str, html_snippet: str, reason: str
) -> dict | None:
    """Optional LLM assist. Returns None if no key / failure → caller falls back."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    prompt = (
        "You label design-inspiration gallery sites for a retrieval pool.\n"
        f"URL: {url}\n"
        f"Submitter reason: {reason}\n"
        f"HTML/text snippet:\n{html_snippet[:6000]}\n\n"
        "Reply JSON only with keys: covers (array of short kebab-case tags), "
        "search_hint (one Chinese or English sentence on how to search in-site), "
        "kind (one of product-flow|component|landing|system).\n"
        "If this is a plain marketing landing for a single product (not a multi-case "
        "gallery), set covers to [] and kind to landing."
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


def seat_counts(sites: list[dict] | None = None) -> dict:
    sites = sites if sites is not None else list_sites()
    core = [s for s in sites if s.get("status") == "core"]
    cand = [s for s in sites if s.get("status") == "candidate"]
    by_kind: dict[str, int] = {k: 0 for k in SEAT_QUOTAS}
    for s in core:
        k = s.get("kind") or "component"
        by_kind[k] = by_kind.get(k, 0) + 1
    return {
        "core_total": len(core),
        "candidate_total": len(cand),
        "by_kind": by_kind,
    }


def generate_status_md(
    miss_terms: list[str] | None = None,
    freeze_landing: bool = True,
) -> str:
    counts = seat_counts()
    by = counts["by_kind"]
    lines = [
        "# Design For You 缺口悬赏单",
        "",
        f"> 自动生成于 {date.today().isoformat()}。",
    ]
    if freeze_landing:
        lines.append(
            "> **暂不接收普通 `landing`（整站/营销落地页）新站。** landing 席位已超配或接近满席，冻结新增。"
        )
    lines += [
        "",
        "## 席位余量（Core）",
        "",
        "| 分类 | 配额 | 已用 | 余量 | 状态 |",
        "| :--- | ---: | ---: | ---: | :--- |",
    ]
    for kind, quota in SEAT_QUOTAS.items():
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
        f"| **Core 合计** | **≤{CORE_CAP}** | **{counts['core_total']}** | — | — |",
        f"| candidate 池 | {CANDIDATE_CAP} | {counts['candidate_total']} | "
        f"{CANDIDATE_CAP - counts['candidate_total']} | "
        f"{'有空位' if counts['candidate_total'] < CANDIDATE_CAP else '满'} |",
        "",
        "## 首期定向悬赏（高优）",
        "",
        "投喂：Issue 标题=URL，标签=`inbox`，正文=原因/`covers`。",
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


def add_to_graveyard(url: str, reason: str, notes: str = "") -> None:
    entries = list_graveyard()
    entries.append(
        {
            "domain": domain_of(url),
            "url": url,
            "reason": reason,
            "rejected_at": date.today().isoformat(),
            "cooldown_until": f"{date.today().year}-12-31",
            "notes": notes,
        }
    )
    save_graveyard(entries)


def add_candidate(entry: dict) -> None:
    sites = list_sites()
    if seat_counts(sites)["candidate_total"] >= CANDIDATE_CAP:
        raise RuntimeError("candidate pool full")
    # landing freeze for new submissions
    if entry.get("kind") == "landing":
        raise RuntimeError("landing submissions frozen; refuse ordinary landing")
    sites.append(entry)
    save_yaml(SITES_PATH, sites)


def triage_url(
    url: str,
    reason: str = "",
    name: str | None = None,
    auth_hint: str | None = None,
    write: bool = False,
) -> dict:
    result: dict[str, Any] = {"input_url": url, "reason": reason}
    try:
        normalized = normalize_url(url)
    except Exception as e:  # noqa: BLE001
        normalized = url.strip()
        result["normalize_error"] = str(e)
    result["url"] = normalized

    dup = find_duplicate(normalized)
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

    llm = llm_covers_and_hint(result["url"], html[:8000], reason)
    if llm:
        covers = list(llm.get("covers") or [])
        search_hint = llm.get("search_hint") or reason or "浏览画廊"
        kind = llm.get("kind") or "component"
        result["label_source"] = "llm"
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
        if not covers:
            result["decision"] = "needs_human"
            result["note"] = "weak_covers_no_llm"
            # still attach draft for human
            result["draft"] = {
                "id": slug_id(result["url"], name),
                "name": name or domain_of(result["url"]),
                "url": result["url"],
                "aliases": [],
                "status": "candidate",
                "kind": kind,
                "covers": covers,
                "search_hint": search_hint,
                "auth": auth,
                "added_at": date.today().isoformat(),
            }
            return result

    if kind == "landing":
        result["decision"] = "rejected_landing_freeze"
        if write:
            add_to_graveyard(
                result["url"],
                "landing_freeze",
                notes="ordinary landing frozen at intake",
            )
        return result

    if gate["verdict"] == "needs_human" and result.get("label_source") == "rules":
        # Keep human path unless LLM + strong score
        result["decision"] = "needs_human"
        result["draft"] = {
            "id": slug_id(result["url"], name),
            "name": name or domain_of(result["url"]),
            "url": result["url"],
            "aliases": [],
            "status": "candidate",
            "kind": kind,
            "covers": covers,
            "search_hint": search_hint,
            "auth": auth,
            "added_at": date.today().isoformat(),
        }
        return result

    entry = {
        "id": slug_id(result["url"], name),
        "name": name or domain_of(result["url"]),
        "url": result["url"],
        "aliases": [],
        "status": "candidate",
        "kind": kind,
        "covers": covers,
        "search_hint": search_hint,
        "auth": auth,
        "added_at": date.today().isoformat(),
    }
    result["entry"] = entry

    if gate["verdict"] == "pass" or result.get("label_source") == "llm":
        result["decision"] = "accept_candidate"
        if write:
            try:
                add_candidate(entry)
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
    if decision == "accept_candidate":
        comment = (
            f"✅ 已入 **candidate**：`{result['entry']['id']}`\n"
            f"- url: {result['entry']['url']}\n"
            f"- kind: {result['entry']['kind']}\n"
            f"- covers: {', '.join(result['entry'].get('covers') or [])}\n"
            f"- label: {result.get('label_source')}"
        )
    elif decision == "duplicate":
        comment = f"⏭️ 重复：已在池或墓碑中 — `{result.get('duplicate')}`"
    elif decision == "rejected_landing_freeze":
        comment = "🚫 当前冻结普通 landing 新站（见 STATUS.md）。已记入 graveyard（landing_freeze）。"
    elif decision == "needs_human":
        comment = (
            "👀 **needs_human**：初筛无法自动确认（弱 HTML / SPA / 缺 covers）。"
            "不会写入墓碑。请维护者人工看一眼。\n"
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
    t.add_argument("--write", action="store_true")

    sub.add_parser("refresh-status", help="Rewrite STATUS.md from sites.yaml")
    sub.add_parser("inbox", help="Actions: triage from ISSUE_TITLE/BODY env")

    c = sub.add_parser("counts", help="Print seat counts JSON")

    args = p.parse_args(argv)

    if args.cmd == "refresh-status":
        refresh_status()
        return 0
    if args.cmd == "counts":
        print(json.dumps(seat_counts(), ensure_ascii=False, indent=2))
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
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
