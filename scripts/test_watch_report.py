"""Review output must not turn untrusted paper metadata into markup or URLs."""

import unittest

from dexterous_watch import WatchError
from watch_report import render


def report(**changes):
    return {
        "status": "ok", "last_checked_at": "2026-10-08T01:35:00Z", "lookback_days": 7,
        "candidate_count": 1, "new_candidate_count": 1, "updated_candidate_count": 0,
        "items": [{"id": "2610.00001v2", "title": "A dexterous robot hand",
                   "published": "2026-10-06T12:00:00Z", "updated": "2026-10-07T12:00:00Z",
                   "matched_topics": ["dexterous", "tactile"]}], **changes,
    }


class ReportTests(unittest.TestCase):
    def test_untrusted_metadata_cannot_change_report_links_or_table(self):
        data = report()
        data["items"][0]["title"] = "Hand | [click](https://example.com) <img src=x>\n@everyone"
        data["items"][0]["links"] = {"paper": "https://example.com"}
        output = render(data)
        self.assertIn("(https://arxiv.org/abs/2610.00001)", output)
        self.assertIn("Hand \\| \\[click\\]\\(", output)
        self.assertNotIn("<img", output)
        self.assertNotIn("@everyone", output)
        self.assertNotIn("[click](https://example.com)", output)
        self.assertIn("2026-10-06 | 2026-10-07", output)

    def test_invalid_link_or_failed_scan_is_not_rendered_as_success(self):
        data = report()
        data["items"][0]["id"] = "https://example.com"
        for candidate in (data, report(status="failed")):
            with self.assertRaises(WatchError):
                render(candidate)

    def test_queue_is_bounded_in_report_but_full_count_remains_visible(self):
        data = report()
        data["items"] *= 35
        data["candidate_count"] = 35
        output = render(data)
        self.assertEqual(output.count("https://arxiv.org/abs/"), 30)
        self.assertIn("待审 **35** 篇", output)
        self.assertIn("完整队列", output)

    def test_discovery_summary_routes_approval_to_the_codex_pr_only(self):
        output = render(report())
        self.assertIn("等待 Codex 审核", output)
        self.assertIn("不创建 PR", output)
        self.assertIn("bot/codex-paper-review", output)
        self.assertIn("此分支无需合并", output)
        self.assertNotIn("合并本 PR", output)


if __name__ == "__main__":
    unittest.main()
