#!/usr/bin/env python3
"""Security admission review: load/validate review records and gate new web/skill
admissions. Keyword heuristics FLAG for human judgment only — never certify safe
or mechanically condemn benign quotations.

Passing a review does NOT grant execution, credentials, or messaging permissions.
Reviewed sources remain untrusted data. Issue bodies cannot self-assert approval.

Approval binds ONLY to a pinned snapshot (track + resource_id + locator + content
integrity). Live host drift is NOT automatically detected; re-review is required
when content changes. Issue-supplied hashes are not trusted unless they match the
committed review pin for that exact identity/locator.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
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
# Video remains ungated in this iteration (compatibility). Video membership does
# NOT grant web/skill security permission.
UNGATED_TRACKS = frozenset({"video"})

VALID_CONCLUSIONS = frozenset({"approve", "block", "insufficient"})
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

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
    status: str  # approved | missing | stale | blocked | insufficient | not_required | legacy_unreviewed | invalid_review
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
            "snapshot_only": True,
        }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def is_sha256_hex(value: str | None) -> bool:
    return bool(value and SHA256_RE.match(value))


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


def review_locator(rev: dict) -> str:
    return (
        rev.get("resource_locator")
        or (rev.get("binds_to") or {}).get("locator")
        or ""
    )


def required_pin_field(track: str) -> str:
    return (
        "package_integrity_sha256" if track == "skill" else "content_sha256"
    )


def review_pin(rev: dict, track: str) -> str | None:
    binds = rev.get("binds_to") or {}
    if not isinstance(binds, dict) or not binds:
        return None
    value = binds.get(required_pin_field(track))
    if is_sha256_hex(value):
        return value
    return None


def find_matching_review(
    track: str,
    *,
    locator: str | None = None,
    resource_id: str | None = None,
    reviews: list[dict] | None = None,
) -> dict | None:
    """Match ONLY when track + resource_id + locator all agree (AND, not OR)."""
    track = (track or "").lower()
    if not resource_id or not locator:
        return None
    pool = reviews if reviews is not None else load_reviews()
    matches: list[dict] = []
    for rev in pool:
        if (rev.get("track") or "").lower() != track:
            continue
        if rev.get("resource_id") != resource_id:
            continue
        rev_loc = review_locator(rev)
        if not rev_loc or not locators_match(locator, rev_loc):
            continue
        matches.append(rev)
    if not matches:
        return None
    matches.sort(key=lambda r: (r.get("reviewed_at") or "", r.get("id") or ""), reverse=True)
    return matches[0]


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

    Approve requires:
      track + resource_id + locator match a committed review AND
      nonempty track-specific binds_to pin AND
      caller-supplied integrity evidence equals that pin.

    - video: not_required (ungated; does not imply web/skill permission)
    - legacy flag: legacy_unreviewed (usable; no new promotion)
    - Issue self-asserted approval: ignored
    """
    track = (track or "web").lower()
    ignored = extract_ignored_issue_claims(issue_body)

    if track in UNGATED_TRACKS:
        return AdmissionResult(
            ok=True,
            status="not_required",
            reason="track_ungated_video_does_not_imply_web_or_skill_permission",
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

    if not resource_id or not locator:
        return AdmissionResult(
            ok=False,
            status="missing",
            reason="admission_requires_resource_id_and_locator",
            ignored_issue_claims=ignored,
        )

    reviews = load_reviews(reviews_dir)
    rev = find_matching_review(
        track,
        locator=locator,
        resource_id=resource_id,
        reviews=reviews,
    )
    if rev is None:
        return AdmissionResult(
            ok=False,
            status="missing",
            reason="no_review_matching_track_id_and_locator",
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
            status="invalid_review",
            reason=f"invalid_conclusion:{conclusion or 'empty'}",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )

    if not binds:
        return AdmissionResult(
            ok=False,
            status="invalid_review",
            reason="approve_requires_nonempty_binds_to",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )

    expected = review_pin(rev, track)
    if not expected:
        field = required_pin_field(track)
        return AdmissionResult(
            ok=False,
            status="invalid_review",
            reason=f"approve_requires_valid_{field}",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )

    provided = package_integrity if track == "skill" else content_sha256
    if not provided:
        return AdmissionResult(
            ok=False,
            status="stale",
            reason=f"missing_input_{required_pin_field(track)}_evidence",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )
    if not is_sha256_hex(provided):
        return AdmissionResult(
            ok=False,
            status="invalid_review",
            reason="input_integrity_not_sha256_hex",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )
    if provided != expected:
        return AdmissionResult(
            ok=False,
            status="stale",
            reason="integrity_mismatch_requires_rereview",
            review_id=review_id,
            binds_to=binds,
            ignored_issue_claims=ignored,
        )

    return AdmissionResult(
        ok=True,
        status="approved",
        reason="bound_review_approve_track_id_locator_content",
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


def is_legacy_unreviewed_entry(entry: dict) -> bool:
    """Explicit legacy policy: missing admission fields mean legacy-unreviewed."""
    marker = (entry.get("security_admission") or "").lower().replace("_", "-")
    if marker in ("legacy-unreviewed",):
        return True
    if entry.get("security_review_id"):
        return False
    if marker in ("reviewed-approve-bound", "approved", "reviewed"):
        return False
    # No review id and no positive reviewed marker → legacy-unreviewed.
    return marker in ("", "legacy-unreviewed")


def can_promote(
    entry: dict,
    track: str,
    *,
    reviews_dir: Path | None = None,
) -> AdmissionResult:
    """Advisory promotion check only.

    There is NO automatic core-promotion write path in this repository yet
    (health.yml prints a stub). This helper must not be read as an implemented
    promotion framework. Legacy-unreviewed entries cannot gain new core status
    without a bound review.
    """
    track = (track or "web").lower()
    if track in UNGATED_TRACKS:
        return evaluate_admission(track)
    if is_legacy_unreviewed_entry(entry):
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


def _host_is_non_public(host: str) -> bool:
    """True if host is localhost, metadata, or a non-public IP (incl. decimal/hex)."""
    h = (host or "").lower().strip().rstrip(".")
    if not h:
        return True
    if h in {"localhost", "metadata.google.internal"}:
        return True
    if h.endswith(".localhost") or h.endswith(".local") or h.endswith(".internal"):
        return True
    # Decimal / hex IPv4 forms (e.g. 2130706433, 0x7f000001)
    candidates: list[str] = [h]
    if h.startswith("0x"):
        try:
            candidates.append(str(ipaddress.IPv4Address(int(h, 16))))
        except ValueError:
            pass
    elif h.isdigit():
        try:
            candidates.append(str(ipaddress.IPv4Address(int(h, 10))))
        except ValueError:
            pass
    for cand in candidates:
        try:
            ip = ipaddress.ip_address(cand)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return True
        except ValueError:
            continue
    return False


def is_allowed_fetch_url(url: str, *, allow_hosts: set[str] | None = None) -> bool:
    """Shared URL policy for triage network fetches (https public hosts only).

    Resolves DNS when possible and rejects non-public resolved addresses.
    This hardens the actual fetch path; it is not a complete SSRF product.
    """
    try:
        parsed = urlparse(url)
    except Exception:  # noqa: BLE001
        return False
    # Require https for outbound fetches (SSRF surface reduction).
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").lower()
    if allow_hosts is not None and host not in allow_hosts:
        return False
    if _host_is_non_public(host):
        return False
    # If hostname is an IP literal already handled; if DNS name, check resolution.
    try:
        ipaddress.ip_address(host)
        return True  # public IP literal already passed _host_is_non_public
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        # Unresolvable: allow parse-level public hostname; fetch will fail later.
        return True
    for info in infos:
        addr = info[4][0]
        if _host_is_non_public(addr):
            return False
    return True


# Back-compat alias used by older tests/docs — same policy as fetch hardening.
def safe_fetch_url_allowed(url: str, allow_hosts: set[str] | None = None) -> bool:
    return is_allowed_fetch_url(url, allow_hosts=allow_hosts)


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


def verify_evidence_package(
    evidence_dir: Path,
    *,
    expected_integrity: str,
    expected_file_hashes: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """Recompute hashes from on-disk evidence files; do not trust hashes.json alone."""
    if not evidence_dir.is_dir():
        return False, "evidence_dir_missing"
    hashes_path = evidence_dir / "hashes.json"
    if expected_file_hashes is None:
        if not hashes_path.exists():
            return False, "hashes_json_missing"
        expected_file_hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
    if not expected_file_hashes:
        return False, "empty_file_hash_map"
    computed: dict[str, str] = {}
    for rel, expect in sorted(expected_file_hashes.items()):
        path = safe_join_under(evidence_dir, rel)
        if path is None or not path.is_file():
            return False, f"missing_evidence_file:{rel}"
        digest = sha256_bytes(path.read_bytes())
        if digest != expect:
            return False, f"hash_mismatch:{rel}"
        computed[rel] = digest
    integ = package_integrity_from_hashes(computed)
    if integ != expected_integrity:
        return False, "package_integrity_mismatch"
    return True, "ok"


def entry_locator(entry: dict) -> str:
    return entry.get("url") or (entry.get("source") or {}).get("install_locator") or ""


def entry_integrity(entry: dict, track: str) -> str | None:
    ci = entry.get("content_integrity") or {}
    if track == "skill":
        return ci.get("package_integrity")
    return ci.get("content_sha256")
