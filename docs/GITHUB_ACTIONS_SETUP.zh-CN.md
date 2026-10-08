# 每天自动追踪 arXiv：GitHub Actions 设置

本项目采用「每天检索 → 生成候选 PR → 人工审核 → 收录并发布」的流程。电脑关机也能运行，无须 Codex 定时任务、付费模型 API 或个人访问令牌。

目前文件已准备好，但尚未连接 GitHub 仓库，云端定时执行也尚未启用。正式目录已整理为 58 篇。原始候选记录来自此前手动检索；页面会排除后来已经正式收录的论文，原扫描时间保持不变。

## 1. 将整个文件夹推送到仓库

本地项目位于 `/Users/zhangyang/Projects/awesome-dexterous-manipulation`。先在 GitHub 创建一个空的公开仓库，推荐名为 `awesome-dexterous-manipulation`；暂时不要勾选初始化 README、.gitignore 或 License，因为本地已有项目文件。把这个文件夹的内容作为仓库根目录，确保 `index.html` 直接出现在仓库首页，而不是嵌套在另一个项目文件夹里。确认网页中的仓库文件列表能看到：

```text
.nojekyll
.github/workflows/dexterous-watch.yml
scripts/dexterous_watch.py
scripts/watch_report.py
scripts/test_dexterous_watch.py
scripts/test_watch_report.py
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

## 2. 允许 Actions 创建审核 PR

进入仓库 **Settings → Actions → General**：

1. 允许运行 GitHub Actions，并允许本工作流使用的官方 `actions/checkout`。
2. 在 **Workflow permissions** 下勾选 **Allow GitHub Actions to create and approve pull requests**，然后保存。这个设置同时涵盖创建和批准的能力；我们的工作流只创建 PR，不会批准或合并。

工作流文件已经声明 `contents: write` 和 `pull-requests: write`，使用 GitHub 自动提供的 `GITHUB_TOKEN`。通常无须创建 Secret，也无须把仓库的默认令牌权限全面改成读写。如果组织策略禁止这两项能力，需要仓库/组织管理员调整对应规则。[官方权限说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#preventing-github-actions-from-creating-or-approving-pull-requests)

## 3. 手动验证一次

打开 **Actions → Dexterous paper watch → Run workflow**，选择默认分支，回看天数保留 **7**，运行。

成功后可以看到：

- Actions 的运行摘要：扫描时间、新增发现数、候选更新数，以及可点击的论文表格。
- `bot/dexterous-watch` 分支：新的 `candidates.json`、`watch.json`。
- **Review dexterous paper discoveries** PR：供审核的论文清单。之后每天更新同一个 PR，而不是一天创建一个。

首次运行是否成功应以 Actions 的实际结果为准。本地预览和网页上的上次扫描时间不能证明云端任务已经启用。

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

arXiv API 的索引/缓存可能晚于网站公告，因此这不是实时推送。七天重叠窗口用于补抓延迟结果和短暂失败；版本号会归一化、重复论文会去重。已正式收录和已拒绝的论文不会重复进入候选队列；已收录论文的后续版本不会单独生成更新提醒。分页间隔至少 3 秒，网络错误最多尝试 3 次，扫描不完整时任务失败并保留上次成功报告。[arXiv API 文档](https://info.arxiv.org/help/api/user-manual.html)

GitHub 定时任务可能延迟，高负载时甚至被丢弃；公共仓库连续 60 天没有活动也可能被自动停用。如果中断超过一周，可在 **Run workflow** 中选择 **14** 或 **30** 天补查，然后恢复日常 7 天窗口。超过 30 天可在本地使用 `--days` 参数补查，仍受分页上限保护。[GitHub 定时触发说明](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## 5. 审核、收录和拒绝

**合并候选 PR，只保存待审队列和检索记录，不表示论文已通过审核。** 网站正式目录读取 `papers.json`，机器人不会改这个文件。

对准备收录的论文，先读原文/官方项目页，核实是否真的使用多指手、触觉是否是策略运行时输入，再在独立的人工编辑分支中修改 `papers.json`。可以复制一条现有论文作为模板：

- `id` 唯一；`date` / `year` 使用首次 arXiv 投稿日期。
- `category` 保留`catalog-core.js` 中现有六个研究方向之一；`tags` 使用 `catalog-core.js` 中的五组受控标签，参考文献导读的口径。
- 填写 `sensing`、`hand`、`task`、`method`，以及人工撰写的 `tldr`。
- `links.paper` 和 `source_url` 使用验证过的论文地址；代码/项目地址没有确认就省略。
- `scope` 区分核心灵巧操作 `core` 和触觉感知、手物交互等相邻研究 `adjacent`。

审核并合并这次人工修改后，下一轮检索会自动从待审队列排除该论文。也可以立即手动运行工作流，再合并清理后的候选 PR。

对明确不收录的论文，在默认分支新增或更新根目录 `rejected_ids.json`：

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

在 **Actions** 中等待 Pages 发布任务成功，再回到 **Settings → Pages** 打开 **Visit site**。以 `breez3young/awesome-dexterous-manipulation` 为例，默认网站地址是 `https://breez3young.github.io/awesome-dexterous-manipulation/`。实际地址以 Pages 显示为准；这只是发布后的预期地址，目前尚未上线。以后人工推送或合并修改到发布分支，Pages 会更新网站。

参考：[GitHub Pages 发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)、[静态网站入口与 .nojekyll](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)。

发布后通常是 `https://你的用户名.github.io/仓库名/`。个人主页的项目卡片链接到这个地址即可。检索工作流和 Pages 是两件事：前者生成审核 PR，后者发布已合并的数据。尚未合并的候选 PR 不会改变线上网站。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| Actions 找不到工作流或没有 Run workflow | 确认完整的 `.github/workflows/dexterous-watch.yml` 已提交到默认分支，并启用 Actions。 |
| 创建 PR 报权限错误 | 开启允许 Actions 创建 PR 的选项；检查组织权限或限制机器人分支推送的规则。机器人分支可能已经保存，可修正权限后重跑。 |
| arXiv 超时 / 503 / 分页不完整 | 查看失败步骤，稍后手动重跑；不用改动上次成功报告。 |
| PR 创建了，但其他检查没启动 | 内置 GITHUB_TOKEN 发起的事件可能不触发其他工作流；需要时手动运行这些检查。 |
| 网页上扫描时间没有更新 | 检查候选 PR 是否已合并、Pages 是否部署成功；页面只展示已发布的记录。 |
| 每天没有新论文 | 可因无相关更新、API 延迟、重复/拒绝过滤而正常出现；先看成功运行摘要，再决定是否扩充关键词。 |

本地验证命令：

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/dexterous_watch.py --days 7
python3 scripts/watch_report.py watch.json
```
