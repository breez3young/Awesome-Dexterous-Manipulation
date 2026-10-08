#!/usr/bin/env python3
"""Validate a Codex review bundle and apply it to a review-branch catalog copy.

No network/model calls, candidate-queue edits, commits, pushes or publication.
The caller supplies taxonomy exported from catalog-core.js. All validation runs
before either output is replaced; replacements are atomic per file, not a
two-file transaction. Commit the catalog and ledger together after success.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ARXIV_ID = re.compile(r"(?:\d{4}\.\d{4,5}|[a-z][a-z.\-]+/\d{7})", re.I)
CHINESE = re.compile(r"[\u3400-\u9fff]")


class ReviewError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReviewError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def timestamp(value):
    require(isinstance(value, str), "Timestamp must be a string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(result.tzinfo is not None, "Timestamp needs a timezone")
        return result.astimezone(timezone.utc)
    except ValueError as exc:
        raise ReviewError(f"Invalid timestamp: {value!r}") from exc


def normalized_id(value):
    if not isinstance(value, str):
        return None
    if "://" in value:
        parsed = urlparse(value)
        if parsed.hostname not in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
            return None
        value = re.sub(r"^/(abs|pdf|html)/", "", parsed.path)
    value = re.sub(r"\.pdf$", "", value, flags=re.I)
    value = re.sub(r"v\d+$", "", value, flags=re.I)
    return value.lower() if ARXIV_ID.fullmatch(value) else None


def normalized_title(value):
    return "".join(c for c in unicodedata.normalize("NFKC", value).casefold() if c.isalnum())


def safe_url(value):
    if not isinstance(value, str) or re.search(r"[\s\x00-\x1f]", value):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def string_list(value, label, allow_empty=True):
    require(isinstance(value, list) and all(nonempty(x) for x in value), f"{label} must be an array of nonempty strings")
    require(allow_empty or bool(value), f"{label} cannot be empty")
    require(len(value) == len(set(value)), f"{label} contains duplicates")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def review_key(review, rules_version):
    source = review["source"]
    updated = timestamp(source["updated"]).isoformat()
    return f"{source['arxiv_id']}|v{source['version']}|{updated}|{rules_version}"


def validate_review(review, taxonomy, reviewed_at):
    require(isinstance(review, dict), "Every review must be an object")
    source = review.get("source")
    require(isinstance(source, dict), "A review needs verified source metadata")
    paper_id = source.get("arxiv_id")
    require(normalized_id(paper_id) == paper_id and bool(paper_id), "Source arxiv_id must be canonical and unversioned")
    require(nonempty(source.get("title")), "Source title is required")
    string_list(source.get("authors"), "Source authors", allow_empty=False)
    published, updated = timestamp(source.get("published")), timestamp(source.get("updated"))
    require(published <= updated <= reviewed_at, "Source dates must satisfy published <= updated <= reviewed_at")
    version = source.get("version")
    require(type(version) is int and version >= 1, "Source version must be a positive integer")
    expected_url = f"https://arxiv.org/abs/{paper_id}v{version}"
    require(source.get("url") == expected_url, "Source URL must identify the reviewed arXiv version")
    primary_urls = source.get("primary_urls", [])
    string_list(primary_urls, "Inspected primary_urls")
    require(all(safe_url(url) for url in primary_urls), "Primary URLs must be safe HTTPS addresses")
    for url in primary_urls:
        if urlparse(url).hostname in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
            require(normalized_id(url) == paper_id, "An arXiv primary URL points to a different paper")
            require(re.search(rf"v{version}(?:\.pdf)?$", urlparse(url).path), "Inspected arXiv URLs must identify the reviewed version")
    allowed_urls = {source["url"], *primary_urls}
    require(review.get("decision") in {"accept", "defer", "reject"}, "Unknown review decision")
    require(nonempty(review.get("reason_zh")) and CHINESE.search(review["reason_zh"]), "A Chinese decision reason is required")
    require(review.get("review_depth") in {"abstract", "fulltext"}, "Review depth must be abstract or fulltext")
    evidence = review.get("evidence")
    require(isinstance(evidence, list) and evidence, "At least one primary-source evidence paraphrase is required")
    for item in evidence:
        require(isinstance(item, dict) and item.get("url") in allowed_urls and nonempty(item.get("paraphrase")), "Evidence needs an inspected primary URL and nonempty paraphrase")
    evidence_urls = {item["url"] for item in evidence}
    fulltext_urls = {u for u in evidence_urls if urlparse(u).hostname == "arxiv.org" and urlparse(u).path.startswith(("/html/", "/pdf/"))}
    if review["review_depth"] == "fulltext":
        require(bool(fulltext_urls), "Fulltext review needs an arXiv HTML/PDF evidence URL")
    if review["decision"] != "accept":
        require("paper" not in review, "Only accepted reviews can contain a proposed paper")
        return
    paper = review.get("paper")
    require(isinstance(paper, dict), "Accepted reviews require a proposed paper")
    require(nonempty(paper.get("id")), "Proposed paper ID is required")
    for key in ("title", "authors"):
        require(paper.get(key) == source[key], f"Proposed {key} differs from verified source")
    expected_date = published.date().isoformat()
    require(paper.get("date") == expected_date and type(paper.get("year")) is int and paper["year"] == published.year, "Proposed date/year must use the first arXiv submission")
    require(paper.get("category") in taxonomy["categories"], "Unknown research area")
    string_list(paper.get("tags"), "Paper tags")
    require(set(paper["tags"]) <= set(taxonomy["tags"]), "Unknown paper tag")
    require(paper.get("scope") in {"core", "adjacent"}, "Paper scope must be core or adjacent")
    require(nonempty(paper.get("tldr")) and nonempty(paper.get("tldr_zh")) and CHINESE.search(paper["tldr_zh"]), "English and Chinese summaries are required")
    for field in ("sensing", "hand", "task", "method"):
        string_list(paper.get(field), f"Paper {field}")
    links = paper.get("links")
    require(isinstance(links, dict) and links.get("paper") == f"https://arxiv.org/abs/{paper_id}", "Paper link must be the canonical arXiv abstract URL")
    for kind, url in links.items():
        require(safe_url(url), f"Unsafe {kind} link")
        require(kind == "paper" or url in allowed_urls, f"Unverified {kind} link")
    if "arxiv_id" in paper:
        require(paper["arxiv_id"] == paper_id, "Proposed arxiv_id conflicts with source")
    if "Tactile feedback" in paper["tags"] or paper["category"] == "Tactile Dexterous Manipulation":
        tactile = review.get("runtime_tactile")
        require(review["review_depth"] == "fulltext" and isinstance(tactile, dict), "Tactile feedback requires fulltext runtime evidence")
        require(tactile.get("uses_at_execution") is True and tactile.get("url") in fulltext_urls and nonempty(tactile.get("paraphrase")), "Runtime tactile evidence must explicitly confirm touch enters the deployed policy")


def prepare(catalog, ledger, bundle, taxonomy):
    """Return new documents without mutating any input or touching the filesystem."""
    require(isinstance(catalog, dict) and isinstance(catalog.get("papers"), list), "Catalog must contain papers")
    require(isinstance(taxonomy, dict), "Taxonomy must be an object")
    for field in ("categories", "tags"):
        string_list(taxonomy.get(field), f"Taxonomy {field}", allow_empty=False)
    require(isinstance(bundle, dict) and bundle.get("schema_version") == 1, "Unsupported review-bundle schema")
    require(nonempty(bundle.get("rules_version")) and "|" not in bundle["rules_version"], "rules_version is required")
    require(nonempty(bundle.get("reviewer")), "reviewer is required")
    reviewed_at = timestamp(bundle.get("reviewed_at"))
    require(isinstance(bundle.get("reviews"), list), "Bundle must contain reviews")
    require(isinstance(ledger, dict) and ledger.get("schema_version") == 1 and isinstance(ledger.get("reviews"), list), "Unsupported review ledger")
    indexed = {}
    for entry in ledger["reviews"]:
        require(isinstance(entry, dict) and isinstance(entry.get("review"), dict) and nonempty(entry.get("rules_version")), "Malformed existing review ledger entry")
        require(entry.get("key") == review_key(entry["review"], entry["rules_version"]) and entry.get("digest") == digest(entry["review"]), "Existing review ledger entry failed integrity validation")
        require(entry["key"] not in indexed, "Duplicate existing review ledger key")
        indexed[entry["key"]] = entry
    new_catalog, new_ledger = copy.deepcopy(catalog), copy.deepcopy(ledger)
    ids, arxiv_ids, titles = set(), {}, {}
    for paper in new_catalog["papers"]:
        require(isinstance(paper, dict) and nonempty(paper.get("id")) and nonempty(paper.get("title")), "Malformed existing catalog paper")
        require(paper["id"] not in ids, "Existing catalog contains duplicate IDs")
        ids.add(paper["id"])
        titles[normalized_title(paper["title"])] = paper
        for value in (paper.get("arxiv_id"), paper.get("id"), paper.get("links", {}).get("paper")):
            if pid := normalized_id(value):
                require(pid not in arxiv_ids or arxiv_ids[pid] is paper, "Existing catalog contains duplicate arXiv IDs")
                arxiv_ids[pid] = paper
    counts = {"accept": 0, "defer": 0, "reject": 0, "skipped": 0, "resolved": 0}
    seen = set()
    for review in bundle["reviews"]:
        validate_review(review, taxonomy, reviewed_at)
        key = review_key(review, bundle["rules_version"])
        require(key not in seen, "Bundle contains a duplicate review key")
        seen.add(key)
        previous = indexed.get(key)
        resolving = False
        if previous and previous["digest"] != digest(review):
            resolving = previous["review"].get("decision") == "defer" and review["decision"] in {"accept", "reject"}
            require(resolving and reviewed_at > timestamp(previous["reviewed_at"]), "A different decision already exists for this source/rules version")
            require(review["evidence"] != previous["review"].get("evidence"), "Resolving a deferral requires new evidence")
            for field in ("arxiv_id", "title", "authors", "published", "updated", "version", "url"):
                require(review["source"][field] == previous["review"]["source"][field], "Resolution changed verified source identity")
        if previous and not resolving:
            if review["decision"] == "accept":
                existing = arxiv_ids.get(review["source"]["arxiv_id"])
                require(existing == reviewed_paper(review), "Accepted ledger entry and catalog are inconsistent; recover the matching review-branch files")
            counts["skipped"] += 1
            continue
        if review["decision"] == "accept":
            paper = reviewed_paper(review)
            pid, title = review["source"]["arxiv_id"], normalized_title(paper["title"])
            require(pid not in arxiv_ids and title not in titles and paper["id"] not in ids, "Accepted paper conflicts with an existing curated entry; existing papers are never overwritten")
            new_catalog["papers"].append(paper)
            arxiv_ids[pid], titles[title] = paper, paper
            ids.add(paper["id"])
        entry = {"key": key, "digest": digest(review), "rules_version": bundle["rules_version"], "reviewed_at": bundle["reviewed_at"], "reviewer": bundle["reviewer"], "review": copy.deepcopy(review)}
        if resolving:
            old = copy.deepcopy(previous)
            history = old.pop("history", [])
            entry["history"] = [*history, old]
            new_ledger["reviews"] = [entry if e["key"] == key else e for e in new_ledger["reviews"]]
            counts["resolved"] += 1
        else:
            new_ledger["reviews"].append(entry)
        indexed[key] = entry
        counts[review["decision"]] += 1
    if counts["accept"]:
        new_catalog["updated"] = max(new_catalog.get("updated", ""), reviewed_at.date().isoformat())
    return new_catalog, new_ledger, counts


def reviewed_paper(review):
    """Use source identity and helper-generated provenance, not model assertions."""
    paper, source = copy.deepcopy(review["paper"]), review["source"]
    paper.update(arxiv_id=source["arxiv_id"], arxiv_version=source["version"], arxiv_updated=source["updated"], title=source["title"], authors=list(source["authors"]), date=timestamp(source["published"]).date().isoformat(), year=timestamp(source["published"]).year)
    paper.update(source_url=source["url"], sources=list(dict.fromkeys(e["url"] for e in review["evidence"])), summary_basis=f"Codex review of arXiv {review['review_depth']} (v{source['version']})", date_kind="First arXiv submission")
    return paper


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReviewError(f"Cannot read {path}: {exc}") from exc


def atomic_json(path, document):
    text = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("catalog", "ledger", "reviews", "taxonomy"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        paths = [args.catalog, args.ledger, args.reviews, args.taxonomy]
        require(len({p.resolve() for p in paths}) == len(paths), "All input/output paths must be distinct")
        catalog = read_json(args.catalog)
        ledger = read_json(args.ledger) if args.ledger.exists() else {"schema_version": 1, "reviews": []}
        updated, decisions, counts = prepare(catalog, ledger, read_json(args.reviews), read_json(args.taxonomy))
        if not args.dry_run:
            # Atomic individually. A failed second write is a failed run; the
            # caller must not commit either output until the whole run succeeds.
            atomic_json(args.catalog, updated)
            atomic_json(args.ledger, decisions)
        print(json.dumps({"dry_run": args.dry_run, **counts}, ensure_ascii=False))
        return 0
    except (ReviewError, OSError, KeyError, TypeError) as exc:
        print(f"Review batch not applied successfully: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
