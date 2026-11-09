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

- **Authoritative grandfather inventory**: `security-reviews/legacy-grandfather.yaml`, anchored at pre-policy commit `b40a1af`. Exact match on **id + track + status + locators (+ integrity)** is required for exemption.
- A row's claimed `security_admission: legacy-unreviewed` marker is **never** trusted alone.
- `origin/main` / git parent is **not** used for legacy trust (push-to-main would self-baseline and launder).
- Status is normalized case-insensitively; unknown statuses are rejected. Transitions into `candidate`/`core` (including `pending-review`→`candidate` and `candidate`→`core`) and any locator/source/alias/integrity mutation **void** grandfathering and require a bound approve review.
- **Core promotion write path is not implemented** (health.yml only prints a stub). `can_promote` is advisory only.
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

Approval matches **track + resource_id + locator + content pin** (AND, never identity-OR-locator). Pool locators include `url`, `aliases`, and nested skill `source.*` fields; every locator on a gated row must be in the review's `resource_locator` ∪ `related_locators`. `binds_to` for `approve` must be nonempty with a valid track-specific SHA-256:

- skill → `package_integrity_sha256`
- web → `content_sha256`

Caller-supplied integrity must equal that pin. Issue-supplied hashes are untrusted unless they match the committed review pin for that exact identity/locator (web intake prefers hash of fetched HTML).

Approval is for the **pinned snapshot only**. Live host drift is **not** automatically detected; changing content requires re-review. No review, blocked, insufficient, invalid, or stale → cannot auto-enter `candidate`/`core`.

### Untrusted Issue bodies

Inbox Issue text **cannot** self-assert an approved review (`security_review: approved`, etc.). Such claims are ignored; only committed review files count.

### Dedup / graveyard tracks

- **skill** pool/graveyard is isolated from web/video (a rejected video URL must not block an unrelated skill).
- web↔video still share inspiration-URL uniqueness.
- Video being ungated does **not** imply web/skill security permission.

### Heuristics

Keyword detectors may **flag** spans for review. They never certify “safe” and must not mechanically condemn benign quotations (e.g. “never send credentials”).

## Skill review scope

Skill reviews must cover the **full package** declared by the catalog/index (SKILL.md, manifests, licenses, references, scripts), not SKILL.md alone. Static read + hash is authorized; **do not execute** third-party skill scripts or run `npx skills add` / paid MCP activation as part of admission.

## Website review scope

Web reviews must state exact pages/outlinks/dynamic surfaces covered and list unknowns (SPA hydration, gated content, etc.).

## Write-path enforcement

Gating is enforced in `scripts/security_admission.py` and called from triage / `add_candidate` / promotion helpers — not README-only.
