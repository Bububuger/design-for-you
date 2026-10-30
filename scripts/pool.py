#!/usr/bin/env python3
"""design-for-you local helpers: 4 Core + 1 Candidate select, log receipts,
Chrome bookmark diff stub.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SITES_PATH = ROOT / "sites.yaml"
LOGS_DIR = ROOT / "logs"

# Chrome bookmark path convention (macOS default; Linux Chromium variants listed).
# This is a READ-ONLY inbox — never write back to Chrome Bookmarks JSON.
CHROME_BOOKMARK_CANDIDATES = [
    Path.home() / "Library/Application Support/Google/Chrome/Default/Bookmarks",
    Path.home() / ".config/google-chrome/Default/Bookmarks",
    Path.home() / ".config/chromium/Default/Bookmarks",
]
# Folder path expected for inspiration bookmarks (names may vary by locale):
# Bookmarks Bar / 🤖 AI 与设计 / ✨ 审美与设计灵感
BOOKMARK_FOLDER_HINTS = ("审美与设计灵感", "设计灵感", "design inspiration")


def load_sites() -> list[dict]:
    with SITES_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return data if isinstance(data, list) else []


def tokenize(query: str) -> list[str]:
    parts = re.split(r"[\s,;/|]+", query.lower().strip())
    return [p for p in parts if p]


def score_site(site: dict, tokens: list[str]) -> int:
    covers = [str(c).lower() for c in (site.get("covers") or [])]
    blob = " ".join(
        [
            site.get("id", ""),
            site.get("name", ""),
            site.get("kind", ""),
            site.get("search_hint", ""),
            " ".join(covers),
        ]
    ).lower()
    score = 0
    for t in tokens:
        if t in covers:
            score += 3
        elif t in blob:
            score += 1
        # soft prefix match on covers
        for c in covers:
            if c.startswith(t) or t.startswith(c):
                score += 1
                break
    return score


def select_pool(query: str, max_core: int = 4, max_candidate: int = 1) -> dict:
    """Pick up to 4 core + 1 candidate by covers/query match."""
    tokens = tokenize(query)
    sites = load_sites()
    core = [s for s in sites if s.get("status") == "core"]
    cand = [s for s in sites if s.get("status") == "candidate"]

    def ranked(pool: list[dict]) -> list[tuple[int, dict]]:
        scored = [(score_site(s, tokens), s) for s in pool]
        scored.sort(key=lambda x: (-x[0], x[1].get("id", "")))
        # Prefer positive scores; if all zero, still return top by stable id for diversity
        positive = [x for x in scored if x[0] > 0]
        return positive if positive else scored

    picked_core = [s for _, s in ranked(core)[:max_core]]
    picked_cand = [s for _, s in ranked(cand)[:max_candidate]]

    return {
        "query": query,
        "tokens": tokens,
        "core": [
            {
                "id": s["id"],
                "name": s["name"],
                "url": s["url"],
                "kind": s.get("kind"),
                "covers": s.get("covers"),
                "search_hint": s.get("search_hint"),
                "auth": s.get("auth"),
                "score": score_site(s, tokens),
            }
            for s in picked_core
        ],
        "candidate": [
            {
                "id": s["id"],
                "name": s["name"],
                "url": s["url"],
                "kind": s.get("kind"),
                "covers": s.get("covers"),
                "search_hint": s.get("search_hint"),
                "auth": s.get("auth"),
                "score": score_site(s, tokens),
            }
            for s in picked_cand
        ],
    }


def append_log(
    query: str,
    hits: list[str],
    misses: list[str],
    selected: list[str] | None = None,
    notes: str = "",
) -> Path:
    """Append one receipt to logs/YYYY-MM.jsonl (append-only)."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    path = LOGS_DIR / f"{now.strftime('%Y-%m')}.jsonl"
    record = {
        "ts": now.isoformat(),
        "query": query,
        "selected": selected or [],
        "hits": hits,
        "misses": misses,
        "notes": notes,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def _walk_bookmark_nodes(node: Any, path: list[str], out: list[dict]) -> None:
    if not isinstance(node, dict):
        return
    name = node.get("name") or ""
    ntype = node.get("type")
    if ntype == "url":
        out.append({"name": name, "url": node.get("url"), "folder_path": list(path)})
        return
    children = node.get("children") or []
    new_path = path + ([name] if name else [])
    for child in children:
        _walk_bookmark_nodes(child, new_path, out)


def scan_chrome_bookmarks_diff(
    bookmark_file: Path | None = None,
) -> dict:
    """Stub / helper: read Chrome Bookmarks JSON and list URLs under inspiration folders
    that are not yet in sites.yaml / graveyard.

    Path convention (read-only):
      macOS: ~/Library/Application Support/Google/Chrome/Default/Bookmarks
      Linux: ~/.config/google-chrome/Default/Bookmarks

    Only folders whose path contains one of BOOKMARK_FOLDER_HINTS are considered.
    Does NOT modify Chrome files. Callers should POST new URLs via inbox Issues
    or pipe into triage.py — never concurrent-write sites.yaml from mobile PAs.
    """
    path = bookmark_file
    if path is None:
        for c in CHROME_BOOKMARK_CANDIDATES:
            if c.exists():
                path = c
                break
    if path is None or not path.exists():
        return {
            "ok": False,
            "error": "chrome_bookmarks_not_found",
            "tried": [str(p) for p in CHROME_BOOKMARK_CANDIDATES],
            "new_urls": [],
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"ok": False, "error": str(e), "new_urls": []}

    roots = (data.get("roots") or {})
    found: list[dict] = []
    for key in ("bookmark_bar", "other", "synced"):
        if key in roots:
            _walk_bookmark_nodes(roots[key], [key], found)

    known_domains: set[str] = set()
    try:
        from triage import domain_of, list_graveyard, list_sites  # type: ignore

        for s in list_sites():
            known_domains.add(domain_of(s.get("url", "")))
            for a in s.get("aliases") or []:
                known_domains.add(domain_of(a))
        for g in list_graveyard():
            known_domains.add(g.get("domain") or domain_of(g.get("url", "")))
    except Exception:
        # Fallback: domains from sites.yaml only
        from urllib.parse import urlparse

        for s in load_sites():
            host = urlparse(s.get("url", "")).netloc.lower().removeprefix("www.")
            known_domains.add(host)

    new_urls = []
    for item in found:
        folder = "/".join(item.get("folder_path") or [])
        if not any(h in folder for h in BOOKMARK_FOLDER_HINTS):
            continue
        url = item.get("url") or ""
        if not url.startswith("http"):
            continue
        from urllib.parse import urlparse

        host = urlparse(url).netloc.lower().removeprefix("www.")
        if host in known_domains:
            continue
        new_urls.append({"name": item.get("name"), "url": url, "folder": folder})

    return {
        "ok": True,
        "bookmark_file": str(path),
        "scanned": len(found),
        "new_urls": new_urls,
        "note": "Read-only diff. Feed new_urls via inbox Issues or triage.py --write.",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="design-for-you local pool helpers")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("select", help="Select up to 4 core + 1 candidate")
    s.add_argument("--query", required=True)
    s.add_argument("--max-core", type=int, default=4)
    s.add_argument("--max-candidate", type=int, default=1)

    lg = sub.add_parser("log", help="Append a retrieval receipt to logs/YYYY-MM.jsonl")
    lg.add_argument("--query", required=True)
    lg.add_argument("--hits", default="", help="comma-separated site ids that hit")
    lg.add_argument("--misses", default="", help="comma-separated miss terms")
    lg.add_argument("--selected", default="", help="comma-separated selected ids")
    lg.add_argument("--notes", default="")

    sub.add_parser(
        "scan-bookmarks",
        help="Diff local Chrome bookmarks vs pool (read-only stub)",
    )

    args = p.parse_args(argv)

    if args.cmd == "select":
        out = select_pool(args.query, args.max_core, args.max_candidate)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "log":
        path = append_log(
            query=args.query,
            hits=[x for x in args.hits.split(",") if x],
            misses=[x for x in args.misses.split(",") if x],
            selected=[x for x in args.selected.split(",") if x],
            notes=args.notes,
        )
        print(f"appended {path}")
        return 0
    if args.cmd == "scan-bookmarks":
        print(json.dumps(scan_chrome_bookmarks_diff(), ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
