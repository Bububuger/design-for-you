#!/usr/bin/env python3
"""Video track scaffold: dual-file seats, track:video intake, landing freeze web-only."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import triage  # noqa: E402
from triage import (  # noqa: E402
    VALID_KINDS,
    VIDEO_KINDS,
    VIDEO_SEAT_QUOTAS,
    generate_status_md,
    parse_explicit_labels,
    seat_counts,
    triage_url,
)
from pool import select_pool  # noqa: E402

SAMPLE_HTML = """
<html><body>
  <h1>Launch demos</h1>
  <nav><a href="/browse">Browse</a></nav>
  <input type="search" name="q" />
  <p>Browse product launch demo reels, UI motion and storyboard inspiration gallery examples.</p>
  <a href="/a">a</a><a href="/b">b</a><a href="/c">c</a>
  <a href="/d">d</a><a href="/e">e</a><a href="/f">f</a>
  <a href="/g">g</a><a href="/h">h</a><a href="/i">i</a>
  <a href="/j">j</a><a href="/k">k</a><a href="/l">l</a>
</body></html>
"""


class TestVideoKindsAndSeats(unittest.TestCase):
    def test_valid_kinds_web_unchanged(self) -> None:
        self.assertEqual(
            VALID_KINDS, frozenset({"product-flow", "component", "landing", "system"})
        )

    def test_video_kinds_only(self) -> None:
        self.assertEqual(
            VIDEO_KINDS,
            frozenset({"ui-motion", "launch-demo", "storyboard", "gen-style"}),
        )
        self.assertTrue(VALID_KINDS.isdisjoint(VIDEO_KINDS))

    def test_dual_file_seat_counts_independent(self) -> None:
        web_sites = [
            {"id": "a", "status": "core", "kind": "component"},
            {"id": "b", "status": "candidate", "kind": "landing"},
        ]
        video_sites = [
            {"id": "v1", "status": "core", "kind": "launch-demo"},
            {"id": "v2", "status": "core", "kind": "ui-motion"},
            {"id": "v3", "status": "candidate", "kind": "storyboard"},
        ]
        web = seat_counts(web_sites, track="web")
        video = seat_counts(video_sites, track="video")
        self.assertEqual(web["core_total"], 1)
        self.assertEqual(web["candidate_total"], 1)
        self.assertEqual(web["by_kind"]["component"], 1)
        self.assertEqual(video["core_total"], 2)
        self.assertEqual(video["candidate_total"], 1)
        self.assertEqual(video["by_kind"]["launch-demo"], 1)
        self.assertEqual(video["by_kind"]["ui-motion"], 1)
        self.assertEqual(video["candidate_cap"], 12)
        self.assertEqual(sum(VIDEO_SEAT_QUOTAS.values()), 18)

    def test_status_md_has_web_and_video_tables(self) -> None:
        md = generate_status_md(miss_terms=[])
        self.assertIn("## Web 席位余量（Core）", md)
        self.assertIn("## Video 席位余量（Core）", md)
        self.assertIn("## 视频轨悬赏（简）", md)
        self.assertIn("ui-motion", md)
        self.assertIn("launch-demo", md)
        self.assertIn("仅 Web 轨", md)


class TestExplicitTrackVideo(unittest.TestCase):
    def test_parse_track_and_video_kind(self) -> None:
        labels = parse_explicit_labels(
            "track: video\nkind: launch-demo\ncovers: demo-reel, motion\n"
        )
        self.assertEqual(labels.get("track"), "video")
        self.assertEqual(labels.get("kind"), "launch-demo")
        self.assertEqual(labels.get("covers"), ["demo-reel", "motion"])

    def test_web_kind_rejected_on_video_track(self) -> None:
        labels = parse_explicit_labels(
            "track: video\nkind: component\n", track="video"
        )
        self.assertEqual(labels.get("track"), "video")
        self.assertNotIn("kind", labels)

    def test_default_track_is_web(self) -> None:
        labels = parse_explicit_labels("kind: component\ncovers: table\n")
        self.assertNotIn("track", labels)
        self.assertEqual(labels.get("kind"), "component")

    @patch("triage.llm_covers_and_hint", return_value=None)
    @patch("triage.fetch_html", return_value=(SAMPLE_HTML, 200, None))
    @patch("triage.normalize_url", return_value="https://launchgallery.example/")
    @patch("triage.find_duplicate", return_value=None)
    def test_triage_explicit_track_video(self, _dup, _norm, _fetch, _llm) -> None:
        result = triage_url(
            "https://launchgallery.example/",
            reason=(
                "track: video\n"
                "kind: launch-demo\n"
                "covers: launch-demo, product-reel\n"
                "产品发布 demo 灵感库\n"
            ),
            write=False,
        )
        self.assertEqual(result.get("track"), "video")
        self.assertNotEqual(result.get("decision"), "rejected_landing_freeze")
        payload = result.get("entry") or result.get("draft") or {}
        self.assertEqual(payload.get("kind"), "launch-demo")


class TestLandingFreezeWebOnly(unittest.TestCase):
    @patch("triage.llm_covers_and_hint", return_value=None)
    @patch("triage.fetch_html", return_value=(SAMPLE_HTML, 200, None))
    @patch("triage.normalize_url", return_value="https://motion.example/")
    @patch("triage.find_duplicate", return_value=None)
    def test_landing_freeze_does_not_block_video(
        self, _dup, _norm, _fetch, _llm
    ) -> None:
        # Even if reason mentions landing, video track + video kind must not freeze.
        result = triage_url(
            "https://motion.example/",
            reason=(
                "track: video\n"
                "kind: ui-motion\n"
                "covers: ui-motion, micro-interaction\n"
                "不是落地页，是 UI motion reel 库\n"
            ),
            write=False,
        )
        self.assertEqual(result.get("track"), "video")
        self.assertNotEqual(result.get("decision"), "rejected_landing_freeze")
        payload = result.get("entry") or result.get("draft") or {}
        self.assertEqual(payload.get("kind"), "ui-motion")

    def test_add_candidate_per_track_full_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            sites = tmp_path / "sites.yaml"
            videos = tmp_path / "videos.yaml"
            sites.write_text("[]\n", encoding="utf-8")
            videos.write_text("[]\n", encoding="utf-8")
            old_sites, old_videos = triage.SITES_PATH, triage.VIDEOS_PATH
            triage.SITES_PATH = sites
            triage.VIDEOS_PATH = videos
            try:
                entry = {
                    "id": "x",
                    "name": "X",
                    "url": "https://x.example/",
                    "status": "candidate",
                    "kind": "ui-motion",
                    "covers": ["ui-motion"],
                    "search_hint": "x",
                    "auth": "none",
                    "added_at": "2026-11-02",
                }
                # Fill video candidate cap
                for i in range(triage.VIDEO_CANDIDATE_CAP):
                    triage.add_candidate({**entry, "id": f"v{i}"}, track="video")
                with self.assertRaisesRegex(RuntimeError, r"video candidate pool full"):
                    triage.add_candidate({**entry, "id": "overflow"}, track="video")
                # Web track still writable independently (seat-cap test; skip
                # security gate — gated path covered in test_security_admission).
                triage.add_candidate(
                    {
                        **entry,
                        "id": "web1",
                        "kind": "component",
                        "url": "https://web.example/",
                    },
                    track="web",
                    skip_security_gate=True,
                )
                self.assertEqual(len(triage.list_videos()), triage.VIDEO_CANDIDATE_CAP)
                self.assertEqual(len(triage.list_sites()), 1)
            finally:
                triage.SITES_PATH = old_sites
                triage.VIDEOS_PATH = old_videos


class TestPoolTrackSelect(unittest.TestCase):
    def test_select_video_track_isolated(self) -> None:
        out = select_pool("launch-demo", track="video")
        self.assertEqual(out["track"], "video")
        self.assertEqual(out["core"], [])  # no video core yet
        # Candidates may exist in videos.yaml; all rows must be video-shaped.
        for row in out["candidate"]:
            self.assertIn(
                row.get("kind"),
                {"ui-motion", "launch-demo", "storyboard", "gen-style"},
            )

    def test_select_defaults_web(self) -> None:
        out = select_pool("data-table")
        self.assertEqual(out["track"], "web")
        self.assertTrue(len(out["core"]) <= 4)


if __name__ == "__main__":
    unittest.main()
