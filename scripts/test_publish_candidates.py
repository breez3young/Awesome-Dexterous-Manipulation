"""Exercise candidate publishing against disposable, local-only Git remotes."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


PUBLISH_SCRIPT = Path(__file__).with_name("publish_candidates.sh").resolve()
GIT = shutil.which("git")
BASH = shutil.which("bash")
BOT_BRANCH = "bot/dexterous-watch"


@unittest.skipUnless(GIT and BASH, "Git and Bash are required")
class PublishCandidatesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="candidate-publish-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.origin = self.root / "origin.git"
        self.seed = self.root / "seed"
        self.empty_hooks = self.root / "empty-hooks"
        self.empty_hooks.mkdir()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.gh_called = self.root / "gh-called"
        gh = self.bin_dir / "gh"
        gh.write_text(
            '#!/bin/sh\nprintf "called\\n" >> "$GH_CALL_SENTINEL"\nexit 97\n',
            encoding="utf-8",
        )
        gh.chmod(0o755)

        # Ignore user/system Git configuration and inherited repository context.
        # Even accidental remote URLs cannot use a network transport in this suite.
        self.env = {
            key: value for key, value in os.environ.items()
            if not key.startswith("GIT_")
            and key not in {"BOT_BRANCH", "DATA_DIR", "PREVIOUS_BOT_SHA"}
        }
        self.env.update({
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_ALLOW_PROTOCOL": "file",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_COUNT": "4",
            "GIT_CONFIG_KEY_0": "user.name",
            "GIT_CONFIG_VALUE_0": "Offline Test",
            "GIT_CONFIG_KEY_1": "user.email",
            "GIT_CONFIG_VALUE_1": "offline-test@example.invalid",
            "GIT_CONFIG_KEY_2": "core.hooksPath",
            "GIT_CONFIG_VALUE_2": str(self.empty_hooks),
            "GIT_CONFIG_KEY_3": "commit.gpgsign",
            "GIT_CONFIG_VALUE_3": "false",
            "LC_ALL": "C",
            "PATH": str(self.bin_dir) + os.pathsep + self.env.get("PATH", ""),
            "GH_CALL_SENTINEL": str(self.gh_called),
        })
        self.git("init", "--bare", str(self.origin))
        self.git("init", "--initial-branch=main", str(self.seed))
        self.write_report(self.seed, "baseline")
        (self.seed / "papers.json").write_text('{"papers": []}\n', encoding="utf-8")
        (self.seed / "README.md").write_text("Original catalog\n", encoding="utf-8")
        self.git("add", ".", cwd=self.seed)
        self.git("commit", "-m", "Initial main", cwd=self.seed)
        self.git("remote", "add", "origin", str(self.origin), cwd=self.seed)
        self.git("push", "origin", "main", cwd=self.seed)
        self.main_sha = self.remote_sha("main")
        self.work = self.clone("work")

    def tearDown(self):
        self.assertFalse(self.gh_called.exists(), "Publisher must never invoke gh")

    def run_command(self, args, *, cwd=None, env=None, check=True):
        result = subprocess.run(
            args,
            cwd=cwd or self.root,
            env=env or self.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
        if check and result.returncode:
            self.fail(
                f"Command failed ({result.returncode}): {args!r}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
        return result

    def git(self, *args, cwd=None, check=True):
        return self.run_command([GIT, *args], cwd=cwd, check=check)

    def clone(self, name, branch="main"):
        path = self.root / name
        self.git("clone", "--branch", branch, str(self.origin), str(path))
        return path

    def remote_sha(self, branch):
        return self.git(
            "--git-dir", str(self.origin), "rev-parse", f"refs/heads/{branch}",
        ).stdout.strip()

    def remote_file(self, branch, path):
        return self.git(
            "--git-dir", str(self.origin), "show", f"refs/heads/{branch}:{path}",
        ).stdout

    @staticmethod
    def write_report(repo, label):
        for filename, value in (
            ("candidates.json", {"candidates": [{"id": label}]}),
            ("watch.json", {"scan": label}),
        ):
            (repo / filename).write_text(json.dumps(value) + "\n", encoding="utf-8")

    def publish(self, repo, previous_sha="", *, branch=None, missing_sha=False):
        env = self.env.copy()
        if not missing_sha:
            env["PREVIOUS_BOT_SHA"] = previous_sha
        if branch is not None:
            env["BOT_BRANCH"] = branch
        return self.run_command([BASH, str(PUBLISH_SCRIPT)], cwd=repo, env=env, check=False)

    def publish_first_report(self):
        self.write_report(self.work, "scan-1")
        result = self.publish(self.work)
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.remote_sha(BOT_BRANCH)

    def test_first_publish_commits_only_report_even_with_staged_papers(self):
        self.write_report(self.work, "scan-1")
        (self.work / "papers.json").write_text('{"papers": ["unreviewed"]}\n', encoding="utf-8")
        self.git("add", "papers.json", cwd=self.work)

        result = self.publish(self.work)

        self.assertEqual(result.returncode, 0, result.stderr)
        bot_sha = self.remote_sha(BOT_BRANCH)
        changed = self.git(
            "--git-dir", str(self.origin), "diff", "--name-only", self.main_sha, bot_sha,
        ).stdout.splitlines()
        self.assertEqual(set(changed), {"candidates.json", "watch.json"})
        self.assertEqual(self.remote_sha("main"), self.main_sha)
        self.assertEqual(self.remote_file(BOT_BRANCH, "papers.json"), '{"papers": []}\n')
        self.assertEqual(
            self.git("diff", "--cached", "--name-only", cwd=self.work).stdout.strip(),
            "papers.json",
            "Unrelated staged user changes should remain staged",
        )
        self.assertEqual(
            self.git("--git-dir", str(self.origin), "rev-parse", bot_sha + "^").stdout.strip(),
            self.main_sha,
        )
        for filename in ("candidates.json", "watch.json"):
            self.assertEqual(self.remote_file(BOT_BRANCH, filename), (self.work / filename).read_text())

    def test_identical_report_keeps_remote_branch_sha(self):
        previous_sha = self.publish_first_report()
        rerun = self.clone("rerun")
        self.write_report(rerun, "scan-1")

        result = self.publish(rerun, previous_sha)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_sha(BOT_BRANCH), previous_sha)
        self.assertEqual(self.remote_sha("main"), self.main_sha)
        self.assertEqual(self.git("branch", "--show-current", cwd=rerun).stdout.strip(), "main")

    def test_refresh_rebuilds_snapshot_from_latest_main(self):
        previous_sha = self.publish_first_report()
        (self.seed / "README.md").write_text("Updated on main\n", encoding="utf-8")
        (self.seed / "papers.json").write_text('{"papers": ["reviewed"]}\n', encoding="utf-8")
        self.git("add", "README.md", "papers.json", cwd=self.seed)
        self.git("commit", "-m", "Merge reviewed catalog", cwd=self.seed)
        self.git("push", "origin", "main", cwd=self.seed)
        new_main_sha = self.remote_sha("main")
        next_run = self.clone("next-run")
        self.write_report(next_run, "scan-2")

        result = self.publish(next_run, previous_sha)

        self.assertEqual(result.returncode, 0, result.stderr)
        new_bot_sha = self.remote_sha(BOT_BRANCH)
        self.assertNotEqual(new_bot_sha, previous_sha)
        self.assertEqual(self.remote_sha("main"), new_main_sha)
        self.assertEqual(
            self.git("--git-dir", str(self.origin), "rev-parse", new_bot_sha + "^").stdout.strip(),
            new_main_sha,
        )
        for filename in ("README.md", "papers.json"):
            self.assertEqual(self.remote_file(BOT_BRANCH, filename), self.remote_file("main", filename))
        self.assertEqual(json.loads(self.remote_file(BOT_BRANCH, "watch.json")), {"scan": "scan-2"})
        self.assertEqual(
            set(self.git("--git-dir", str(self.origin), "diff", "--name-only", new_main_sha, new_bot_sha).stdout.splitlines()),
            {"candidates.json", "watch.json"},
        )

    def test_concurrent_remote_advance_rejects_stale_lease(self):
        inspected_sha = self.publish_first_report()
        stale_run = self.clone("stale-run")
        self.write_report(stale_run, "stale-scan")
        concurrent = self.clone("concurrent", BOT_BRANCH)
        self.write_report(concurrent, "newer-scan")
        self.git("add", "candidates.json", "watch.json", cwd=concurrent)
        self.git("commit", "-m", "Concurrent discovery update", cwd=concurrent)
        self.git("push", "origin", BOT_BRANCH, cwd=concurrent)
        concurrent_sha = self.remote_sha(BOT_BRANCH)

        result = self.publish(stale_run, inspected_sha)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale info", result.stderr)
        self.assertEqual(self.remote_sha(BOT_BRANCH), concurrent_sha)
        self.assertEqual(self.remote_sha("main"), self.main_sha)
        self.assertEqual(json.loads(self.remote_file(BOT_BRANCH, "watch.json")), {"scan": "newer-scan"})

    def test_main_is_rejected_as_target_before_staging_or_committing(self):
        self.write_report(self.work, "unpublished")

        result = self.publish(self.work, branch="main")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing", result.stderr)
        self.assertEqual(self.remote_sha("main"), self.main_sha)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.work).stdout.strip(), self.main_sha)
        self.assertEqual(self.git("diff", "--cached", "--name-only", cwd=self.work).stdout, "")
        self.assertEqual(
            self.git("--git-dir", str(self.origin), "for-each-ref", "--format=%(refname)", "refs/heads").stdout.strip(),
            "refs/heads/main",
        )

    def test_previous_sha_must_be_explicit_even_for_new_branch(self):
        self.write_report(self.work, "unpublished")

        result = self.publish(self.work, missing_sha=True)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PREVIOUS_BOT_SHA", result.stderr)
        self.assertEqual(self.remote_sha("main"), self.main_sha)
        self.assertEqual(self.git("diff", "--cached", "--name-only", cwd=self.work).stdout, "")
        self.assertEqual(
            self.git("--git-dir", str(self.origin), "for-each-ref", "--format=%(refname)", "refs/heads").stdout.strip(),
            "refs/heads/main",
        )


if __name__ == "__main__":
    unittest.main()
