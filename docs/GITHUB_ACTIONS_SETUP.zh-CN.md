# 每天自动追踪 arXiv：GitHub Actions 设置

本项目采用「每天检索并保存后台候选 → Codex 自动审核 → 维护者合并一个审核 PR → 发布」的流程。GitHub Actions 抓取时不创建 PR；维护者只需要处理包含审核结果和对应扫描数据的 Codex PR。

GitHub 仓库、Pages 和每日抓取已启用。抓取在云端运行，电脑关机也不受影响，使用 GitHub 自动提供的令牌。本地 Codex 审核要求电脑开机、应用运行并保有 GitHub 访问权限，无须另配付费模型 API；详见 [Codex 自动审核流程](CODEX_REVIEW.zh-CN.md)。下面保留首次设置、手动维护与排查说明。

## 1. 将整个文件夹推送到仓库

本地项目位于 `/Users/zhangyang/Projects/awesome-dexterous-manipulation`。先在 GitHub 创建一个空的公开仓库，推荐名为 `awesome-dexterous-manipulation`；暂时不要勾选初始化 README、.gitignore 或 License，因为本地已有项目文件。把这个文件夹的内容作为仓库根目录，确保 `index.html` 直接出现在仓库首页，而不是嵌套在另一个项目文件夹里。确认网页中的仓库文件列表能看到：

```text
.nojekyll
.github/workflows/dexterous-watch.yml
scripts/dexterous_watch.py
scripts/watch_report.py
scripts/publish_candidates.sh
scripts/test_dexterous_watch.py
scripts/test_watch_report.py
scripts/test_publish_candidates.py
index.html
papers.json
candidates.json
watch.json
```

注意 `.github` 是隐藏目录，上传时不能漏掉。工作流必须位于默认分支（通常为 `main`），只有放在其他分支不会触发每日执行。

如果使用终端，在这个项目文件夹中执行以下命令；将 `YOUR_REPOSITORY_URL` 换成刚创建的空仓库地址：

```sh
cd /Users/zhangyang/Projects/awesome-dexterous-manipulation
git init -b main
git add .
git commit -m "Initialize dexterous manipulation collection"
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

这些命令用于尚未初始化的新文件夹；已有 Git 仓库时直接提交并推送即可。

## 2. 允许 Actions 保存抓取结果

进入仓库 **Settings → Actions → General**：

1. 允许运行 GitHub Actions，并允许本工作流使用的官方 `actions/checkout`。
2. 确认组织策略与分支规则允许工作流写入 `bot/dexterous-watch`。如果设置 main 分支保护，只匹配 `main`，不要匹配 `bot/*` 或所有分支。

工作流文件只声明 `contents: write`，使用 GitHub 自动提供的 `GITHUB_TOKEN` 保存候选分支，不请求 PR 写入权限。通常无须创建 Secret，也无须把仓库的默认令牌权限全面改成读写。如果组织策略禁止分支写入，需要仓库/组织管理员调整对应规则。

本工作流不依赖 **Allow GitHub Actions to create and approve pull requests**。无需开启，也不要为了这次调整特意关闭已有设置，以免影响仓库中的其他流程。审核 PR 由本地 Codex 使用维护者已有的 GitHub 登录创建。[官方权限说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)

## 3. 手动验证一次

打开 **Actions → Dexterous paper watch → Run workflow**，选择默认分支，回看天数保留 **7**，运行。

成功后可以看到：

- Actions 的运行摘要：扫描时间、新增发现数、候选更新数，以及可点击的论文表格。
- `bot/dexterous-watch` 分支：新的 `candidates.json`、`watch.json`。
- 抓取阶段不会出现新的 PR。Codex 随后从成功抓取的候选分支读取数据，不要求它有对应的 PR。

首次运行是否成功应以 Actions 的实际结果为准。本地预览和网页上的上次扫描时间不能证明云端任务已经启用。

迁移自旧流程时，先将本次工作流修复合并到 main。确认队列已保存在 `bot/dexterous-watch` 后，可以关闭旧的 **Review dexterous paper discoveries** 候选 PR，无需合并；保留该分支，以免丢失待审积压。如果提前关闭旧 PR，务必在下次抓取前合并修复，否则 main 上的旧工作流仍会重新创建候选 PR。

## 4. 每天什么时候、怎么检索

已配置每天 **北京时间 09:35**，即 **UTC 01:35**：

```yaml
on:
  schedule:
    - cron: '35 1 * * *'
  workflow_dispatch:
```

这是现有工作流的触发部分示意，请保留文件中完整的 `workflow_dispatch.inputs` 和其他步骤。

机器人查询 arXiv API，按 **lastUpdatedDate 倒序**分页，默认回看最近 **7 天**：既发现新稿，也发现旧论文的新修订。关键词集中于 dexterous manipulation、in-hand manipulation、multi-finger 和触觉与灵巧手的组合，再用标题/摘要做初筛。主要逻辑在 `scripts/dexterous_watch.py` 中的 `SEARCH_QUERY` 和 `classify()`；调整检索范围时需同时检查这两处。

arXiv API 的索引/缓存可能晚于网站公告，因此这不是实时推送。七天重叠窗口用于补抓延迟结果和短暂失败；版本号会归一化、重复论文会去重。已正式收录和在人工永久名单中排除的论文不会重复进入候选队列；已收录论文的后续版本不会单独生成更新提醒。Codex 的 reject 结论保存在独立审核账本中，不等于人工永久排除。分页间隔至少 3 秒，网络错误最多尝试 3 次，扫描不完整时任务失败并保留上次成功报告。[arXiv API 文档](https://info.arxiv.org/help/api/user-manual.html)

GitHub 定时任务可能延迟，高负载时甚至被丢弃；公共仓库连续 60 天没有活动也可能被自动停用。如果中断超过一周，可在 **Run workflow** 中选择 **14** 或 **30** 天补查，然后恢复日常 7 天窗口。超过 30 天可在本地使用 `--days` 参数补查，仍受分页上限保护。[GitHub 定时触发说明](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## 5. 一个审核 PR 完成确认与发布

每天北京时间 **10:05**，本地 Codex 固定 `bot/dexterous-watch` 上一次成功抓取的提交 SHA，从同一提交读取 `candidates.json` 和 `watch.json`，核查论文原始来源，再记录 accept、defer 或 reject。抓取工作流不会改动正式目录 `papers.json`。

有新审核结论或需要维护者决策的实质变化时，Codex 创建或更新 `bot/codex-paper-review` 的唯一待合并 PR，包含：

- 通过收录的论文条目 `papers.json` 与审核账本 `reviews.json`。
- 对应成功扫描的 `candidates.json` 和 `watch.json`。
- 与正式目录一致的 README 统计和近期论文。

审核 PR 尚未合并时，下一批结论继续追加到这个 PR；合并后，下轮从最新 main 开始。维护者只需检查并合并审核 PR，Pages 就会发布。后台抓取分支无需人工合并，也不要删除：保留两个分支可以避免 Actions 重建队列时覆盖未合并的审核结果。

只有候选或扫描时间改变、没有新审核结论或需要维护者处理的变化时，不新建或更新仅含扫描结果的 PR。最新抓取状态可在 Actions 和候选分支查看；网站显示的是最近一次随审核 PR 发布的扫描记录。

### 人工补充或修正论文

也可以在独立的人工编辑分支补充遗漏论文或修正条目。先读原文/官方项目页，核实是否真的使用多指手、触觉是否是策略运行时输入，再修改 `papers.json`。可以复制一条现有论文作为模板：

- `id` 唯一；`date` / `year` 使用首次 arXiv 投稿日期。
- `category` 保留`catalog-core.js` 中现有六个研究方向之一；`tags` 使用 `catalog-core.js` 中的五组受控标签，参考文献导读的口径。
- 填写 `sensing`、`hand`、`task`、`method`，以及人工撰写的 `tldr`。
- `links.paper` 和 `source_url` 使用验证过的论文地址；代码/项目地址没有确认就省略。
- `scope` 区分核心灵巧操作 `core` 和触觉感知、手物交互等相邻研究 `adjacent`。

运行 `node scripts/build_readme.cjs` 同步 README，并通过 [维护指南](MAINTENANCE.md) 中的检查。合并人工修改后，下一轮检索会自动从后台待审队列排除已收录论文；也可以手动运行抓取工作流，无须另外合并清理队列的 PR。

### 人工永久排除与模型结论

Codex 的 reject 只写入 `reviews.json`，用于记录当前版本的来源与理由，不会自动写入永久排除名单。若维护者确定某篇论文以后也不应进入候选队列，可通过人工 PR 在根目录新增或更新 `rejected_ids.json`：

```json
{
  "rejected_ids": ["2610.00001", "2610.00002"]
}
```

上面是格式示例，请替换成实际拒绝的 ID。保留已有 ID，追加新 ID；无须版本号。只从 `candidates.json` 删除一篇论文不算永久拒绝，它下次仍可能被发现。若要重新考虑已拒绝论文，须同时移除 `rejected_ids.json`、默认分支和机器人分支 `candidates.json` 中保存的拒绝记录，再重新检索。

不要在 `bot/dexterous-watch` 上保存人工补写的摘要或正式目录修改：机器人会重建这个生成数据专用分支。待审历史按 arXiv 最后更新日期保留 180 天，最多 500 篇。检索是发现辅助，仍可能漏掉关键词不匹配的论文或包含不相关结果；触觉基础工作也可以人工补充。

## 6. 发布网页与连接个人主页

在 **Settings → Pages → Build and deployment** 设置：

| 设置项 | 选择 |
| --- | --- |
| Source | Deploy from a branch |
| Branch | main（或实际默认分支） |
| Folder | /(root) |

点击 **Save**。根目录已包含空文件 `.nojekyll`，让 Pages 直接发布现有静态文件。网站入口为 `index.html`，从同目录读取论文与候选数据，无须 npm 构建或另配服务器。

在 **Actions** 中等待 Pages 发布任务成功，再回到 **Settings → Pages** 打开 **Visit site**。以 `breez3young/awesome-dexterous-manipulation` 为例，默认网站地址是 `https://breez3young.github.io/awesome-dexterous-manipulation/`。实际地址以 Pages 显示为准；当前已发布的实际地址为 `https://breez3young.github.io/Awesome-Dexterous-Manipulation/`。以后人工推送或合并修改到发布分支，Pages 会更新网站。

参考：[GitHub Pages 发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)、[静态网站入口与 .nojekyll](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)。

发布后通常是 `https://你的用户名.github.io/仓库名/`。个人主页的项目卡片链接到这个地址即可。检索工作流只更新后台候选分支，Codex 才生成审核 PR，Pages 发布已合并到 main 的数据。尚未合并的审核结果和后台候选更新不会改变线上网站。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| Actions 找不到工作流或没有 Run workflow | 确认完整的 `.github/workflows/dexterous-watch.yml` 已提交到默认分支，并启用 Actions。 |
| 抓取结果无法保存到分支 | 检查 `contents: write` 是否被组织策略限制，以及保护规则是否误覆盖 `bot/dexterous-watch`；修正后重跑。 |
| arXiv 超时 / 503 / 分页不完整 | 查看失败步骤，稍后手动重跑；不用改动上次成功报告。 |
| 抓取成功但没有 PR | 抓取阶段不创建 PR。确认本地 Codex 能运行；只有新的审核结论或需要维护者处理的变化才会创建/更新审核 PR。 |
| Codex 无法创建或更新审核 PR | 检查本地 GitHub 登录和仓库访问权限，以及审核分支是否存在冲突；不是 Actions 创建 PR 开关的问题。 |
| 网页上扫描时间没有更新 | 页面展示最近一次随审核 PR 合并并成功部署的扫描记录。仅有新扫描时不单独发布；查看 Actions 获取最新抓取状态。 |
| 旧候选 PR 一直显示 | 先将工作流修复合并 main，确认队列仍在后台分支后关闭旧候选 PR，保留分支；日后只合并 Codex 审核 PR。 |
| 每天没有新论文 | 可因无相关更新、API 延迟、重复/拒绝过滤而正常出现；先看成功运行摘要，再决定是否扩充关键词。 |

本地验证命令：

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/dexterous_watch.py --days 7
python3 scripts/watch_report.py watch.json
```
