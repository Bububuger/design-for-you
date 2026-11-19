#!/usr/bin/env python3
"""Regressions for inbox triage defects (#40 / #42 / #43 review findings).

Observable behaviors covered:
1. GitHub skill locators derive stable repo-slug ids (not host ``github``).
2. Explicit illegal ``kind:`` fails closed with needs_human (no silent fallback).
3. Inbox workflow triggers are single-shot (labeled+reopened; not opened+labeled).
4. PR mention helpers never emit literal ``PR #None``.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import security_admission as secu  # noqa: E402
from triage import (  # noqa: E402
    build_inbox_comment,
    format_pr_ref,
    format_security_review_cite,
    parse_explicit_labels,
    slug_id,
    strip_pr_none_mentions,
    triage_skill_locator,
    triage_url,
)


SAMPLE_HTML = """
<html><body>
  <h1>Gallery</h1>
  <nav><a href="/a">a</a><a href="/b">b</a><a href="/c">c</a>
  <a href="/d">d</a><a href="/e">e</a><a href="/f">f</a>
  <a href="/g">g</a><a href="/h">h</a><a href="/i">i</a>
  <a href="/j">j</a><a href="/k">k</a><a href="/l">l</a></nav>
  <p>Browse inspiration gallery screenshots and examples.</p>
</body></html>
"""

INBOX_WORKFLOW = ROOT / ".github" / "workflows" / "inbox.yml"


class TestGithubSlugIdStable(unittest.TestCase):
    """Defect 1: github.com host must not collapse every skill to id=github."""

    def test_github_repos_use_repo_slug_not_host(self) -> None:
        craft = "https://github.com/diego3g/craft"
        stitch = "https://github.com/google-labs-code/stitch-skills"
        self.assertEqual(slug_id(craft), "craft")
        self.assertEqual(slug_id(stitch), "stitch-skills")
        self.assertNotEqual(slug_id(craft), slug_id(stitch))
        self.assertNotEqual(slug_id(craft), "github")
        self.assertNotEqual(slug_id(stitch), "github")

    def test_github_slug_matches_cli_name_convention(self) -> None:
        url = "https://github.com/diego3g/craft"
        self.assertEqual(slug_id(url), slug_id(url, "craft"))
        self.assertEqual(slug_id(url, "craft"), "craft")

    def test_non_github_still_uses_host_label(self) -> None:
        self.assertEqual(
            slug_id("https://uizze.sh/.well-known/agent-skills/ui-taste/"),
            "uizze",
        )
        self.assertEqual(slug_id("https://inspora.design/"), "inspora")

    def test_explicit_name_still_wins(self) -> None:
        self.assertEqual(
            slug_id("https://github.com/diego3g/craft", "my-craft"),
            "my-craft",
        )

    def test_different_github_repos_do_not_share_id(self) -> None:
        a = slug_id("https://github.com/assistant-ui/assistant-ui")
        b = slug_id("https://github.com/tremorlabs/tremor")
        self.assertEqual(a, "assistant-ui")
        self.assertEqual(b, "tremor")
        self.assertNotEqual(a, b)

    def test_skill_inbox_without_name_matches_review_resource_id(self) -> None:
        """Inbox path (no --name) must AND-match a review keyed by repo slug."""
        locator = "https://github.com/diego3g/craft/"
        pin = "a" * 64
        review = {
            "id": "skill-craft-test",
            "track": "skill",
            "resource_id": "craft",
            "resource_locator": locator,
            "related_locators": [locator],
            "conclusion": "approve",
            "binds_to": {"package_integrity_sha256": pin},
            "reviewed_at": "2026-11-16",
        }
        with tempfile.TemporaryDirectory() as tmp:
            reviews_dir = Path(tmp)
            (reviews_dir / "skill-craft-test.yaml").write_text(
                yaml.safe_dump(review, sort_keys=False), encoding="utf-8"
            )
            old = secu.REVIEWS_DIR
            secu.REVIEWS_DIR = reviews_dir
            try:
                self.assertEqual(slug_id(locator), "craft")
                result = triage_skill_locator(
                    locator,
                    reason="track: skill\n",
                    name=None,
                    write=False,
                )
                draft = result.get("draft") or result.get("entry") or {}
                self.assertEqual(draft.get("id"), "craft")
                self.assertNotEqual(draft.get("id"), "github")
                self.assertEqual(
                    (draft.get("content_integrity") or {}).get("package_integrity"),
                    pin,
                )
                matched = secu.find_matching_review(
                    "skill", locator=locator, resource_id="craft"
                )
                self.assertIsNotNone(matched)
                self.assertEqual(matched.get("id"), "skill-craft-test")
                # Collapsed host id must still fail closed (AND match).
                self.assertIsNone(
                    secu.find_matching_review(
                        "skill", locator=locator, resource_id="github"
                    )
                )
                # With matching id+locator+pin, admission should accept.
                self.assertEqual(result.get("decision"), "accept_candidate")
                adm = result.get("security_admission") or {}
                self.assertTrue(adm.get("ok"))
            finally:
                secu.REVIEWS_DIR = old

    def test_two_github_skills_keep_distinct_ids_under_admission(self) -> None:
        craft = "https://github.com/diego3g/craft/"
        stitch = "https://github.com/google-labs-code/stitch-skills/"
        pin_c, pin_s = "b" * 64, "c" * 64
        reviews = [
            {
                "id": "skill-craft-test",
                "track": "skill",
                "resource_id": "craft",
                "resource_locator": craft,
                "conclusion": "approve",
                "binds_to": {"package_integrity_sha256": pin_c},
                "reviewed_at": "2026-11-16",
            },
            {
                "id": "skill-stitch-test",
                "track": "skill",
                "resource_id": "stitch-skills",
                "resource_locator": stitch,
                "conclusion": "approve",
                "binds_to": {"package_integrity_sha256": pin_s},
                "reviewed_at": "2026-11-16",
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            reviews_dir = Path(tmp)
            for rev in reviews:
                (reviews_dir / f"{rev['id']}.yaml").write_text(
                    yaml.safe_dump(rev, sort_keys=False), encoding="utf-8"
                )
            old = secu.REVIEWS_DIR
            secu.REVIEWS_DIR = reviews_dir
            try:
                r1 = triage_skill_locator(craft, reason="track: skill\n", write=False)
                r2 = triage_skill_locator(stitch, reason="track: skill\n", write=False)
                id1 = (r1.get("draft") or r1.get("entry") or {}).get("id")
                id2 = (r2.get("draft") or r2.get("entry") or {}).get("id")
                self.assertEqual(id1, "craft")
                self.assertEqual(id2, "stitch-skills")
                self.assertNotEqual(id1, id2)
                # Cross-wiring locator to the other review's id must not match.
                self.assertIsNone(
                    secu.find_matching_review(
                        "skill", locator=craft, resource_id="stitch-skills"
                    )
                )
                self.assertIsNone(
                    secu.find_matching_review(
                        "skill", locator=stitch, resource_id="craft"
                    )
                )
            finally:
                secu.REVIEWS_DIR = old


class TestInvalidKindFailClosed(unittest.TestCase):
    """Defect 2: illegal kind must not silently fall through to covers/rules."""

    def test_parse_records_invalid_kind(self) -> None:
        labels = parse_explicit_labels(
            "kind: gallery\ncovers: landing, branding\n"
        )
        self.assertNotIn("kind", labels)
        self.assertEqual(labels.get("invalid_kind"), "gallery")
        self.assertEqual(labels.get("covers"), ["landing", "branding"])

    @patch("triage.llm_covers_and_hint", return_value=None)
    @patch("triage.fetch_html", return_value=(SAMPLE_HTML, 200, None))
    @patch("triage.normalize_url", return_value="https://inspora.design/")
    @patch("triage.find_duplicate", return_value=None)
    @patch("triage.add_to_graveyard")
    def test_issue40_gallery_kind_does_not_become_landing(
        self, mock_gy, _dup, _norm, _fetch, _llm
    ) -> None:
        reason = (
            "kind: gallery\n"
            "covers: landing, branding, motion, logo\n\n"
            "视觉设计灵感聚合站。\n"
        )
        result = triage_url(
            "https://inspora.design/",
            reason=reason,
            write=True,
        )
        self.assertEqual(result.get("decision"), "needs_human")
        self.assertEqual(result.get("invalid_kind"), "gallery")
        self.assertEqual(result.get("note"), "invalid_kind:gallery")
        self.assertNotEqual(result.get("decision"), "rejected_landing_freeze")
        mock_gy.assert_not_called()
        # Fetch / LLM must not run after invalid kind (fail before side effects).
        _fetch.assert_not_called()
        _llm.assert_not_called()

    def test_inbox_comment_names_illegal_kind(self) -> None:
        comment = build_inbox_comment(
            {
                "decision": "needs_human",
                "track": "web",
                "invalid_kind": "gallery",
                "allowed_kinds": ["component", "landing", "product-flow", "system"],
                "note": "invalid_kind:gallery",
            }
        )
        self.assertIn("非法 kind", comment)
        self.assertIn("gallery", comment)
        self.assertIn("静默回退", comment)


class TestInboxWorkflowDedup(unittest.TestCase):
    """Defect 3: workflow must not double-fire on create-with-inbox-label."""

    def test_workflow_does_not_listen_to_opened(self) -> None:
        text = INBOX_WORKFLOW.read_text(encoding="utf-8")
        # types line must be labeled+reopened only (not the dual opened+labeled trigger).
        self.assertRegex(text, r"types:\s*\[labeled,\s*reopened\]")
        self.assertNotRegex(
            text,
            r"types:\s*\[[^\]]*\bopened\b[^\]]*\]",
        )

    def test_labeled_filtered_to_inbox_label_only(self) -> None:
        text = INBOX_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.event.label.name == 'inbox'", text)

    def test_idempotent_skip_step_present(self) -> None:
        text = INBOX_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Skip if already triaged", text)
        self.assertIn("steps.dedup.outputs.skip", text)
        # Ensure label auto-add (which re-fired labeled) is gone.
        self.assertNotIn("Ensure inbox label", text)


class TestPrNoneNeverEmitted(unittest.TestCase):
    """Defect 4: missing PR number must omit the phrase, not print PR #None."""

    def test_format_pr_ref_none_empty(self) -> None:
        self.assertEqual(format_pr_ref(None), "")
        self.assertEqual(format_pr_ref("None"), "")
        self.assertEqual(format_pr_ref("null"), "")
        self.assertEqual(format_pr_ref(0), "")
        self.assertEqual(format_pr_ref(-1), "")
        self.assertEqual(format_pr_ref(39), "PR #39")
        self.assertEqual(format_pr_ref("41"), "PR #41")

    def test_format_security_review_cite_omits_none(self) -> None:
        with_none = format_security_review_cite("web-inspora-2026-11-11", None)
        self.assertNotIn("PR #None", with_none)
        self.assertNotIn("#None", with_none)
        self.assertIn("web-inspora-2026-11-11", with_none)
        with_pr = format_security_review_cite("web-inspora-2026-11-11", 39)
        self.assertIn("PR #39", with_pr)
        self.assertIn("web-inspora-2026-11-11", with_pr)

    def test_strip_pr_none_from_feeder_body_echo(self) -> None:
        raw = (
            "配套 security review 见 PR #None（web-inspora-2026-11-11）。"
            "外链学习参考。"
        )
        cleaned = strip_pr_none_mentions(raw)
        self.assertNotIn("PR #None", cleaned)
        self.assertNotIn("#None", cleaned)
        self.assertIn("web-inspora-2026-11-11", cleaned)

    def test_inbox_comment_strips_pr_none_in_json_fallback(self) -> None:
        comment = build_inbox_comment(
            {
                "decision": "weird",
                "track": "web",
                "note": "配套 security review 见 PR #None（web-inspora-2026-11-11）。",
            }
        )
        self.assertNotIn("PR #None", comment)
        self.assertNotIn("#None", comment)


class TestParseNameLabel(unittest.TestCase):
    def test_name_from_issue_body(self) -> None:
        labels = parse_explicit_labels("track: skill\nname: craft\n")
        self.assertEqual(labels.get("name"), "craft")
        self.assertEqual(labels.get("track"), "skill")


if __name__ == "__main__":
    unittest.main()
