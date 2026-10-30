#!/usr/bin/env python3
"""Minimal tests for github.com owner/repo URL matching."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from triage import github_repo_key, urls_match  # noqa: E402


class TestGithubRepoKey(unittest.TestCase):
    def test_normalizes_variants(self) -> None:
        expect = "bububuger/design-pool"
        variants = [
            "https://github.com/Bububuger/design-pool",
            "https://www.github.com/Bububuger/design-pool/",
            "https://github.com/Bububuger/design-pool.git",
            "https://GitHub.com/BUBUBUGER/Design-Pool",
        ]
        for url in variants:
            self.assertEqual(github_repo_key(url), expect, url)

    def test_non_github_is_none(self) -> None:
        self.assertIsNone(github_repo_key("https://dribbble.com/shots/123"))
        self.assertIsNone(github_repo_key("https://github.com/only-owner"))


class TestUrlsMatch(unittest.TestCase):
    def test_different_repos_do_not_collide(self) -> None:
        a = "https://github.com/assistant-ui/assistant-ui"
        b = "https://github.com/tremorlabs/tremor"
        self.assertFalse(urls_match(a, b))

    def test_same_repo_variants_match(self) -> None:
        a = "https://github.com/assistant-ui/assistant-ui"
        b = "https://www.github.com/Assistant-UI/assistant-ui.git/"
        self.assertTrue(urls_match(a, b))

    def test_non_github_still_domain_match(self) -> None:
        self.assertTrue(
            urls_match("https://mobbin.com/browse", "https://www.mobbin.com/foo")
        )
        self.assertFalse(
            urls_match("https://mobbin.com/browse", "https://dribbble.com/shots")
        )


if __name__ == "__main__":
    unittest.main()
