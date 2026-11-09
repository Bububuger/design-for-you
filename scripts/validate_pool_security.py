#!/usr/bin/env python3
"""CI / local validator: pool rows must match security admission policy.

Legacy exemption comes ONLY from the immutable committed inventory
`security-reviews/legacy-grandfather.yaml` (pre-policy anchor). It is NOT
inferred from:
  - a row's claimed `security_admission: legacy-unreviewed` marker
  - "id exists on origin/main" / arbitrary git parent (push-to-main self-baseline)

Rules (web + skill):
  - Status must normalize to a recognized value (case/underscore insensitive).
  - Unknown / empty status → reject.
  - `candidate` / `core` require a bound approve review for the *current*
    security surface, OR an *exact* grandfather match (id+track+status+locators
    +integrity unchanged). Status transitions (pending-review→candidate,
    candidate→core, etc.) and locator/source/alias/integrity mutations void
    grandfathering and require review.
  - `pending-review` / `blocked` do not require approve, but cannot later enter
    candidate/core via grandfather merely because the id appeared in a prior
    commit while nongated.
  - Approve reviews must have nonempty track-specific binds_to pins.
  - Skill evidence packages re-hash on disk (not hashes.json alone).

Exit 0 on success; 1 on violations. Does not fetch or execute third-party skills.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import security_admission as secu  # noqa: E402

GRANDFATHER_PATH = ROOT / "security-reviews" / "legacy-grandfather.yaml"

RECOGNIZED_STATUSES = frozenset(
    {"candidate", "core", "pending-review", "blocked"}
)
GATED_STATUSES = frozenset({"candidate", "core"})
SOURCE_LOCATOR_KEYS = (
    "install_locator",
    "catalog_url",
    "skill_md_url",
    "index_url",
)


def load_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return data if isinstance(data, list) else []


def normalize_status(raw: Any) -> str | None:
    """Map Candidate/pending_review → canonical; unknown → None."""
    if raw is None:
        return None
    s = str(raw).strip().lower().replace("_", "-")
    if s in RECOGNIZED_STATUSES:
        return s
    return None


def git_rev_parse(ref: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", ref],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def is_self_baseline(base_ref: str | None) -> bool:
    """True when base_ref resolves to the same commit as HEAD (push-main laundering)."""
    if not base_ref:
        return False
    head = git_rev_parse("HEAD")
    base = git_rev_parse(base_ref)
    return bool(head and base and head == base)


def collect_locators(entry: dict) -> list[str]:
    """Canonical security-relevant locators (url, aliases, nested skill sources)."""
    found: list[str] = []
    if entry.get("url"):
        found.append(str(entry["url"]))
    for alias in entry.get("aliases") or []:
        if alias:
            found.append(str(alias))
    src = entry.get("source") or {}
    if isinstance(src, dict):
        for key in SOURCE_LOCATOR_KEYS:
            if src.get(key):
                found.append(str(src[key]))
    # Normalize + dedupe while preserving stability.
    normed: list[str] = []
    seen: set[str] = set()
    for raw in found:
        n = secu.normalize_locator(raw).rstrip("/")
        if n and n not in seen:
            seen.add(n)
            normed.append(n)
    return sorted(normed)


def security_surface(entry: dict, track: str) -> dict[str, Any]:
    """Fingerprint of fields that bind admission / grandfather identity."""
    ci = entry.get("content_integrity") or {}
    return {
        "id": entry.get("id"),
        "track": track,
        "status": normalize_status(entry.get("status")),
        "locators": collect_locators(entry),
        "package_integrity": ci.get("package_integrity"),
        "content_sha256": ci.get("content_sha256"),
    }


def load_grandfather(path: Path = GRANDFATHER_PATH) -> dict[str, dict[str, dict]]:
    """Return {track: {id: grandfather_entry_surface_dict}}."""
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tracks = data.get("tracks") or {}
    out: dict[str, dict[str, dict]] = {"web": {}, "skill": {}}
    for track in ("web", "skill"):
        for row in tracks.get(track) or []:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            # Build a synthetic entry so collect_locators works.
            synthetic = {
                "id": row["id"],
                "status": row.get("status"),
                "url": row.get("url"),
                "aliases": list(row.get("aliases") or []),
                "source": row.get("source") or {},
                "content_integrity": row.get("content_integrity") or {},
            }
            out[track][row["id"]] = security_surface(synthetic, track)
    return out


def surfaces_match_for_legacy(current: dict, grandfathered: dict) -> bool:
    """Exact match required: status + locators + integrity pins."""
    if current.get("id") != grandfathered.get("id"):
        return False
    if current.get("track") != grandfathered.get("track"):
        return False
    if current.get("status") != grandfathered.get("status"):
        return False
    if current.get("locators") != grandfathered.get("locators"):
        return False
    if current.get("package_integrity") != grandfathered.get("package_integrity"):
        return False
    if current.get("content_sha256") != grandfathered.get("content_sha256"):
        return False
    return True


def validate_reviews(reviews: list[dict]) -> list[str]:
    errs: list[str] = []
    for rev in reviews:
        conclusion = (rev.get("conclusion") or "").lower()
        if conclusion != "approve":
            continue
        track = (rev.get("track") or "").lower()
        binds = rev.get("binds_to") or {}
        if not isinstance(binds, dict) or not binds:
            errs.append(f"review {rev.get('id')}: approve requires nonempty binds_to")
            continue
        pin = secu.review_pin(rev, track)
        if not pin:
            errs.append(
                f"review {rev.get('id')}: approve missing valid "
                f"{secu.required_pin_field(track)}"
            )
        if not rev.get("resource_id"):
            errs.append(f"review {rev.get('id')}: missing resource_id")
        if not secu.review_locator(rev):
            errs.append(f"review {rev.get('id')}: missing resource_locator")
    return errs


def review_allowed_locators(rev: dict) -> set[str]:
    """Primary resource_locator plus optional related_locators declared on the review."""
    allowed: set[str] = set()
    primary = secu.review_locator(rev)
    if primary:
        allowed.add(secu.normalize_locator(primary).rstrip("/"))
    for extra in rev.get("related_locators") or []:
        if extra:
            allowed.add(secu.normalize_locator(str(extra)).rstrip("/"))
    binds = rev.get("binds_to") or {}
    for extra in binds.get("related_locators") or []:
        if extra:
            allowed.add(secu.normalize_locator(str(extra)).rstrip("/"))
    return allowed


def require_bound_review(
    entry: dict,
    track: str,
    *,
    reviews_dir: Path,
) -> list[str]:
    errs: list[str] = []
    eid = entry.get("id") or "<missing-id>"
    locator = secu.entry_locator(entry)
    integ = secu.entry_integrity(entry, track)
    adm = secu.evaluate_admission(
        track,
        locator=locator,
        package_integrity=integ if track == "skill" else None,
        content_sha256=integ if track == "web" else None,
        resource_id=entry.get("id"),
        reviews_dir=reviews_dir,
    )
    if not adm.ok:
        errs.append(
            f"{track}/{eid}: gated status requires bound review "
            f"({adm.status}:{adm.reason})"
        )
        return errs
    if entry.get("security_review_id") and entry.get("security_review_id") != adm.review_id:
        errs.append(
            f"{track}/{eid}: security_review_id mismatch "
            f"(entry={entry.get('security_review_id')} review={adm.review_id})"
        )
    # Binding scope: every pool locator/alias/source URL must be declared on the
    # matching review (resource_locator ∪ related_locators).
    rev = secu.find_matching_review(
        track, locator=locator, resource_id=entry.get("id"), reviews=secu.load_reviews(reviews_dir)
    )
    if rev is not None:
        allowed = review_allowed_locators(rev)
        for loc in collect_locators(entry):
            if loc not in allowed:
                errs.append(
                    f"{track}/{eid}: locator not in review binding scope: {loc}"
                )
    return errs


def validate_entry(
    entry: dict,
    track: str,
    *,
    grandfather: dict[str, dict[str, dict]],
    reviews_dir: Path,
) -> list[str]:
    errs: list[str] = []
    eid = entry.get("id") or "<missing-id>"
    raw_status = entry.get("status")
    status = normalize_status(raw_status)

    if status is None:
        errs.append(
            f"{track}/{eid}: unrecognized or missing status "
            f"{raw_status!r} (expected one of {sorted(RECOGNIZED_STATUSES)})"
        )
        return errs

    marker = (entry.get("security_admission") or "").lower().replace("_", "-")
    surface = security_surface(entry, track)
    gf = (grandfather.get(track) or {}).get(eid)
    exact_legacy = bool(gf and surfaces_match_for_legacy(surface, gf))

    # Claimed legacy marker is never trust by itself.
    if marker == "legacy-unreviewed" and not exact_legacy:
        errs.append(
            f"{track}/{eid}: security_admission=legacy-unreviewed rejected "
            "(not an exact pre-policy grandfather match)"
        )
        # continue — gated rows still need review checks below

    if status not in GATED_STATUSES:
        # pending-review / blocked: schema already checked; no approve required.
        return errs

    # Gated: exact grandfather match (unchanged pre-policy record+status) OR review.
    if exact_legacy:
        return errs

    # Status transition or locator/integrity mutation (or brand-new id).
    if gf and not exact_legacy:
        # Explain common bypass classes in the error text for operators.
        reasons: list[str] = []
        if surface.get("status") != gf.get("status"):
            reasons.append(
                f"status_transition:{gf.get('status')}->{surface.get('status')}"
            )
        if surface.get("locators") != gf.get("locators"):
            reasons.append("locator_or_source_mutation")
        if surface.get("package_integrity") != gf.get("package_integrity") or surface.get(
            "content_sha256"
        ) != gf.get("content_sha256"):
            reasons.append("integrity_mutation")
        detail = ",".join(reasons) or "surface_mismatch"
        # Still must pass bound review; annotate why grandfather did not apply.
        review_errs = require_bound_review(entry, track, reviews_dir=reviews_dir)
        if review_errs:
            errs.append(
                f"{track}/{eid}: grandfather voided ({detail}); "
                + review_errs[0].split(": ", 1)[-1]
            )
            errs.extend(review_errs[1:])
            return errs
        return errs

    # Not in grandfather inventory at all.
    errs.extend(require_bound_review(entry, track, reviews_dir=reviews_dir))
    return errs


def validate_skill_evidence(reviews: list[dict], root: Path) -> list[str]:
    errs: list[str] = []
    for rev in reviews:
        if (rev.get("track") or "").lower() != "skill":
            continue
        if (rev.get("conclusion") or "").lower() != "approve":
            continue
        scope = rev.get("scope") or {}
        evidence_rel = scope.get("evidence_dir") or ""
        if not evidence_rel:
            continue
        evidence_dir = root / evidence_rel
        pin = secu.review_pin(rev, "skill")
        if not pin:
            continue
        hashes_path = evidence_dir / "hashes.json"
        expected = None
        if hashes_path.exists():
            expected = json.loads(hashes_path.read_text(encoding="utf-8"))
        ok, reason = secu.verify_evidence_package(
            evidence_dir,
            expected_integrity=pin,
            expected_file_hashes=expected,
        )
        if not ok:
            errs.append(f"review {rev.get('id')}: evidence integrity failed ({reason})")
        if expected:
            missing = [rel for rel in expected if not (evidence_dir / rel).is_file()]
            if missing:
                errs.append(
                    f"review {rev.get('id')}: evidence missing {len(missing)} files "
                    f"(e.g. {missing[0]})"
                )
    return errs


def run(
    *,
    grandfather_path: Path = GRANDFATHER_PATH,
    base_ref: str | None = None,
) -> int:
    """Validate pools. `base_ref` is NEVER used for legacy trust.

    If provided, a self-baseline (base_ref == HEAD) is reported and ignored.
    Missing grandfather inventory fails closed for the run.
    """
    errors: list[str] = []

    if base_ref:
        if is_self_baseline(base_ref):
            print(
                f"validate_pool_security: ignoring self-baseline {base_ref} "
                "(equals HEAD; would launder legacy). Using grandfather inventory only."
            )
        else:
            print(
                f"validate_pool_security: note base_ref={base_ref} is not used for "
                "legacy trust; grandfather inventory is authoritative."
            )

    if not grandfather_path.exists():
        print("validate_pool_security: FAIL")
        print(f" - missing grandfather inventory: {grandfather_path}")
        return 1

    grandfather = load_grandfather(grandfather_path)
    if not grandfather.get("web"):
        errors.append("grandfather inventory has empty web track")

    reviews_dir = ROOT / "security-reviews"
    reviews = secu.load_reviews(reviews_dir)
    errors.extend(validate_reviews(reviews))
    errors.extend(validate_skill_evidence(reviews, ROOT))

    for track, path in (("web", ROOT / "sites.yaml"), ("skill", ROOT / "skills.yaml")):
        for entry in load_list(path):
            errors.extend(
                validate_entry(
                    entry,
                    track,
                    grandfather=grandfather,
                    reviews_dir=reviews_dir,
                )
            )

    if errors:
        print("validate_pool_security: FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("validate_pool_security: OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Validate pool/security review consistency "
        "(legacy via committed grandfather inventory only)"
    )
    p.add_argument(
        "--base-ref",
        default="",
        help=(
            "Optional git ref for diagnostics only — NEVER used to grant legacy "
            "trust. Self-baseline (ref==HEAD) is ignored. Prefer empty."
        ),
    )
    p.add_argument(
        "--grandfather",
        default=str(GRANDFATHER_PATH),
        help="Path to immutable legacy-grandfather.yaml",
    )
    args = p.parse_args(argv)
    base = args.base_ref.strip() or None
    return run(grandfather_path=Path(args.grandfather), base_ref=base)


if __name__ == "__main__":
    raise SystemExit(main())
