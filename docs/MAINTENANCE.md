# Maintaining the collection

The website reads `papers.json` directly. `README.md` introduces the collection and includes a small generated overview; it is not a second paper database.

## Local preview

From the repository root, run `python3 -m http.server 5174 --bind 127.0.0.1`, then open [the local site](http://127.0.0.1:5174/). There is no frontend build or npm dependency installation.

## Keep the README current

After editing or promoting papers, run:

```sh
node scripts/build_readme.cjs
node scripts/build_readme.cjs --check
```

This updates only the section between the generated-catalog markers: counts, research-area distribution, reading-route links, and recent papers. The remaining introduction, contribution instructions, and links stay editable by hand. The recent-papers table uses first publication dates; it must not present them as repository addition dates. Counts describe the catalog in the same branch, so a review PR can show a higher count than the website until that PR is merged.

The cover in `assets/cover.svg` is an original vector illustration. Inspiration for the README layout and browsing experience comes from [Awesome Loop Models](https://github.com/huskydoge/Awesome-Loop-Models); no license, citation ranking, or unimplemented feature is inferred from that reference.

## Data and checks

Required catalog fields include unique `id`, `title`, `year`, `date`, `category`, `tldr`, `tags`, `sensing`, `hand`, `task`, `method`, `links.paper`, `scope`, and `source_url`. New reviewed entries also include Chinese summaries and source evidence. Use the taxonomy exported from `catalog-core.js`; do not introduce a new category through a single paper record.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
node --test scripts/test_catalog_core.cjs
node scripts/build_readme.cjs --check
```

| File or folder | Purpose |
|:--|:--|
| `index.html`, `style.css`, `landscape.css`, `app.js` | Website interface |
| `catalog-core.js` | Taxonomy, filtering, statistics, and URL state |
| `papers.json` | Curated papers |
| `candidates.json`, `watch.json` | Discovered candidates and last successful search |
| `reviews.json` | Codex decisions and evidence |
| `scripts/` | Discovery, validation, reports, and README generation |
| `.github/workflows/` | Daily GitHub discovery workflow |

## Discovery, review, and publication

- [GitHub Actions and Pages setup](GITHUB_ACTIONS_SETUP.zh-CN.md)
- [Codex review protocol](CODEX_REVIEW.zh-CN.md)
- [Literature guide and scope](LITERATURE_MAP.zh-CN.md)
- [Main-branch protection settings](BRANCH_PROTECTION.zh-CN.md)

GitHub discovery saves candidates and successful scan records to `bot/dexterous-watch` without opening a PR. Codex review is a separate local task and requires the computer and app to be running. It reads a fixed successful commit from that branch and creates or updates one pending PR on `bot/codex-paper-review`, including the reviewed papers, decision ledger, README, and corresponding scan data. The maintainer merges that PR and Pages publishes its contents.

Keep the discovery branch: it preserves the candidate backlog and needs no manual merge. Separate branches prevent the next discovery run from overwriting pending review work. After a review PR is merged, the next batch starts from the latest `main`; while it is open, new decisions join the same PR. Candidate or scan-time changes alone do not create a PR. The website therefore shows the last published scan, while Actions and the discovery branch show the latest successful scan.

The discovery workflow needs only `contents: write`. It does not depend on the repository setting that allows Actions to create or approve pull requests; leave that setting unchanged if other workflows use it.
