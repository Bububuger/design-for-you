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

- **Authoritative grandfather**: derived at validation time from immutable git commit `b40a1af66b26dd8b0a3472c6d49b1e9e665b9fc5` (must be an ancestor of trusted `origin/main`/`main`). Exact match on **id + track + status + locators (+ integrity)** is required for exemption.
- `security-reviews/legacy-grandfather.yaml` is **display/cache only**; if present it must match the git derivation or validation fails (blocks coordinated inventory+pool edits).
- A row's claimed `security_admission: legacy-unreviewed` marker is **never** trusted alone. No CLI `--grandfather` path.
- Missing anchor / non-ancestor / shallow history without the commit → **fail closed**.
- Status is normalized case-insensitively; unknown statuses are rejected. Transitions into `candidate`/`core` and locator/source/alias/integrity mutations **void** grandfathering and require a bound approve review.
- **Honest limit**: human-reviewed approval YAML is still a social/process control; a PR that rewrites the validator itself is out of scope for this pin. The git anchor closes self-label / inventory-coordination loopholes.
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

### Web evidence honesty

Web `approve` reviews must commit the **audited response body** (and fetch metadata) under `scope.evidence_dir` so reviewers can inspect hidden text without trusting `hashes.json` alone. CI re-hashes on-disk files; `binds_to.content_sha256` must equal the primary body digest (default `homepage.html`), using the same convention as triage (`Response.text` → UTF-8 SHA-256) and the triage User-Agent.

- Homepage-only scope is **not** library / case-study / paywall / recording coverage. State unknowns explicitly.
- Empty SPA/JS shells (no substantive static body) are **not** approvable; use `conclusion: insufficient` until safe public official substantive evidence exists. Third-party directory writeups are auxiliary and never substitute evidence.
- Dynamic hosts without a **stable current** pin under the triage fetch convention remain **live-admission ineligible**: archive the snapshot with `conclusion: insufficient` (`scope.live_admission: ineligible`, `binds_to.snapshot_archive_only: true`). Do not strip scripts, broaden text hashes, relabel an old snapshot as live, or rotate a hash solely to turn the gate green.
- An `approve` that still marks `snapshot_archive_only` / `live_admission: ineligible` / `live_pin_stable: false` is **invalid** (fail closed).

### Binding & staleness

Approval matches **track + resource_id + locator + content pin** (AND, never identity-OR-locator). Resource ids for URL-only triage follow `triage.slug_id(url)` (host label); do not invent hyphenated aliases that fail AND matching. Pool locators include `url`, `aliases`, and nested skill `source.*` fields; every locator on a gated row must be in the review's `resource_locator` ∪ `related_locators`. `binds_to` for `approve` must be nonempty with a valid track-specific SHA-256:

- skill → `package_integrity_sha256`
- web → `content_sha256`

Caller-supplied integrity must equal that pin. Issue-supplied hashes are untrusted unless they match the committed review pin for that exact identity/locator (web intake prefers hash of fetched HTML).

Approval is for the **pinned snapshot only**. Changing content requires re-review. Web intake re-fetches HTML and compares to the pin; host drift → pending until a new bound review. No review, blocked, insufficient, invalid, or stale → cannot auto-enter `candidate`/`core`.

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
