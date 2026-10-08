"""Offline tests for discovery correctness and failure atomicity."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from xml.sax.saxutils import escape

import dexterous_watch as watch


NOW = datetime(2026, 10, 8, 1, 35, tzinfo=timezone.utc)


def entry(paper_id="2610.00001v1", title="Dexterous manipulation with tactile feedback", published="2026-10-06T12:00:00Z", updated=None, abstract="We study dexterous manipulation using tactile observations from a multi-finger robot hand."):
    values = {"id": "http://arxiv.org/abs/" + paper_id, "title": title, "published": published, "updated": updated or published, "summary": abstract}
    tags = "".join(f"<{key}>{escape(value)}</{key}>" for key, value in values.items())
    return f"<entry>{tags}<author><name>Alice Example</name></author></entry>"


def feed(*entries, total=None, start=0):
    total = len(entries) if total is None else total
    return (f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
            f"<opensearch:totalResults>{total}</opensearch:totalResults><opensearch:startIndex>{start}</opensearch:startIndex>"
            + "".join(entries) + "</feed>").encode()


class WatchTests(unittest.TestCase):
    def test_normalizes_versions_urls_and_legacy_ids(self):
        for source, expected in (("arXiv:2610.00001v3", "2610.00001"), ("https://arxiv.org/pdf/2610.00001v2.pdf", "2610.00001"), ("http://arxiv.org/abs/cs/9901001v2", "cs/9901001")):
            self.assertEqual(watch.normalize_id(source), expected)
        self.assertIsNone(watch.normalize_id("https://example.com/abs/2610.00001"))
        self.assertIsNone(watch.normalize_id("project-2610.00001"))

    def test_parses_and_deduplicates_replacements_by_latest_update(self):
        raw = feed(entry("2610.00001v2", updated="2026-10-07T12:00:00Z"), entry("2610.00001v1"))
        papers = watch.fetch_recent(NOW, 7, fetcher=lambda _: raw)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["updated"], "2026-10-07T12:00:00Z")
        self.assertEqual(papers[0]["matched_topics"], ["dexterous", "tactile"])
        self.assertLessEqual(len(papers[0]["evidence"][0]["text"].replace("…", "").split()), 22)
        self.assertNotIn("tldr", papers[0])

    def test_rolling_window_includes_old_paper_replaced_this_week(self):
        papers = watch.fetch_recent(NOW, 7, fetcher=lambda _: feed(entry("2301.00001v3", published="2023-01-01T12:00:00Z", updated="2026-10-07T12:00:00Z")))
        self.assertEqual([paper["id"] for paper in papers], ["2301.00001"])

    def test_pagination_stops_after_crossing_cutoff(self):
        requests, delays = [], []
        pages = [feed(entry(), total=3), feed(entry("2609.00001", published="2026-09-20T12:00:00Z"), total=3, start=1)]
        def fetch(url):
            requests.append(parse_qs(urlparse(url).query))
            return pages[len(requests) - 1]
        papers = watch.fetch_recent(NOW, 7, fetcher=fetch, sleeper=delays.append, page_size=1)
        self.assertEqual(len(papers), 1)
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[1]["start"], ["1"])
        self.assertEqual(requests[0]["sortBy"], ["lastUpdatedDate"])
        self.assertEqual(delays, [3])

    def test_unrelated_tactile_paper_is_not_automatically_a_hand_candidate(self):
        self.assertEqual(watch.classify("Tactile sensing", "A two-finger gripper estimates object shape."), [])
        self.assertEqual(watch.classify("Multi-finger manipulation", "A robot manipulates an object."), ["dexterous"])

    def test_curated_ids_and_normalized_titles_are_excluded(self):
        recent = watch.fetch_recent(NOW, 7, fetcher=lambda _: feed(entry(), entry("2610.00002", title="A New Hand: Dexterous Manipulation"), entry("2610.00003", title="Remaining dexterous manipulation candidate")))
        curated = {"papers": [{"id": "human-slug", "title": "Different title", "links": {"paper": "https://arxiv.org/abs/2610.00001v2"}}, {"id": "second", "title": "A New Hand — Dexterous Manipulation", "links": {}}]}
        queue, new, updated, trimmed = watch.merge_candidates(recent, {"items": []}, curated, set(), NOW)
        self.assertEqual([paper["id"] for paper in queue["items"]], ["2610.00003"])
        self.assertEqual((new, updated, trimmed), (1, 0, 0))

    def test_rejected_candidate_is_persisted_and_not_resurrected(self):
        recent = watch.fetch_recent(NOW, 7, fetcher=lambda _: feed(entry()))
        rejected = {**recent[0], "review_status": "rejected"}
        queue, *_ = watch.merge_candidates(recent, {"items": [rejected]}, {"papers": []}, set(), NOW)
        self.assertEqual(queue["items"], [])
        self.assertEqual(queue["rejected_ids"], ["2610.00001"])
        queue, *_ = watch.merge_candidates(recent, queue, {"papers": []}, set(), NOW)
        self.assertEqual(queue["items"], [])

    def test_replacement_retains_first_seen_and_counts_as_update(self):
        old = watch.fetch_recent(NOW, 7, fetcher=lambda _: feed(entry()))[0]
        old["first_seen"] = "2026-10-06T14:00:00Z"
        recent = watch.fetch_recent(NOW, 7, fetcher=lambda _: feed(entry("2610.00001v2", updated="2026-10-07T12:00:00Z")))
        queue, new, updated, _ = watch.merge_candidates(recent, {"items": [old]}, {"papers": []}, set(), NOW)
        self.assertEqual(queue["items"][0]["first_seen"], old["first_seen"])
        self.assertEqual((new, updated), (0, 1))

    def test_history_is_bounded_by_age_and_count(self):
        rows, _, _ = watch.parse_feed(feed(entry("2610.00001"), entry("2610.00002"), entry("2501.00001", published="2025-01-01T12:00:00Z")))
        queue, _, _, trimmed = watch.merge_candidates([], {"items": rows}, {"papers": []}, set(), NOW, max_candidates=1)
        self.assertEqual([paper["id"] for paper in queue["items"]], ["2610.00002"])
        self.assertEqual(trimmed, 1)

    def test_pending_branch_history_survives_and_main_rejections_win(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "papers.json").write_text('{"papers": []}')
            rows, _, _ = watch.parse_feed(feed(entry("2610.00001"), entry("2610.00002")))
            previous = folder / "previous.json"
            previous.write_text(json.dumps({"items": rows}))
            (folder / "rejected_ids.json").write_text('["2610.00001"]')
            report = watch.run(folder, now=NOW, fetcher=lambda _: feed(), previous_candidates=previous)
            self.assertEqual([paper["id"] for paper in report["items"]], ["2610.00002"])

    def test_pending_branch_newer_metadata_survives_an_empty_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "papers.json").write_text('{"papers": []}')
            old, _, _ = watch.parse_feed(feed(entry()))
            newer, _, _ = watch.parse_feed(feed(entry("2610.00001v2", updated="2026-10-07T12:00:00Z")))
            (folder / "candidates.json").write_text(json.dumps({"items": old}))
            previous = folder / "previous.json"
            previous.write_text(json.dumps({"items": newer}))
            report = watch.run(folder, now=NOW, fetcher=lambda _: feed(), previous_candidates=previous)
            self.assertEqual(report["items"][0]["updated"], "2026-10-07T12:00:00Z")

    def test_older_rejection_wins_over_newer_pending_metadata(self):
        old, _, _ = watch.parse_feed(feed(entry()))
        old[0]["review_status"] = "rejected"
        newer, _, _ = watch.parse_feed(feed(entry("2610.00001v2", updated="2026-10-07T12:00:00Z")))
        combined = watch.combine_queues({"items": old}, {"items": newer})
        queue, *_ = watch.merge_candidates([], combined, {"papers": []}, set(), NOW)
        self.assertEqual(queue["items"], [])
        self.assertEqual(queue["rejected_ids"], ["2610.00001"])

    def test_failure_never_writes_success_or_changes_curated(self):
        failures = [watch.WatchError("primary endpoint unavailable"), b"<html>gateway failure</html>", feed('<entry><id>http://arxiv.org/api/errors#bad_query</id><title>Error</title><summary>Invalid query</summary></entry>')]
        for failure in failures:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                initial = {"papers.json": '{"papers": []}\n', "watch.json": '{"status":"never_run"}\n', "candidates.json": '{"items": []}\n'}
                for filename, content in initial.items():
                    (folder / filename).write_text(content)
                def fetch(_):
                    if isinstance(failure, Exception):
                        raise failure
                    return failure
                with self.assertRaises(watch.WatchError):
                    watch.run(folder, now=NOW, fetcher=fetch)
                for filename, content in initial.items():
                    self.assertEqual((folder / filename).read_text(), content)

    def test_partial_pagination_failure_does_not_save_partial_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "papers.json").write_text('{"papers": []}')
            with self.assertRaises(watch.WatchError):
                watch.run(folder, now=NOW, fetcher=lambda _: feed(entry(), total=500), sleeper=lambda _: None)
            self.assertFalse((folder / "watch.json").exists())
            self.assertFalse((folder / "candidates.json").exists())

    def test_success_preserves_curated_and_rejections(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            original = '{"papers": [{"id": "curated", "title": "Already curated", "links": {}}]}'
            (folder / "papers.json").write_text(original)
            (folder / "rejected_ids.json").write_text('["2610.00001v9"]')
            report = watch.run(folder, now=NOW, fetcher=lambda _: feed(entry(), entry("2610.00002", title="A new dexterous manipulation method")))
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["last_checked_at"], "2026-10-08T01:35:00Z")
            self.assertEqual(report["candidate_count"], 1)
            self.assertEqual((folder / "papers.json").read_text(), original)
            self.assertEqual(json.loads((folder / "candidates.json").read_text())["rejected_ids"], ["2610.00001"])


if __name__ == "__main__":
    unittest.main()
