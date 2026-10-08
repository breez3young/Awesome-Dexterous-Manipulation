import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

import apply_reviews as apply


TAXONOMY = {
    "categories": ["Dexterous Manipulation", "Tactile Dexterous Manipulation"],
    "tags": ["Tactile feedback", "Reinforcement learning", "Vision"],
}
EMPTY_LEDGER = {"schema_version": 1, "reviews": []}


def review(decision="accept", paper_id="2610.00001"):
    source = {
        "arxiv_id": paper_id, "title": "Dexterous Example " + paper_id,
        "authors": ["One Author", "Second Author"], "published": "2026-10-01T10:00:00Z",
        "updated": "2026-10-08T12:00:00Z", "version": 2,
        "url": f"https://arxiv.org/abs/{paper_id}v2", "primary_urls": [],
    }
    result = {
        "source": source, "decision": decision, "reason_zh": "多指手操作方法，研究范围明确。",
        "review_depth": "abstract",
        "evidence": [{"url": source["url"], "paraphrase": "The abstract studies learned multi-finger object reorientation."}],
    }
    if decision == "accept":
        result["paper"] = {
            "id": "arxiv-" + paper_id, "title": source["title"], "authors": source["authors"].copy(),
            "date": "2026-10-01", "year": 2026, "category": "Dexterous Manipulation",
            "tags": ["Reinforcement learning"], "scope": "core", "tldr": "Learns object reorientation with a multi-finger hand.",
            "tldr_zh": "利用多指手学习物体重定向。", "sensing": [], "hand": [],
            "task": ["Object reorientation"], "method": ["Reinforcement learning"],
            "links": {"paper": f"https://arxiv.org/abs/{paper_id}"},
        }
    return result


def bundle(*reviews):
    return {"schema_version": 1, "rules_version": "dexterous-v1", "reviewed_at": "2026-10-09T08:00:00Z", "reviewer": "Codex", "reviews": list(reviews)}


def catalog():
    return {"title": "Collection", "updated": "2026-10-08", "coverage": {"preserved": True}, "papers": [{
        "id": "human-curated", "title": "Original curated work", "links": {"paper": "https://arxiv.org/abs/1808.00177"},
        "notes_zh": "人工备注必须保留。", "arbitrary_metadata": ["unchanged"],
    }]}


def fulltext(item):
    url = f"https://arxiv.org/html/{item['source']['arxiv_id']}v2#S4"
    item["source"]["primary_urls"].append(url)
    item["review_depth"] = "fulltext"
    item["evidence"].append({"url": url, "paraphrase": "The policy observes fingertip tactile readings at execution time."})
    return url


class ReviewTests(unittest.TestCase):
    def test_accept_preserves_original_fields_and_adds_source_provenance(self):
        original = catalog()
        snapshot = copy.deepcopy(original)
        updated, ledger, counts = apply.prepare(original, EMPTY_LEDGER, bundle(review()), TAXONOMY)
        self.assertEqual(original, snapshot)
        self.assertEqual(updated["papers"][0], snapshot["papers"][0])
        self.assertEqual(updated["coverage"], snapshot["coverage"])
        self.assertEqual(updated["updated"], "2026-10-09")
        self.assertEqual(updated["papers"][1]["arxiv_id"], "2610.00001")
        self.assertEqual(updated["papers"][1]["summary_basis"], "Codex review of arXiv abstract (v2)")
        self.assertEqual(counts["accept"], 1)
        self.assertEqual(len(ledger["reviews"]), 1)

    def test_source_revision_overrides_conflicting_proposed_metadata(self):
        item = review()
        item["paper"]["arxiv_version"] = 99
        item["paper"]["arxiv_updated"] = "2099-01-01T00:00:00Z"
        updated, _, _ = apply.prepare(catalog(), EMPTY_LEDGER, bundle(item), TAXONOMY)
        self.assertEqual(updated["papers"][-1]["arxiv_version"], item["source"]["version"])
        self.assertEqual(updated["papers"][-1]["arxiv_updated"], item["source"]["updated"])

    def test_repeated_batch_is_idempotent_even_if_run_timestamp_changes(self):
        batch = bundle(review())
        first, ledger, _ = apply.prepare(catalog(), EMPTY_LEDGER, batch, TAXONOMY)
        batch["reviewed_at"] = "2026-10-10T08:00:00Z"
        second, second_ledger, counts = apply.prepare(first, ledger, batch, TAXONOMY)
        self.assertEqual(first, second)
        self.assertEqual(ledger, second_ledger)
        self.assertEqual(counts["skipped"], 1)

    def test_defer_and_reject_do_not_change_catalog_or_permanent_rejections(self):
        original = catalog()
        updated, ledger, counts = apply.prepare(original, EMPTY_LEDGER, bundle(review("defer"), review("reject", "2610.00002")), TAXONOMY)
        self.assertEqual(updated, original)
        self.assertNotIn("rejected_ids", ledger)
        self.assertEqual([e["review"]["decision"] for e in ledger["reviews"]], ["defer", "reject"])

    def test_resolution_retains_deferral_history_and_is_idempotent(self):
        original, ledger, _ = apply.prepare(catalog(), EMPTY_LEDGER, bundle(review("defer")), TAXONOMY)
        resolved = review()
        fulltext(resolved)
        batch = bundle(resolved)
        batch["reviewed_at"] = "2026-10-10T08:00:00Z"
        updated, ledger, counts = apply.prepare(original, ledger, batch, TAXONOMY)
        self.assertEqual(counts["resolved"], 1)
        self.assertEqual(len(ledger["reviews"]), 1)
        self.assertEqual(ledger["reviews"][0]["history"][0]["review"]["decision"], "defer")
        again, _, counts = apply.prepare(updated, ledger, batch, TAXONOMY)
        self.assertEqual(again, updated)
        self.assertEqual(counts["skipped"], 1)

    def test_defer_resolution_without_new_evidence_fails(self):
        original, ledger, _ = apply.prepare(catalog(), EMPTY_LEDGER, bundle(review("defer")), TAXONOMY)
        batch = bundle(review())
        batch["reviewed_at"] = "2026-10-10T08:00:00Z"
        with self.assertRaisesRegex(apply.ReviewError, "new evidence"):
            apply.prepare(original, ledger, batch, TAXONOMY)

    def test_existing_decision_cannot_be_silently_reversed(self):
        original, ledger, _ = apply.prepare(catalog(), EMPTY_LEDGER, bundle(review("reject")), TAXONOMY)
        with self.assertRaisesRegex(apply.ReviewError, "different decision"):
            apply.prepare(original, ledger, bundle(review()), TAXONOMY)

    def test_new_source_revision_can_receive_a_new_decision(self):
        original, ledger, _ = apply.prepare(catalog(), EMPTY_LEDGER, bundle(review("reject")), TAXONOMY)
        revised = review()
        revised["source"].update(version=3, updated="2026-10-09T07:00:00Z", url="https://arxiv.org/abs/2610.00001v3")
        revised["evidence"][0]["url"] = revised["source"]["url"]
        updated, ledger, counts = apply.prepare(original, ledger, bundle(revised), TAXONOMY)
        self.assertEqual(counts["accept"], 1)
        self.assertEqual(len(ledger["reviews"]), 2)
        self.assertEqual(len(updated["papers"]), 2)

    def test_identity_and_taxonomy_must_be_verified(self):
        mutations = [
            lambda r: r["paper"].update(title="Invented title"),
            lambda r: r["paper"].update(authors=["Invented Author"]),
            lambda r: r["paper"].update(date="2026-10-08"),
            lambda r: r["paper"].update(year=2025),
            lambda r: r["paper"].update(category="Miscellaneous"),
            lambda r: r["paper"].update(tags=["Invented tag"]),
            lambda r: r["source"].update(version=True),
            lambda r: r["source"].update(updated="2026-10-10T00:00:00Z"),
            lambda r: r["source"].update(published="2026-10-01"),
            lambda r: r.update(reason_zh="An English-only reason"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                item = review()
                mutate(item)
                with self.assertRaises(apply.ReviewError):
                    apply.prepare(catalog(), EMPTY_LEDGER, bundle(item), TAXONOMY)

    def test_missing_or_unverified_evidence_and_links_fail(self):
        mutations = [
            lambda r: r.update(evidence=[]),
            lambda r: r["evidence"][0].update(url="https://invented.example/"),
            lambda r: r["paper"]["links"].update(code="https://github.com/invented/repository"),
            lambda r: r["source"].update(primary_urls=["javascript:alert(1)"]),
            lambda r: r["source"].update(primary_urls=["https://arxiv.org/html/2610.00002v2"]),
            lambda r: r["source"].update(primary_urls=["https://arxiv.org/html/2610.00001v1"]),
            lambda r: r.update(review_depth="fulltext"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                item = review()
                mutate(item)
                with self.assertRaises(apply.ReviewError):
                    apply.prepare(catalog(), EMPTY_LEDGER, bundle(item), TAXONOMY)

    def test_tactile_accept_requires_explicit_fulltext_runtime_evidence(self):
        item = review()
        item["paper"].update(category="Tactile Dexterous Manipulation", tags=["Tactile feedback"])
        with self.assertRaisesRegex(apply.ReviewError, "fulltext runtime"):
            apply.prepare(catalog(), EMPTY_LEDGER, bundle(item), TAXONOMY)
        url = fulltext(item)
        item["runtime_tactile"] = {"uses_at_execution": False, "url": url, "paraphrase": "Contact labels only supervise training."}
        with self.assertRaisesRegex(apply.ReviewError, "deployed policy"):
            apply.prepare(catalog(), EMPTY_LEDGER, bundle(item), TAXONOMY)
        item["runtime_tactile"].update(uses_at_execution=True, paraphrase="Fingertip touch readings are policy inputs during deployment.")
        updated, _, counts = apply.prepare(catalog(), EMPTY_LEDGER, bundle(item), TAXONOMY)
        self.assertEqual(counts["accept"], 1)
        self.assertEqual(updated["papers"][-1]["category"], "Tactile Dexterous Manipulation")

    def test_existing_curated_arxiv_id_title_or_local_id_never_overwritten(self):
        for field in ("arxiv", "title", "local_id"):
            original = catalog()
            item = review()
            if field == "arxiv":
                original["papers"][0]["links"]["paper"] = item["paper"]["links"]["paper"] + "v1"
            elif field == "title":
                original["papers"][0]["title"] = item["paper"]["title"].upper()
            else:
                item["paper"]["id"] = original["papers"][0]["id"]
            with self.subTest(field=field), self.assertRaisesRegex(apply.ReviewError, "never overwritten"):
                apply.prepare(original, EMPTY_LEDGER, bundle(item), TAXONOMY)

    def test_duplicate_bundle_and_tampered_ledger_fail(self):
        item = review()
        with self.assertRaisesRegex(apply.ReviewError, "duplicate review"):
            apply.prepare(catalog(), EMPTY_LEDGER, bundle(item, item), TAXONOMY)
        updated, ledger, _ = apply.prepare(catalog(), EMPTY_LEDGER, bundle(item), TAXONOMY)
        ledger["reviews"][0]["review"]["decision"] = "reject"
        with self.assertRaisesRegex(apply.ReviewError, "integrity"):
            apply.prepare(updated, ledger, bundle(item), TAXONOMY)

    def test_accepted_ledger_without_matching_catalog_requires_recovery(self):
        _, ledger, _ = apply.prepare(catalog(), EMPTY_LEDGER, bundle(review()), TAXONOMY)
        with self.assertRaisesRegex(apply.ReviewError, "inconsistent"):
            apply.prepare(catalog(), ledger, bundle(review()), TAXONOMY)

    def files(self, directory, batch):
        paths = {name: Path(directory) / (name + ".json") for name in ("catalog", "ledger", "reviews", "taxonomy")}
        for name, document in (("catalog", catalog()), ("ledger", EMPTY_LEDGER), ("reviews", batch), ("taxonomy", TAXONOMY)):
            paths[name].write_text(json.dumps(document, ensure_ascii=False) + "\n", encoding="utf-8")
        args = [part for key, path in paths.items() for part in ("--" + key, str(path))]
        return paths, args

    def test_entire_batch_validates_before_any_file_is_written(self):
        bad = review("accept", "2610.00002")
        bad["paper"]["date"] = "2026-10-08"
        with tempfile.TemporaryDirectory() as directory:
            paths, args = self.files(directory, bundle(review(), bad))
            before = {name: path.read_bytes() for name, path in paths.items()}
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(apply.main(args), 1)
            self.assertEqual(before, {name: path.read_bytes() for name, path in paths.items()})

    def test_dry_run_writes_nothing_and_success_only_updates_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            paths, args = self.files(directory, bundle(review()))
            before = {name: path.read_bytes() for name, path in paths.items()}
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(apply.main([*args, "--dry-run"]), 0)
            self.assertEqual(before, {name: path.read_bytes() for name, path in paths.items()})
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(apply.main(args), 0)
            after = {name: path.read_bytes() for name, path in paths.items()}
            self.assertEqual(before["reviews"], after["reviews"])
            self.assertEqual(before["taxonomy"], after["taxonomy"])
            self.assertNotEqual(before["catalog"], after["catalog"])
            self.assertNotEqual(before["ledger"], after["ledger"])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(apply.main(args), 0)
            self.assertEqual(after, {name: path.read_bytes() for name, path in paths.items()})


if __name__ == "__main__":
    unittest.main()
