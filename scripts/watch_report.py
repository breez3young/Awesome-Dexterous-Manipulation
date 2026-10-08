#!/usr/bin/env python3
"""Render a successful scan as the review PR body and Actions job summary."""

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
        "## arXiv 每日发现 · 等待人工审核", "",
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
        lines.extend(["", f"这里显示最新 {limit} 篇；完整队列见本分支的 `candidates.json`。"])
    lines.extend([
        "", "### 审核与收录", "",
        "1. 阅读原论文或官方项目页，确认与多指灵巧操作、触觉控制的关系。",
        "2. 在独立的人工编辑分支将确认收录的论文加入 `papers.json`，补全标签、TL;DR 和验证后的链接。",
        "3. 不收录的论文，将其无版本号 arXiv ID 写入默认分支的 `rejected_ids.json`。格式和操作步骤见 `docs/GITHUB_ACTIONS_SETUP.zh-CN.md`。",
        "4. 合并本 PR 只保存检索报告和待审队列，不会将候选自动加入正式目录。", "",
        "机器人每天更新同一个 `bot/dexterous-watch` 分支，请勿在该分支保存人工编辑。已收录和已拒绝论文会被排除；候选最多保留 180 天、500 篇。",
        "工作流不会自动合并；网页使用最近一次已合并并发布的检索结果。失败或不完整的 API 检索不会覆盖上次成功报告。",
        "使用内置 GITHUB_TOKEN 创建的 PR 可能不会触发其他检查；如仓库要求这些检查，请手动运行。",
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
