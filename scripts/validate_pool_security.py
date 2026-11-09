#!/usr/bin/env python3
"""CI / local validator: pool rows must match security admission policy.

- New web/skill candidate|core rows cannot self-label legacy-unreviewed.
- Reviewed rows must bind track + id + locator + content pin to a committed review.
- Baseline (origin/main or BASE_REF) IDs without review fields are legacy-unreviewed.
- Approve reviews must have nonempty track-specific binds_to pins.
- Skill evidence packages must re-hash on disk (not trust hashes.json alone).

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

GATED_STATUSES = frozenset({"candidate", "core"})


def load_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return data if isinstance(data, list) else []


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


def baseline_pool(track: str, base_ref: str | None) -> dict[str, dict]:
    """Map id → entry from base ref when available."""
    if not base_ref:
        return {}
    rel = {"web": "sites.yaml", "skill": "skills.yaml"}[track]
    raw = git_show(base_ref, rel)
    if raw is None:
        return {}
    data = yaml.safe_load(raw) or []
    if not isinstance(data, list):
        return {}
    return {e["id"]: e for e in data if isinstance(e, dict) and e.get("id")}


def baseline_was_legacy(entry: dict | None) -> bool:
    if entry is None:
        return False
    return secu.is_legacy_unreviewed_entry(entry)


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


def validate_entry(
    entry: dict,
    track: str,
    *,
    baseline: dict[str, dict],
    reviews_dir: Path,
) -> list[str]:
    errs: list[str] = []
    eid = entry.get("id") or "<missing-id>"
    status = entry.get("status")
    if status not in GATED_STATUSES:
        return errs

    marker = (entry.get("security_admission") or "").lower().replace("_", "-")
    in_baseline = eid in baseline
    was_legacy = baseline_was_legacy(baseline.get(eid)) if in_baseline else False

    # New rows cannot self-label legacy.
    if not in_baseline and marker == "legacy-unreviewed":
        errs.append(
            f"{track}/{eid}: new row cannot self-label security_admission=legacy-unreviewed"
        )
        return errs

    # Baseline legacy (or unlabeled on base): may remain usable without review,
    # but must not claim reviewed-approve-bound without a valid binding.
    if in_baseline and was_legacy and marker in ("", "legacy-unreviewed"):
        return errs

    if in_baseline and was_legacy and marker == "reviewed-approve-bound":
        # Promotion-like claim: require real bound review.
        pass

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
        # Explicit legacy on an old baseline row is OK only if still legacy-shaped.
        if in_baseline and was_legacy and marker in ("", "legacy-unreviewed"):
            return errs
        errs.append(
            f"{track}/{eid}: gated status={status} without bound review "
            f"({adm.status}:{adm.reason})"
        )
        return errs

    # Reviewed claim must match review id.
    if entry.get("security_review_id") and entry.get("security_review_id") != adm.review_id:
        errs.append(
            f"{track}/{eid}: security_review_id mismatch "
            f"(entry={entry.get('security_review_id')} review={adm.review_id})"
        )
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
        # Require on-disk file count to cover declared package files.
        if expected:
            missing = [
                rel
                for rel in expected
                if not (evidence_dir / rel).is_file()
            ]
            if missing:
                errs.append(
                    f"review {rev.get('id')}: evidence missing {len(missing)} files "
                    f"(e.g. {missing[0]})"
                )
    return errs


def run(base_ref: str | None = "origin/main") -> int:
    reviews_dir = ROOT / "security-reviews"
    reviews = secu.load_reviews(reviews_dir)
    errors: list[str] = []
    errors.extend(validate_reviews(reviews))
    errors.extend(validate_skill_evidence(reviews, ROOT))

    for track, path in (("web", ROOT / "sites.yaml"), ("skill", ROOT / "skills.yaml")):
        baseline = baseline_pool(track, base_ref)
        for entry in load_list(path):
            errors.extend(
                validate_entry(
                    entry,
                    track,
                    baseline=baseline,
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
    p = argparse.ArgumentParser(description="Validate pool/security review consistency")
    p.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git ref for legacy baseline (empty string to disable)",
    )
    args = p.parse_args(argv)
    base = args.base_ref.strip() or None
    return run(base_ref=base)


if __name__ == "__main__":
    raise SystemExit(main())
