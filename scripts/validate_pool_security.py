#!/usr/bin/env python3
"""CI / local validator: pool rows must match security admission policy.

Legacy exemption is derived ONLY from the immutable pre-policy Git commit
PRE_POLICY_ANCHOR (must be an ancestor of trusted main). It is NOT granted by:
  - a row's claimed `security_admission: legacy-unreviewed` marker
  - HEAD-committed `legacy-grandfather.yaml` (display/cache only; mismatch fails)
  - arbitrary CLI grandfather path
  - "id exists on origin/main" / push-main self-baseline

Honest limit: committed *review approvals* still require human judgment of review
YAML; this tool cannot stop a malicious PR that rewrites the validator itself.
The git anchor closes accidental/self-label/inventory-coordination loopholes.

Rules (web + skill):
  - Status must normalize to a recognized value (case/underscore insensitive).
  - Unknown / empty status → reject.
  - `candidate` / `core` require a bound approve review for the *current*
    security surface, OR an *exact* derived-grandfather match (id+track+status
    +locators+integrity unchanged). Status transitions and locator/source/alias
    mutations void grandfathering and require review.
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

# Immutable pre-policy tip (origin/main before skills/security-admission work).
PRE_POLICY_ANCHOR = "b40a1af66b26dd8b0a3472c6d49b1e9e665b9fc5"
TRUSTED_MAIN_REFS = ("origin/main", "main")
GRANDFATHER_CACHE_PATH = ROOT / "security-reviews" / "legacy-grandfather.yaml"

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


class GrandfatherError(RuntimeError):
    """Fail-closed grandfather derivation / cache mismatch."""


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


def git_is_ancestor(ancestor: str, descendant: str) -> bool:
    try:
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def git_show(ref: str, relpath: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "show", f"{ref}:{relpath}"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def is_self_baseline(base_ref: str | None) -> bool:
    """True when base_ref resolves to the same commit as HEAD (push-main laundering)."""
    if not base_ref:
        return False
    head = git_rev_parse("HEAD")
    base = git_rev_parse(base_ref)
    return bool(head and base and head == base)


def resolve_trusted_main(refs: tuple[str, ...] = TRUSTED_MAIN_REFS) -> str:
    for ref in refs:
        sha = git_rev_parse(ref)
        if sha:
            return sha
    raise GrandfatherError(
        "trusted main ref unavailable "
        f"(tried {', '.join(refs)}); fetch-depth must include main history"
    )


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


def _rows_to_surfaces(rows: list[dict], track: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        synthetic = {
            "id": row["id"],
            "status": row.get("status"),
            "url": row.get("url"),
            "aliases": list(row.get("aliases") or []),
            "source": row.get("source") or {},
            "content_integrity": row.get("content_integrity") or {},
        }
        out[row["id"]] = security_surface(synthetic, track)
    return out


def derive_grandfather_from_git(
    *,
    anchor: str = PRE_POLICY_ANCHOR,
    trusted_main: str | None = None,
) -> dict[str, dict[str, dict]]:
    """Build grandfather surfaces from the pinned pre-policy commit.

    Fails closed if the anchor is missing or not an ancestor of trusted main.
    Skills did not exist pre-policy → empty skill track.
    """
    anchor_sha = git_rev_parse(anchor)
    if not anchor_sha:
        raise GrandfatherError(
            f"pre-policy anchor {anchor} not found in local git history "
            "(shallow clone? need fetch-depth: 0)"
        )
    main_sha = trusted_main or resolve_trusted_main()
    if not git_is_ancestor(anchor_sha, main_sha):
        raise GrandfatherError(
            f"pre-policy anchor {anchor_sha} is not an ancestor of trusted main "
            f"{main_sha}; refusing legacy exemptions"
        )

    sites_raw = git_show(anchor_sha, "sites.yaml")
    if sites_raw is None:
        raise GrandfatherError(f"sites.yaml missing at anchor {anchor_sha}")
    sites = yaml.safe_load(sites_raw) or []
    if not isinstance(sites, list) or not sites:
        raise GrandfatherError(f"sites.yaml empty/invalid at anchor {anchor_sha}")

    # skills.yaml must not exist pre-policy; if present, refuse (unexpected).
    skills_raw = git_show(anchor_sha, "skills.yaml")
    if skills_raw is not None:
        raise GrandfatherError(
            f"skills.yaml unexpectedly present at pre-policy anchor {anchor_sha}"
        )

    web = _rows_to_surfaces(sites, "web")
    if not web:
        raise GrandfatherError("derived grandfather web track is empty")
    return {"web": web, "skill": {}}


def load_grandfather_cache(path: Path = GRANDFATHER_CACHE_PATH) -> dict[str, dict[str, dict]]:
    """Load display/cache YAML only — NEVER use alone for production trust."""
    if not path.exists():
        return {"web": {}, "skill": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tracks = data.get("tracks") or {}
    out: dict[str, dict[str, dict]] = {"web": {}, "skill": {}}
    for track in ("web", "skill"):
        out[track] = _rows_to_surfaces(list(tracks.get(track) or []), track)
    return out


def grandfather_maps_equal(
    a: dict[str, dict[str, dict]], b: dict[str, dict[str, dict]]
) -> bool:
    for track in ("web", "skill"):
        if set((a.get(track) or {})) != set((b.get(track) or {})):
            return False
        for eid, surf in (a.get(track) or {}).items():
            if not surfaces_match_for_legacy(surf, (b.get(track) or {})[eid]):
                return False
    return True


# Back-compat name used by unit tests that inject comparison maps only.
# Production trust path must call derive_grandfather_from_git().
def load_grandfather(path: Path = GRANDFATHER_CACHE_PATH) -> dict[str, dict[str, dict]]:
    """DEPRECATED for trust: alias of load_grandfather_cache (tests / display)."""
    return load_grandfather_cache(path)


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
    rev = secu.find_matching_review(
        track,
        locator=locator,
        resource_id=entry.get("id"),
        reviews=secu.load_reviews(reviews_dir),
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
    """Validate one pool row against a grandfather *map*.

    Callers that inject `grandfather=` are unit-testing comparison logic only.
    Production `run()` always passes a map from derive_grandfather_from_git().
    """
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

    if marker == "legacy-unreviewed" and not exact_legacy:
        errs.append(
            f"{track}/{eid}: security_admission=legacy-unreviewed rejected "
            "(not an exact pre-policy grandfather match)"
        )

    if status not in GATED_STATUSES:
        return errs

    if exact_legacy:
        return errs

    if gf and not exact_legacy:
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
        review_errs = require_bound_review(entry, track, reviews_dir=reviews_dir)
        if review_errs:
            errs.append(
                f"{track}/{eid}: grandfather voided ({detail}); "
                + review_errs[0].split(": ", 1)[-1]
            )
            errs.extend(review_errs[1:])
            return errs
        return errs

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


def run(*, base_ref: str | None = None) -> int:
    """Validate pools. Legacy trust = git-derived grandfather only."""
    errors: list[str] = []

    if base_ref:
        if is_self_baseline(base_ref):
            print(
                f"validate_pool_security: ignoring self-baseline {base_ref} "
                "(equals HEAD; would launder legacy)."
            )
        else:
            print(
                f"validate_pool_security: note base_ref={base_ref} is not used for "
                "legacy trust; git pre-policy anchor is authoritative."
            )

    try:
        grandfather = derive_grandfather_from_git()
    except GrandfatherError as e:
        print("validate_pool_security: FAIL")
        print(f" - {e}")
        return 1

    # Cache YAML is display-only; if present it MUST match derivation.
    if GRANDFATHER_CACHE_PATH.exists():
        cache = load_grandfather_cache(GRANDFATHER_CACHE_PATH)
        labeled = None
        try:
            labeled = (
                yaml.safe_load(GRANDFATHER_CACHE_PATH.read_text(encoding="utf-8")) or {}
            ).get("anchor_commit")
        except OSError:
            labeled = None
        if labeled and git_rev_parse(str(labeled)) != git_rev_parse(PRE_POLICY_ANCHOR):
            errors.append(
                f"legacy-grandfather.yaml anchor_commit {labeled!r} does not match "
                f"enforced PRE_POLICY_ANCHOR {PRE_POLICY_ANCHOR}"
            )
        if not grandfather_maps_equal(cache, grandfather):
            errors.append(
                "legacy-grandfather.yaml cache mismatches git-derived grandfather "
                f"at {PRE_POLICY_ANCHOR}; refusing (coordinated inventory edit)"
            )

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
    print(
        f"validate_pool_security: OK "
        f"(grandfather derived from {PRE_POLICY_ANCHOR}; "
        f"web={len(grandfather['web'])} skill={len(grandfather['skill'])})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Validate pool/security review consistency "
        "(legacy via git-derived pre-policy anchor only)"
    )
    p.add_argument(
        "--base-ref",
        default="",
        help=(
            "Optional git ref for diagnostics only — NEVER used to grant legacy "
            "trust. Self-baseline (ref==HEAD) is ignored. Prefer empty."
        ),
    )
    # Intentionally NO --grandfather path: that was a production trust bypass.
    args = p.parse_args(argv)
    base = args.base_ref.strip() or None
    return run(base_ref=base)


if __name__ == "__main__":
    raise SystemExit(main())
