#!/usr/bin/env python3
"""Security admission review: load/validate review records and gate new web/skill
admissions. Keyword heuristics FLAG for human judgment only — never certify safe
or mechanically condemn benign quotations.

Passing a review does NOT grant execution, credentials, or messaging permissions.
Reviewed sources remain untrusted data. Issue bodies cannot self-assert approval.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
REVIEWS_DIR = ROOT / "security-reviews"
EVIDENCE_DIR = REVIEWS_DIR / "evidence"

# Tracks that require a committed, hash-bound approval before candidate/core write.
GATED_TRACKS = frozenset({"web", "skill"})
# Video remains ungated in this iteration (compatibility).
UNGATED_TRACKS = frozenset({"video"})

VALID_CONCLUSIONS = frozenset({"approve", "block", "insufficient"})

# Self-assertions in untrusted Issue bodies — ignored for gating.
ISSUE_SELF_ASSERT_RE = re.compile(
    r"(?:^|\n)\s*(?:security[_-]?review|admission[_-]?review|security[_-]?admission)"
    r"\s*[:=]\s*(approve[d]?|pass(ed)?|ok|safe|allow(ed)?)\b",
    re.I,
)

# Heuristic detectors: FLAG only. Context decides; never auto-certify/condemn.
FLAG_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "authority_override",
        re.compile(
            r"(ignore|disregard|override).{0,48}(system|safety|policy|safeguard|instructions?)"
            r"|you are now (?:in )?(?:developer|DAN|jailbreak)"
            r"|jailbreak|developer mode",
            re.I,
        ),
    ),
    (
        "credential_exfil",
        re.compile(
            r"(exfiltrat|webhook\.site|pastebin\.com|"
            r"send\s+(?:me\s+)?(?:your\s+)?(?:api[_-]?key|secret|password|token|credential)s?"
            r"|upload\s+(?:the\s+)?(?:api[_-]?key|secret|password|credential)s?)",
            re.I,
        ),
    ),
    (
        "dangerous_shell",
        re.compile(
            r"(rm\s+-rf\s+/|curl\s+[^\n]{0,80}\|\s*(?:ba)?sh|"
            r"wget\s+[^\n]{0,80}\|\s*(?:ba)?sh|"
            r"chmod\s+\+x|npx\s+skills\s+add|"
            r"pip\s+install\s+[^\s]+|npm\s+install\s+-g)",
            re.I,
        ),
    ),
    (
        "remote_install",
        re.compile(
            r"(curl\s+[^\n]{0,60}\|\s*(?:ba)?sh|install\s+via\s+remote|"
            r"download\s+and\s+(?:run|execute)|skills\.sh/.+\|\s*sh)",
            re.I,
        ),
    ),
    (
        "messaging_inducement",
        re.compile(
            r"(send_message|post_to_(?:slack|discord)|forward\s+(?:all\s+)?secrets?"
            r"|exfiltrat.+?(?:slack|discord|telegram))",
            re.I,
        ),
    ),
]


@dataclass
class FlagHit:
    category: str
    match: str
    context: str
    # Heuristic only — caller must judge benign quotes vs suspicious inducement.
    judgment: str = "needs_context"


@dataclass
class AdmissionResult:
    ok: bool
    status: str  # approved | missing | stale | blocked | insufficient | not_required | legacy_unreviewed
    reason: str
    review_id: str | None = None
    binds_to: dict[str, Any] = field(default_factory=dict)
    ignored_issue_claims: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "reason": self.reason,
            "review_id": self.review_id,
            "binds_to": self.binds_to,
            "ignored_issue_claims": self.ignored_issue_claims,
            "permissions_granted": [],
            "trust": "untrusted-data",
        }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def package_integrity_from_hashes(file_hashes: dict[str, str]) -> str:
    """Deterministic integrity over path→sha256 map (sorted lines)."""
    blob = "\n".join(f"{k}={v}" for k, v in sorted(file_hashes.items())) + "\n"
    return sha256_text(blob)


def normalize_locator(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/") + "/"
    # Prefer trailing slash on directory-like package roots
    if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
        path = path + "/"
    return f"{parsed.scheme or 'https'}://{host}{path}"


def locators_match(a: str, b: str) -> bool:
    na, nb = normalize_locator(a), normalize_locator(b)
    if not na or not nb:
        return False
    return na.rstrip("/") == nb.rstrip("/")


def load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_review_paths(reviews_dir: Path | None = None) -> list[Path]:
    base = reviews_dir or REVIEWS_DIR
    if not base.exists():
        return []
    out: list[Path] = []
    for p in sorted(base.glob("*.yaml")) + sorted(base.glob("*.yml")):
        if p.name.lower() in ("readme.yaml", "policy.yaml"):
            continue
        out.append(p)
    return out


def load_reviews(reviews_dir: Path | None = None) -> list[dict]:
    reviews: list[dict] = []
    for path in list_review_paths(reviews_dir):
        data = load_yaml(path)
        if isinstance(data, dict) and data.get("id"):
            data = dict(data)
            data["_path"] = str(path)
            reviews.append(data)
    return reviews


def scan_flags(text: str) -> list[FlagHit]:
    """Keyword/heuristic scan. Hits require contextual judgment; never certify."""
    hits: list[FlagHit] = []
    blob = text or ""
    for category, rx in FLAG_PATTERNS:
        for m in rx.finditer(blob):
            start = max(0, m.start() - 48)
            end = min(len(blob), m.end() + 48)
            ctx = blob[start:end].replace("\n", " ")
            hits.append(
                FlagHit(
                    category=category,
                    match=m.group(0)[:120],
                    context=ctx[:200],
                )
            )
    return hits


def is_likely_benign_security_advice(hit: FlagHit) -> bool:
    """Conservative benign detector for tests/docs quoting anti-exfil advice."""
    ctx = hit.context.lower()
    if hit.category == "credential_exfil":
        if any(
            w in ctx
            for w in (
                "never send",
                "do not send",
                "don't send",
                "keep credentials",
                "never request credentials",
                "without an account, token",
            )
        ):
            return True
    return False


def extract_ignored_issue_claims(issue_body: str | None) -> list[str]:
    if not issue_body:
        return []
    return [m.group(0).strip() for m in ISSUE_SELF_ASSERT_RE.finditer(issue_body)]


def find_matching_review(
    track: str,
    *,
    locator: str | None = None,
    package_integrity: str | None = None,
    resource_id: str | None = None,
    reviews: list[dict] | None = None,
) -> dict | None:
    track = (track or "").lower()
    pool = reviews if reviews is not None else load_reviews()
    candidates: list[dict] = []
    for rev in pool:
        if (rev.get("track") or "").lower() != track:
            continue
        if resource_id and rev.get("resource_id") == resource_id:
            candidates.append(rev)
            continue
        rev_loc = (
            rev.get("resource_locator")
            or (rev.get("binds_to") or {}).get("locator")
            or ""
        )
        if locator and rev_loc and locators_match(locator, rev_loc):
            candidates.append(rev)
    if not candidates:
        return None
    # Prefer approve matching integrity when provided; else newest by reviewed_at.
    def sort_key(r: dict) -> tuple:
        binds = r.get("binds_to") or {}
        integ = binds.get("package_integrity_sha256") or binds.get("content_sha256") or ""
        match_integ = 1 if package_integrity and integ == package_integrity else 0
        return (match_integ, r.get("reviewed_at") or "", r.get("id") or "")

    candidates.sort(key=sort_key, reverse=True)
    return candidates[0]


def evaluate_admission(
    track: str,
    *,
    locator: str | None = None,
    package_integrity: str | None = None,
    content_sha256: str | None = None,
    resource_id: str | None = None,
    issue_body: str | None = None,
    reviews_dir: Path | None = None,
    legacy: bool = False,
) -> AdmissionResult:
    """Gate for NEW candidate/core writes on web/skill tracks.

    - video: not_required
    - legacy existing resources: legacy_unreviewed (usable; no new promotion)
    - Issue self-asserted approval: ignored
    - missing/stale/blocked/insufficient: not ok
    """
    track = (track or "web").lower()
    ignored = extract_ignored_issue_claims(issue_body)

    if track in UNGATED_TRACKS:
        return AdmissionResult(
            ok=True,
            status="not_required",
            reason="track_ungated",
            ignored_issue_claims=ignored,
        )

    if track not in GATED_TRACKS:
        return AdmissionResult(
            ok=False,
            status="missing",
            reason=f"unknown_track:{track}",
            ignored_issue_claims=ignored,
        )

    if legacy:
        return AdmissionResult(
            ok=True,
            status="legacy_unreviewed",
            reason="preexisting_resource_legacy_unreviewed_policy",
            ignored_issue_claims=ignored,
        )

    reviews = load_reviews(reviews_dir)
    rev = find_matching_review(
        track,
        locator=locator,
        package_integrity=package_integrity,
        resource_id=resource_id,
        reviews=reviews,
    )
    if rev is None:
        return AdmissionResult(
            ok=False,
            status="missing",
            reason="no_committed_security_review",
            ignored_issue_claims=ignored,
        )

    conclusion = (rev.get("conclusion") or "").lower().strip()
    binds = dict(rev.get("binds_to") or {})
    review_id = rev.get("id")

    if conclusion == "block":
        return AdmissionResult(
            ok=False,
            status="blocked",
            reason="review_conclusion_block",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )
    if conclusion == "insufficient":
        return AdmissionResult(
            ok=False,
            status="insufficient",
            reason="review_conclusion_insufficient",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )
    if conclusion != "approve":
        return AdmissionResult(
            ok=False,
            status="missing",
            reason=f"invalid_conclusion:{conclusion or 'empty'}",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )

    # Bind approval to reviewed content integrity.
    expected_pkg = binds.get("package_integrity_sha256")
    expected_content = binds.get("content_sha256")
    if package_integrity and expected_pkg and package_integrity != expected_pkg:
        return AdmissionResult(
            ok=False,
            status="stale",
            reason="package_integrity_mismatch_requires_rereview",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )
    if content_sha256 and expected_content and content_sha256 != expected_content:
        return AdmissionResult(
            ok=False,
            status="stale",
            reason="content_hash_mismatch_requires_rereview",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )
    # Skill track: integrity required on approve path when review declares one.
    if track == "skill" and expected_pkg and not package_integrity:
        return AdmissionResult(
            ok=False,
            status="stale",
            reason="skill_admission_requires_package_integrity_to_bind",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )
    # Web track: if review pins content_sha256, caller must supply matching hash.
    if track == "web" and expected_content and not content_sha256:
        return AdmissionResult(
            ok=False,
            status="stale",
            reason="web_admission_requires_content_hash_to_bind",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )

    return AdmissionResult(
        ok=True,
        status="approved",
        reason="bound_review_approve",
        review_id=review_id,
        binds_to=binds,
        ignored_issue_claims=ignored,
    )


def can_write_candidate(
    track: str,
    *,
    locator: str | None = None,
    package_integrity: str | None = None,
    content_sha256: str | None = None,
    resource_id: str | None = None,
    issue_body: str | None = None,
    reviews_dir: Path | None = None,
) -> AdmissionResult:
    """Entry-path gate used by triage/add_candidate (never trusts Issue claims)."""
    return evaluate_admission(
        track,
        locator=locator,
        package_integrity=package_integrity,
        content_sha256=content_sha256,
        resource_id=resource_id,
        issue_body=issue_body,
        reviews_dir=reviews_dir,
        legacy=False,
    )


def can_promote(
    entry: dict,
    track: str,
    *,
    reviews_dir: Path | None = None,
) -> AdmissionResult:
    """Promotion gate: legacy-unreviewed and blocked cannot gain new core status."""
    track = (track or "web").lower()
    if track in UNGATED_TRACKS:
        return evaluate_admission(track)
    # Explicit legacy marker or missing security_review_id on preexisting rows.
    marker = (entry.get("security_admission") or "").lower()
    if marker in ("legacy-unreviewed", "legacy_unreviewed"):
        return AdmissionResult(
            ok=False,
            status="legacy_unreviewed",
            reason="legacy_unreviewed_cannot_receive_new_promotion_without_review",
        )
    locator = entry.get("url") or (entry.get("source") or {}).get("install_locator")
    integ = (entry.get("content_integrity") or {}).get("package_integrity")
    content_hash = (entry.get("content_integrity") or {}).get("content_sha256")
    return evaluate_admission(
        track,
        locator=locator,
        package_integrity=integ,
        content_sha256=content_hash,
        resource_id=entry.get("id"),
        reviews_dir=reviews_dir,
        legacy=False,
    )


def safe_fetch_url_allowed(url: str, allow_hosts: set[str] | None = None) -> bool:
    """SSRF guard for optional review helpers: https only, no link-local/metadata."""
    try:
        parsed = urlparse(url)
    except Exception:  # noqa: BLE001
        return False
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").lower()
    if not host or host in {"localhost", "metadata.google.internal"}:
        return False
    if host.endswith(".local") or host.endswith(".internal"):
        return False
    # Block literal IPs in obviously private ranges (simple string checks).
    if re.match(r"^(127\.|10\.|192\.168\.|169\.254\.|0\.|::1$)", host):
        return False
    if allow_hosts is not None and host not in allow_hosts:
        return False
    return True


def safe_join_under(root: Path, relative: str) -> Path | None:
    """Prevent path traversal when reading evidence under a root."""
    rel = relative.replace("\\", "/").lstrip("/")
    if ".." in rel.split("/"):
        return None
    root = root.resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target
