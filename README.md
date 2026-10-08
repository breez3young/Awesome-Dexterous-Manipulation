<!-- Catalog update: 2026-10-08 -->
# Awesome Dexterous & Tactile Manipulation

A standalone research collection on dexterous and tactile manipulation, maintained by [Yang Zhang](https://breez3young.github.io/).

## 每日自动追踪 arXiv

已准备 GitHub Actions 每天北京时间 **09:35** 检索、生成候选审核 PR，人工确认后加入正式目录。配置尚未在云端启用。

先看 [中文设置与审核指南](docs/GITHUB_ACTIONS_SETUP.zh-CN.md)：包含仓库上传、权限、手动验证、7/14/30 天补查、收录/拒绝和 Pages 发布步骤。

## Local preview

From this folder, run `python3 -m http.server 5174 --bind 127.0.0.1`, then open [the local collection](http://127.0.0.1:5174/). No frontend build or npm installation is needed. Serve the page over HTTP rather than opening `index.html` with `file://`.

## Folder layout

```text
index.html, style.css, app.js   Standalone interface
papers.json                   Curated paper data
candidates.json, watch.json   Discovery queue and last search report
scripts/                      Watcher, readable PR report, and tests
docs/                         Chinese GitHub Actions setup and review guide
.github/workflows/            Daily review-PR workflow
integration/homepage-card.css Optional style for a future homepage link
```

Run offline checks with `python3 -m unittest discover -s scripts -p "test_*.py" -v`. Run a manual discovery scan with `python3 scripts/dexterous_watch.py`. If the local macOS Python certificate store is unavailable, use `SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/dexterous_watch.py`; certificate verification remains enabled.

## Scope

- **Dexterous Manipulation:** multi-fingered grasping, in-hand control, hand–arm systems, teleoperation, and learning.
- **Tactile Dexterous Manipulation:** tactile feedback contributes to multi-fingered manipulation, or a dexterous hand integrates substantial tactile sensing.
- **Tactile Sensing & Representation:** tactile sensors, simulation, and representations with potential relevance to dexterity.
- **Hand–Object Interaction:** human hand motion, hand–object perception, and interaction modeling; currently HandX and DexYCB.
- **Grasp Synthesis:** grasp generation, scoring, and selection; currently Dex-Net 4.0 with parallel-jaw and suction grippers.
- **Policy Optimization:** general policy-training objectives and optimization algorithms evaluated on manipulation; currently Coupled Policy Optimization.

The current collection contains 58 papers: 44 unique works from the supplied bibliography, two requested additions, and 12 complementary seed works. It is not an exhaustive survey or a claim of coverage through October 2026. Dates refer to the first arXiv submission, or journal publication for non-arXiv work. TL;DRs are curator-written paraphrases; metadata and links are grounded in the linked primary sources. Code links may point to a released component or hardware design, as labeled.

## Adding and reviewing papers

Edit `papers.json` in this collection repository. Keep each paper's `id` unique. Required fields: `title`, `year`, `date`, `category`, `tldr`, `tags`, `sensing`, `hand`, `task`, `method`, `links.paper`, `scope`, and `source_url`. Add only verified project/code links. Omit citation and star counts unless there is a working refresh process.

Review each candidate against the original paper or official project:

1. Does the work involve a multi-fingered hand, or belong in related methods, datasets, or sensing resources?
2. Is touch an actual observation used by the deployed policy, a training-only signal, or merely a contact reward? Proprioception alone is not tactile sensing.
3. What is the research question and main insight? Write that in the TL;DR, instead of a headline performance number.
4. Which sensors, hand, tasks, and methods are supported by the paper?
5. Is the entry a new work or an updated version of an existing arXiv record?

## Daily watch: verified manually, scheduling not activated

The implementation lives in `scripts/dexterous_watch.py` and `.github/workflows/dexterous-watch.yml`. It queries the public arXiv API over a rolling seven-day window and produces **unreviewed candidates**, never edits `papers.json`, and never merges a pull request. A keyword search can miss papers and can include irrelevant ones; it is a discovery aid, not a literature review.

A live API scan completed on 2026-10-08 and produced 33 unreviewed candidates. That scan did not change the curated collection; the later bibliography import expanded it to 58 papers. Recurring execution on GitHub has not been enabled.

The configured cadence is daily at **09:35 Asia/Shanghai / 01:35 UTC**. arXiv's API indexing and cache can lag announcements, so the rolling window catches delayed results on subsequent runs. A scheduled GitHub Actions run may be delayed. The interface shows a recorded successful search; it does not present a countdown as evidence of a completed update.

### Enable after reviewing the local version

1. Create the intended GitHub repository, add this folder as its source, and commit the implementation to its **default branch**. No remote repository has been created or connected yet.
2. In GitHub **Settings → Actions → General**, allow Actions to create pull requests, subject to the repository's policy. The workflow uses the built-in `GITHUB_TOKEN`; no paid model API or manually created personal access token is required.
3. In **Actions → Dexterous paper watch**, use **Run workflow** once and inspect the readable run summary and candidate PR before relying on the schedule. The manual run accepts 7, 14, or 30 lookback days to recover from interruptions; scheduled runs use 7 days.
4. Review the candidate records. Promote accepted papers into `papers.json` with verified categories and a human-reviewed TL;DR. The queue retains up to 500 candidates for 180 days. Record rejected arXiv IDs in `rejected_ids.json` using `{"rejected_ids": ["YYMM.NNNNN"]}`. Make curated edits on a separate source branch; the bot branch is reserved for generated queue files. Merging the candidate queue alone does not add papers to the catalog.
5. Enable GitHub Pages for this collection repository, using the default branch and repository root as the publishing source. Its project website will use the repository name as the URL prefix. The homepage can link to that published URL. The watch workflow does not configure Pages; Pages must be enabled separately. Once configured, merged source changes are published by the Pages deployment process.

Public repositories may have scheduled workflows disabled after 60 days without activity. Check GitHub's [schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) and the Actions run history when diagnosing missed runs. Nothing in this local preview proves that the workflow has been activated on GitHub.

## How the reference site works

The layout and browsing approach were inspired by [Awesome Loop Models](https://huskydoge.github.io/Awesome-Loop-Models/index.html). This initial implementation recreates the core collection experience; it does not claim feature parity with the original site's metrics, briefings, reading desk, or analytics.

- The original repository's [September 3 implementation plan, Task 5](https://github.com/huskydoge/Awesome-Loop-Models/blob/main/docs/plans/2026-09-03-catalog-refresh-automation.md) identifies a local Codex automation, `hermes-daily-awesome-loop-models-watch`, for new papers and rotating metadata audits. The [design document](https://github.com/huskydoge/Awesome-Loop-Models/blob/main/docs/plans/2026-09-03-catalog-refresh-automation-design.md) routes changes through review PRs.
- Its current [countdown configuration](https://github.com/huskydoge/Awesome-Loop-Models/blob/main/assets/daily-watch-countdown.js) uses Sunday–Thursday at 20:15 America/New_York: Monday–Friday 08:15 Beijing in summer, 09:15 in winter. The private automation's current enabled state, model, and complete prompt cannot be confirmed from public code.
- A separate [metrics workflow](https://github.com/huskydoge/Awesome-Loop-Models/blob/main/.github/workflows/update-metrics.yml) refreshes citations, stars, and publication metadata at 05:17 UTC (13:17 Beijing), plus push/manual triggers. That workflow uses a `SEMANTIC_SCHOLAR_API_KEY` repository secret and GitHub's built-in token.
- The reference repository is [MIT licensed](https://github.com/huskydoge/Awesome-Loop-Models/blob/main/LICENSE), copyright 2026 Benhao Huang. Retain its license and copyright if copying its source. This page's implementation is newly written, with visible attribution for the reference design.

Our lightweight alternative runs candidate discovery on GitHub Actions, so it does not require this computer to be awake or a local Codex automation to be running. Editorial judgment stays with the curator.

## Reading desk, tags, and Stats

The reading desk shares the homepage's ivory / forest-green / clay palette. Papers have English and Chinese summaries. **Stats** shows first-release activity, category mix, policy families, data-transfer approaches, and manipulation skills for the current selection. Click charts to open matching papers; copy the URL to preserve filters and `#stats`.

The five controlled tag groups live in `catalog-core.js`. Topic tags combine with AND, research areas with OR. `Tactile feedback` requires runtime tactile observations; contact constraints or a tactile-free student trained by a contact-aware teacher do not qualify. Six primary areas distinguish core dexterity, tactile dexterity, tactile sensing and representation, hand–object interaction, grasp synthesis, and policy optimization. Choose the primary area by the paper’s main contribution. Robot-hand control systems stay in the dexterity areas; human-interaction resources, gripper grasp generation, and general optimization methods use the three more specific supporting areas. Dataset / benchmark remains a resource tag across areas, not a catch-all research area. Existing links to the former broad area select all three replacement areas. Unknown metadata stays unfilled.

See [中文文献导读与逐篇总结](docs/LITERATURE_MAP.zh-CN.md). Imported records keep `bib_keys`, `summary_basis`, and `sources`; original attachment paths were not copied into the website.

Check catalog/filter/statistics logic with `node --test scripts/test_catalog_core.cjs`. Existing watcher checks remain `python3 -m unittest discover -s scripts -p 'test_*.py' -v`.

“Foundation policy” is reserved for broadly pretrained control policies; it does not mean general background resources. Research areas use descriptive topic names to avoid confusion with foundation models.
