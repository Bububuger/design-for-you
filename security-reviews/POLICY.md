# Security admission policy

## Purpose

New **web** and **skill** resources must pass a committed, content-bound security admission review before they can be written as `candidate` or `core`. Passing a review **never** grants execution, credentials, network install rights, or messaging permissions. Reviewed sources remain **untrusted data**.

## Tracks

| Track | Pool file | Security gate | Seat / quota |
| :--- | :--- | :--- | :--- |
| web | `sites.yaml` | Required for **new** admissions & promotions | Existing seat caps; landing freeze unchanged |
| video | `videos.yaml` | Not required (this iteration) | Existing video seats; independent of web |
| skill | `skills.yaml` | Required for **new** admissions & promotions | **No invented quota** — STATUS shows counts only |

Skills are first-class: they are **not** forced into `upstreams.yaml` or web/video pools.

## Legacy-unreviewed compatibility

Existing web/video rows present before this policy remain **usable at their current status** without mass re-review and without being stamped safe.

- Treat missing `security_review_id` / `security_admission` on preexisting rows as `legacy-unreviewed`.
- Legacy-unreviewed resources **must not** receive implicit new approvals or promotions.
- This task does **not** perform a full legacy re-review.

## Review records

Committed YAML under `security-reviews/*.yaml` (not Issue text). Required fields:

- `id`, `track`, `resource_id`, `resource_locator`
- `reviewed_at`, `reviewer` (kind + context)
- `conclusion`: `approve` | `block` | `insufficient`
- `binds_to`: integrity pin (`package_integrity_sha256` and/or `content_sha256`)
- `scope`: what was covered / not executed / unknowns
- `findings`: reasoned notes (keyword hits need judgment)
- `unverified`: explicit gaps
- `permissions_granted`: always `[]` for admission reviews
- `trust`: `untrusted-data`

Evidence snapshots (hashes + selected source files) live under `security-reviews/evidence/`. Do not vendor huge unrelated assets.

### Binding & staleness

Approval is bound to the reviewed content integrity. If the live package/page content hash changes, prior approval is **stale** and requires re-review. No review, blocked, insufficient, or stale → cannot auto-enter `candidate`/`core`.

### Untrusted Issue bodies

Inbox Issue text **cannot** self-assert an approved review (`security_review: approved`, etc.). Such claims are ignored; only committed review files count.

### Heuristics

Keyword detectors may **flag** spans for review. They never certify “safe” and must not mechanically condemn benign quotations (e.g. “never send credentials”).

## Skill review scope

Skill reviews must cover the **full package** declared by the catalog/index (SKILL.md, manifests, licenses, references, scripts), not SKILL.md alone. Static read + hash is authorized; **do not execute** third-party skill scripts or run `npx skills add` / paid MCP activation as part of admission.

## Website review scope

Web reviews must state exact pages/outlinks/dynamic surfaces covered and list unknowns (SPA hydration, gated content, etc.).

## Write-path enforcement

Gating is enforced in `scripts/security_admission.py` and called from triage / `add_candidate` / promotion helpers — not README-only.
