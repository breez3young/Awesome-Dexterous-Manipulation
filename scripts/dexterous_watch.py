#!/usr/bin/env python3
"""Collect unreviewed arXiv candidates without modifying the curated collection.

Python 3.10+; standard library only. Run from the collection repository root:
    python3 scripts/dexterous_watch.py

Optional rejected_ids.json can be either an array of
arXiv IDs or {"rejected_ids": [...]}. Versions/URLs are accepted. Rejections are
retained in candidates.json's rejected_ids as well; remove an ID from both places
to reconsider it.

The seven-day window uses arXiv's *updated* timestamp, so replacements of older
papers are included. The API has no updated-date range filter: pages are sorted
by lastUpdatedDate and fetched until the cutoff is crossed. If that cannot be
completed, the script fails without writing a misleading success report.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path


API_URL = "https://export.arxiv.org/api/query"
SEARCH_QUERY = (
    '(all:"dexterous manipulation" OR all:"in-hand manipulation" '
    'OR all:"in hand manipulation" OR all:multifinger OR all:"multi-finger" '
    'OR all:"multi finger" OR (all:tactile AND '
    '(all:dexterous OR all:"in-hand" OR all:multifinger OR all:"multi-finger")))'
)
NS = {"atom": "http://www.w3.org/2005/Atom", "os": "http://a9.com/-/spec/opensearch/1.1/"}
DEXTEROUS = re.compile(r"\bdexterous\s+manipulation\b|\bin[\s-]+hand\s+manipulation\b", re.I)
MULTIFINGER = re.compile(r"\bmulti[\s-]*finger(?:ed)?\b", re.I)
TACTILE = re.compile(r"\btactile\b|\btouch\b|\bhaptic\b", re.I)
HAND = re.compile(r"\bdexterous\b|\bin[\s-]+hand\b|\bmulti[\s-]*finger(?:ed)?\b", re.I)
CONTEXT = re.compile(r"\b(?:manipulat\w*|grasp\w*|robot\w*|hand|hands)\b", re.I)
ARXIV_ID = re.compile(r"(?:\d{4}\.\d{4,5}|[a-z][a-z.\-]+/\d{7})(?:v\d+)?", re.I)


class WatchError(RuntimeError):
    """An incomplete or invalid scan must never replace the last good report."""


def utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_date(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone missing")
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError) as exc:
        raise WatchError(f"Invalid arXiv timestamp: {value!r}") from exc


def normalize_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value.lower().startswith("arxiv:"):
        value = value[6:].strip()
    if "://" in value:
        parsed = urllib.parse.urlparse(value)
        if parsed.hostname not in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
            return None
        value = re.sub(r"^/(?:abs|pdf)/", "", parsed.path)
    value = re.sub(r"\.pdf$", "", value, flags=re.I)
    if not ARXIV_ID.fullmatch(value):
        return None
    return re.sub(r"v\d+$", "", value, flags=re.I).lower()


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in value if character.isalnum())


def text_content(element: ET.Element, name: str) -> str:
    return " ".join((element.findtext(f"atom:{name}", "", NS)).split())


def classify(title: str, abstract: str) -> list[str]:
    text = title + " " + abstract
    dexterous = bool(DEXTEROUS.search(text) or (MULTIFINGER.search(text) and CONTEXT.search(text)))
    tactile = bool(TACTILE.search(text) and HAND.search(text) and CONTEXT.search(text))
    return (["dexterous"] if dexterous or tactile else []) + (["tactile"] if tactile else [])


def evidence(title: str, abstract: str) -> list[dict[str, str]]:
    """A short source excerpt is evidence for screening, never a generated TLDR."""
    for source, text in (("abstract", abstract), ("title", title)):
        match = DEXTEROUS.search(text) or MULTIFINGER.search(text) or HAND.search(text)
        if not match:
            continue
        words = text.split()
        word_index = len(text[:match.start()].split())
        start = max(0, word_index - 6)
        end = min(len(words), start + 22)
        snippet = ("… " if start else "") + " ".join(words[start:end]) + (" …" if end < len(words) else "")
        return [{"source": source, "text": snippet}]
    return []


def parse_feed(raw: bytes) -> tuple[list[dict], int, int]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise WatchError("arXiv returned invalid XML") from exc
    if root.tag != "{" + NS["atom"] + "}feed":
        raise WatchError("arXiv returned something other than an Atom feed")
    rows = []
    for entry in root.findall("atom:entry", NS):
        entry_id = text_content(entry, "id")
        if "/api/errors" in entry_id or text_content(entry, "title").lower() == "error":
            raise WatchError("arXiv API error: " + text_content(entry, "summary"))
        paper_id = normalize_id(entry_id)
        title, abstract = text_content(entry, "title"), text_content(entry, "summary")
        if not paper_id or not title:
            raise WatchError("arXiv entry lacks a valid ID or title")
        rows.append({
            "id": paper_id,
            "title": title,
            "authors": [" ".join((author.findtext("atom:name", "", NS)).split()) for author in entry.findall("atom:author", NS)],
            "published": utc(parse_date(text_content(entry, "published"))),
            "updated": utc(parse_date(text_content(entry, "updated"))),
            "links": {"paper": f"https://arxiv.org/abs/{paper_id}", "pdf": f"https://arxiv.org/pdf/{paper_id}"},
            "matched_topics": classify(title, abstract),
            "evidence": evidence(title, abstract),
            "review_status": "pending",
        })
    try:
        total = int(root.findtext("os:totalResults", "", NS))
        start = int(root.findtext("os:startIndex", "", NS))
    except ValueError as exc:
        raise WatchError("arXiv feed lacks valid pagination metadata") from exc
    if total < 0 or start < 0 or total < start + len(rows):
        raise WatchError("Inconsistent arXiv pagination metadata")
    return rows, total, start


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "DexterousCollectionWatch/1.0 (daily arXiv metadata research collection)",
        "Accept": "application/atom+xml",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == 2:
                raise WatchError(f"arXiv fetch failed after 3 attempts: {exc}") from exc
            time.sleep(4 * (attempt + 1))
    raise AssertionError("unreachable")


def fetch_recent(now: datetime, days: int, fetcher=download, sleeper=time.sleep, page_size: int = 100, max_pages: int = 20) -> list[dict]:
    cutoff = now - timedelta(days=days)
    newest: dict[str, dict] = {}
    previous_date = None
    for page in range(max_pages):
        if page:
            sleeper(3)
        start = page * page_size
        params = {"search_query": SEARCH_QUERY, "sortBy": "lastUpdatedDate", "sortOrder": "descending", "start": start, "max_results": page_size}
        rows, total, actual_start = parse_feed(fetcher(API_URL + "?" + urllib.parse.urlencode(params)))
        if actual_start != start:
            raise WatchError("arXiv returned the wrong page; scan is incomplete")
        if not rows and start < total:
            raise WatchError("arXiv returned an empty page before the end of results")
        crossed_cutoff = False
        for paper in rows:
            updated = parse_date(paper["updated"])
            if previous_date is not None and updated > previous_date:
                raise WatchError("arXiv results are not sorted by lastUpdatedDate")
            previous_date = updated
            if updated < cutoff:
                crossed_cutoff = True
                continue
            if updated > now or not paper["matched_topics"]:
                continue
            old = newest.get(paper["id"])
            if old is None or paper["updated"] > old["updated"]:
                newest[paper["id"]] = paper
        if crossed_cutoff or start + len(rows) >= total:
            return list(newest.values())
        if len(rows) != page_size:
            raise WatchError("arXiv returned a short page before the end of results")
    raise WatchError(f"More than {max_pages * page_size} recent results; increase max_pages before claiming success")


def read_json(path: Path, default=None):
    if not path.exists() and default is not None:
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise WatchError(f"Cannot read {path}: {exc}") from exc


def curated_keys(document: dict) -> tuple[set[str], set[str]]:
    if not isinstance(document, dict) or not isinstance(document.get("papers"), list):
        raise WatchError("papers.json must contain a papers array")
    ids, titles = set(), set()
    for paper in document["papers"]:
        if not isinstance(paper, dict):
            raise WatchError("Curated papers must be objects")
        for value in (paper.get("id"), paper.get("arxiv_id"), paper.get("links", {}).get("paper")):
            if paper_id := normalize_id(value):
                ids.add(paper_id)
        if paper.get("title"):
            titles.add(normalize_title(paper["title"]))
    return ids, titles


def reject_keys(document) -> set[str]:
    values = document.get("rejected_ids", []) if isinstance(document, dict) else document
    if not isinstance(values, list):
        raise WatchError("rejected_ids must be an array")
    result = set()
    for value in values:
        paper_id = normalize_id(value)
        if not paper_id:
            raise WatchError(f"Invalid rejected arXiv ID: {value!r}")
        result.add(paper_id)
    return result


def merge_candidates(recent: list[dict], existing: dict, curated: dict, rejected: set[str], now: datetime, retain_days: int = 180, max_candidates: int = 500) -> tuple[dict, int, int, int]:
    curated_ids, curated_titles = curated_keys(curated)
    if not isinstance(existing, dict):
        raise WatchError("candidates.json must be an object")
    rejected = rejected | reject_keys(existing)
    if not isinstance(existing.get("items", []), list):
        raise WatchError("candidates.json must contain an items array")
    timestamp, cutoff = utc(now), now - timedelta(days=retain_days)
    merged = {}
    def eligible(paper):
        return paper["id"] not in curated_ids | rejected and normalize_title(paper["title"]) not in curated_titles
    for paper in existing.get("items", []):
        paper = dict(paper)
        paper["id"] = normalize_id(paper.get("id"))
        if not paper["id"] or not paper.get("title"):
            raise WatchError("Existing candidate lacks a valid ID or title")
        if paper.get("review_status") == "rejected":
            rejected.add(paper["id"])
            continue
        # Age by arXiv update, not repeated daily sightings, to bound history.
        if eligible(paper) and parse_date(paper["updated"]) >= cutoff:
            old = merged.get(paper["id"])
            if old is None or paper["updated"] > old["updated"]:
                merged[paper["id"]] = paper
    new_count = updated_count = 0
    for paper in recent:
        if not eligible(paper):
            continue
        old = merged.get(paper["id"])
        if old and old["updated"] > paper["updated"]:
            continue
        item = dict(paper)
        item["first_seen"] = old.get("first_seen", timestamp) if old else timestamp
        item["last_seen"] = timestamp
        if old and old.get("review_status"):
            item["review_status"] = old["review_status"]
        if old is None:
            new_count += 1
        elif any(old.get(key) != item.get(key) for key in ("title", "updated", "authors", "matched_topics", "evidence")):
            updated_count += 1
        merged[item["id"]] = item
    items = sorted((item for item in merged.values() if item["id"] not in rejected), key=lambda paper: (paper["updated"], paper["id"]), reverse=True)
    trimmed_count = max(0, len(items) - max_candidates)
    return {"schema_version": 1, "updated_at": timestamp, "rejected_ids": sorted(rejected), "items": items[:max_candidates]}, new_count, updated_count, trimmed_count


def atomic_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, encoding="utf-8", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def combine_queues(primary: dict, pending: dict) -> dict:
    """Keep newer bot metadata while preserving explicit editorial rejections."""
    indexed, rejected = {}, set()
    for document in (pending, primary):
        if not isinstance(document, dict) or not isinstance(document.get("items", []), list):
            raise WatchError("Candidate queue must be an object with an items array")
        rejected |= reject_keys(document)
        for item in document.get("items", []):
            if not isinstance(item, dict) or not (paper_id := normalize_id(item.get("id"))):
                raise WatchError("Existing candidate lacks a valid arXiv ID")
            item = {**item, "id": paper_id}
            if item.get("review_status") == "rejected":
                rejected.add(paper_id)
            old = indexed.get(paper_id)
            if old is None or parse_date(item["updated"]) >= parse_date(old["updated"]):
                indexed[paper_id] = item
    return {"items": list(indexed.values()), "rejected_ids": sorted(rejected)}


def run(data_dir: Path, now: datetime | None = None, fetcher=download, sleeper=time.sleep, days: int = 7, previous_candidates: Path | None = None, rejected_ids: Path | None = None, retain_days: int = 180, max_candidates: int = 500) -> dict:
    now = now or datetime.now(timezone.utc)
    curated = read_json(data_dir / "papers.json")
    curated_keys(curated)
    existing = read_json(data_dir / "candidates.json", {"items": []})
    if previous_candidates and previous_candidates.exists():
        pending = read_json(previous_candidates)
        existing = combine_queues(existing, pending)
    rejected = reject_keys(read_json(rejected_ids or data_dir / "rejected_ids.json", []))
    recent = fetch_recent(now, days, fetcher=fetcher, sleeper=sleeper)
    candidates, new_count, updated_count, trimmed_count = merge_candidates(recent, existing, curated, rejected, now, retain_days, max_candidates)
    visible_keys = ("id", "title", "published", "updated", "links", "matched_topics", "evidence", "review_status")
    report = {
        "schema_version": 1,
        "status": "ok",
        "last_checked_at": utc(now),
        "lookback_days": days,
        "window_start": utc(now - timedelta(days=days)),
        "source": "arXiv API",
        "source_url": API_URL,
        "query": SEARCH_QUERY,
        "review_required": True,
        "candidate_count": len(candidates["items"]),
        "recent_match_count": len(recent),
        "new_candidate_count": new_count,
        "updated_candidate_count": updated_count,
        "trimmed_count": trimmed_count,
        "retention_days": retain_days,
        "items": [{key: paper[key] for key in visible_keys if key in paper} for paper in candidates["items"]],
    }
    # No output is touched until the entire network scan and validation succeed.
    # Write the success report last; it describes the queue written immediately above.
    atomic_json(data_dir / "candidates.json", candidates)
    atomic_json(data_dir / "watch.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--retain-days", type=int, default=180)
    parser.add_argument("--max-candidates", type=int, default=500)
    parser.add_argument("--previous-candidates", type=Path)
    parser.add_argument("--rejected-ids", type=Path)
    args = parser.parse_args()
    if min(args.days, args.retain_days, args.max_candidates) < 1:
        parser.error("days, retain-days and max-candidates must be positive")
    try:
        report = run(**vars(args))
    except (WatchError, OSError, KeyError, TypeError) as exc:
        print(f"Watch failed; previous published status is unchanged: {exc}", file=sys.stderr)
        return 1
    print(f"Successful arXiv scan at {report['last_checked_at']}: {report['candidate_count']} pending candidates, {report['new_candidate_count']} new, {report['updated_candidate_count']} updated. Human review required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
