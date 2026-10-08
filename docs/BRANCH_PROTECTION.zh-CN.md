# main 分支保护：兼容现有自动化的设置

GitHub 的 “Your main branch isn't protected” 是建议提示，不是抓取或部署失败。不设置保护也不会停止自动化。本项目适合只保护 `main`，保留“自动抓取 → Codex 审核 PR → 维护者合并 → Pages 发布”的流程。

本说明是建议配置，没有自动修改远程设置。

## 创建规则集

进入仓库 **Settings → Rules → Rulesets → New ruleset → New branch ruleset**。如果界面将 Rulesets 直接列在侧栏，点击该项即可。

| 设置项 | 值 |
| --- | --- |
| Ruleset name | Protect main |
| Enforcement status | Active |
| Target branches | 仅 `main`（按名称匹配），不要选择 All branches |
| Bypass list | 留空 |
| Restrict deletions | 开启 |
| Block force pushes | 开启 |
| Require a pull request before merging | 开启 |
| Required approvals | **0** |

其余规则暂时保持关闭，尤其是 Require status checks、Require deployments、Require signed commits、Require linear history、Restrict creations / updates，以及需要其他人批准最近一次推送的选项。保存后核对目标分支确实只有 `main`。

Required approvals 为 0 仍要求通过 PR 合并，不会自动合并。当前 Codex 使用维护者的 GitHub 登录创建 PR，PR 作者不能批准自己的 PR；设置 1 次批准会要求另一位协作者，和现在由你确认合并的单人维护方式不匹配。

## 为什么不会拦住已检查的流程

- 抓取工作流只写入 `bot/dexterous-watch`，不创建 PR，也无需合并该分支。更新时会重建该分支并使用 `--force-with-lease`，因此保护规则不能覆盖 `bot/*` 或所有分支。
- Codex 从成功抓取的固定提交读取候选，写入 `bot/codex-paper-review` 并创建/更新唯一的审核 PR；仅保护 main 不限制审核分支更新。
- 维护者合并 PR 后，Pages 从 main 发布；不必更改 Pages 来源、现有计划时间或 Actions 令牌权限。
- 当前没有每个 PR 都会运行的独立检查工作流。不要把定时抓取或合并后的 Pages 发布设为合并前必须成功的检查，以免一直等待未产生的检查结果。

抓取工作流只需要 `contents: write`，不依赖 Allow GitHub Actions to create and approve pull requests。无需为此关闭仓库里的该设置，以免影响其他工作流；Codex 使用维护者已有的 GitHub 登录创建审核 PR。

未来如果增加 PR 检查，先确认它在 Codex 审核 PR 和人工提交的 PR 上都能正常运行，再考虑将其设为必需检查。这份规则只作用于本仓库 main；它不修改其他仓库或 Codex 定时任务。

参考：[规则集创建](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)、[可用规则及 PR 要求](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)、[必需检查的阻塞原因](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)。
