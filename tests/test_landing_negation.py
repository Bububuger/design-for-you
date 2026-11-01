#!/usr/bin/env python3
"""Regression: negated 落地页/landing in submitter reason must not force kind=landing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from triage import (  # noqa: E402
    rule_covers_from_text,
    triage_url,
)

# Issue #14-style contrastive reason (STATUS bounty gap ③, not a landing gallery).
ISSUE_14_REASON = (
    "不是又一个落地页画廊，是 empty states / user-feedback UX patterns 文档页，"
    "对应 STATUS 悬赏缺口 ③。\n"
    "kind: component\n"
    "covers: empty-state, skeleton, loading, user-feedback\n"
)

SAMPLE_HTML = """
<html><body>
  <h1>Empty states</h1>
  <nav><a href="/patterns">Patterns</a></nav>
  <p>Browse empty state, skeleton and loading UX patterns and examples.</p>
  <a href="/a">a</a><a href="/b">b</a><a href="/c">c</a>
  <a href="/d">d</a><a href="/e">e</a><a href="/f">f</a>
  <a href="/g">g</a><a href="/h">h</a><a href="/i">i</a>
  <a href="/j">j</a><a href="/k">k</a><a href="/l">l</a>
</body></html>
"""


class TestLandingNegationCovers(unittest.TestCase):
    def test_issue14_reason_does_not_add_landing_page_cover(self) -> None:
        covers = rule_covers_from_text("", ISSUE_14_REASON)
        self.assertNotIn("landing-page", covers)
        self.assertIn("empty-state", covers)

    def test_positive_landing_gallery_still_matches(self) -> None:
        covers = rule_covers_from_text("", "优质落地页画廊与营销页灵感合集")
        self.assertIn("landing-page", covers)

    def test_contrastive_variants(self) -> None:
        for reason in (
            "而非普通落地页，是组件模式库",
            "别把这个站当落地页灵感站",
            "这不是 landing page gallery，是 pattern docs",
        ):
            covers = rule_covers_from_text("", reason)
            self.assertNotIn("landing-page", covers, reason)


class TestIssue14TriageRegression(unittest.TestCase):
    @patch("triage.llm_covers_and_hint", return_value=None)
    @patch("triage.fetch_html", return_value=(SAMPLE_HTML, 200, None))
    @patch(
        "triage.normalize_url",
        return_value="https://uxpatterns.dev/patterns/user-feedback/empty-states",
    )
    @patch("triage.find_duplicate", return_value=None)
    def test_triage_does_not_reject_landing_freeze(
        self, _dup, _norm, _fetch, _llm
    ) -> None:
        result = triage_url(
            "https://uxpatterns.dev/patterns/user-feedback/empty-states",
            reason=ISSUE_14_REASON,
            write=False,
        )
        self.assertNotEqual(result.get("decision"), "rejected_landing_freeze")
        kind = (result.get("entry") or result.get("draft") or {}).get("kind")
        self.assertNotEqual(kind, "landing")
        self.assertEqual(kind, "component")
        covers = (result.get("entry") or result.get("draft") or {}).get("covers") or []
        self.assertNotIn("landing-page", covers)


if __name__ == "__main__":
    unittest.main()
