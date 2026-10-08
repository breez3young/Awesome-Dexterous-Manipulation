#!/usr/bin/env python3
"""Render a successful discovery scan as the Actions job summary."""

import argparse
import html
import re
import sys
from pathlib import Path

from dexterous_watch import WatchError, normalize_id, parse_date, read_json


def markdown_text(value: object) -> str:
    text = html.escape(" ".join(str(value).split())).replace("@", "&#64;")
    return re.sub(r"([\\`*_{}\[\]()#+.!|])", r"\\\1", text)


def render(report: dict, limit: int = 30) -> str:
    if report.get("status") != "ok" or not isinstance(report.get("items"), list):
        raise WatchError("Only a successful scan can produce a review report")
    checked = parse_date(report["last_checked_at"]).isoformat()
    lines = [
        "## arXiv 每日发现 · 等待 Codex 审核", "",
        f"检索完成：{checked}（UTC）；回看 {int(report['lookback_days'])} 天。",
        f"待审 **{int(report['candidate_count'])}** 篇，本次新增发现 **{int(report['new_candidate_count'])}** 篇，已有候选更新 **{int(report['updated_candidate_count'])}** 篇。", "",
        "新增发现指首次进入候选队列，也可能是旧论文的新修订。检索词命中尚未核实，不等于正式收录。", "",
        "| 论文 | 初稿日期 | 最新修订 | 初筛标签 |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["items"][:limit]:
        paper_id = normalize_id(item.get("id"))
        if not paper_id:
            raise WatchError("Cannot link a candidate with an invalid arXiv ID")
        title = markdown_text(item["title"])
        published = parse_date(item["published"]).date().isoformat()
        updated = parse_date(item["updated"]).date().isoformat()
        tags = markdown_text(", ".join(item.get("matched_topics", [])))
        lines.append(f"| [{title}](https://arxiv.org/abs/{paper_id}) | {published} | {updated} | {tags} |")
    if not report["items"]:
        lines.extend(["", "当前没有待审候选。"])
    elif len(report["items"]) > limit:
        lines.extend(["", f"这里显示最新 {limit} 篇；完整队列见 `bot/dexterous-watch` 分支的 `candidates.json`。"])
    lines.extend([
        "", "### 审核与收录", "",
        "1. 本次抓取只保存后台候选队列，不创建 PR，也不修改正式论文目录。",
        "2. Codex 从候选分支读取成功扫描，核对原始来源、分类和触觉部署证据，记录通过、暂缓或排除理由。",
        "3. Codex 将已审核条目、审核账本及对应扫描记录放入唯一的 `bot/codex-paper-review` PR。",
        "4. 维护者只需确认并合并该审核 PR，随后 GitHub Pages 发布。无新结论时不创建仅含抓取记录的 PR。", "",
        "机器人每天更新同一个 `bot/dexterous-watch` 分支；此分支无需合并，请勿在其中保存人工编辑。已收录和人工永久排除的论文会被过滤；候选最多保留 180 天、500 篇。",
        "Codex 的 reject / defer 保存在 reviews.json，用来源版本去重；不自动写入永久排除名单。详见 `docs/CODEX_REVIEW.zh-CN.md`。",
        "网页使用最近一次审核 PR 合并并发布的检索结果。失败或不完整的 API 检索不会覆盖上次成功报告。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        print(render(read_json(args.report)), end="")
    except (WatchError, KeyError, TypeError, ValueError) as exc:
        print(f"Cannot render watch report: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
