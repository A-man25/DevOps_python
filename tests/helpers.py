# ============================================================
# Project      : HNI Build Automation
# File         : helpers.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Shared tools for the test suite.
#
# - Sandbox        : a fake server (bare Git repo) and a working
#                    clone with one test branch, in a temp folder.
#                    Tests never touch C:\CetDev or Bitbucket.
# - QuietTestCase  : catches the tool's screen output and sends
#                    its logs to a temp folder (not log/).
# - SandboxTestCase: QuietTestCase + a fresh Sandbox per test.
#
# ============================================================

import contextlib
import io
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pipeline.command_runner as command_runner

GIT_AVAILABLE = shutil.which("git") is not None
IS_WINDOWS = os.name == "nt"

ANSI_CODE_PATTERN = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

def remove_folder(path: str):
    """Deletes a folder, including Git's read-only files."""
    def make_writable(func, failed_path, error):
        os.chmod(failed_path, stat.S_IWRITE)
        func(failed_path)

    if not os.path.exists(path):
        return
    try:
        shutil.rmtree(path, onexc=make_writable)
    except TypeError:
        # Python before 3.12 has onerror instead of onexc
        shutil.rmtree(path, onerror=make_writable)

def git(cwd: str, *git_args: str) -> str:
    """Runs a Git command for a test and returns its output. Fails loudly if Git fails."""
    result = subprocess.run(["git", *git_args], cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(git_args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()

def write_file(path: str, text: str):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)

class Sandbox:
    """A fake server and a working clone with the branch test/demo.build.99.0.0 at build 99.0.0.1."""

    BRANCH = "test/demo.build.99.0.0"
    RELEASE_BRANCH = "origin/" + BRANCH
    VERSION_FILE = "hbf/extension.xml"

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="hni_build_test_")
        self.server = os.path.join(self.root, "server.git")
        self.work = os.path.join(self.root, "work")

        git(self.root, "init", "--bare", "-q", self.server)
        git(self.root, "clone", "-q", self.server, self.work)
        self.configure(self.work)

        git(self.work, "checkout", "-q", "-b", self.BRANCH)
        self.write_version("99.0.0.1")
        git(self.work, "add", ".")
        git(self.work, "commit", "-q", "-m", "99.0.0.1")
        git(self.work, "tag", "99.0.0.1")
        git(self.work, "push", "-q", "-u", "origin", self.BRANCH, "99.0.0.1")

    def configure(self, repo: str):
        """Settings that keep test commits simple on any PC."""
        git(repo, "config", "user.name", "Tester")
        git(repo, "config", "user.email", "tester@example.com")
        git(repo, "config", "commit.gpgsign", "false")
        git(repo, "config", "tag.gpgsign", "false")
        git(repo, "config", "core.autocrlf", "false")

    def clone_other_pc(self, name: str = "other") -> str:
        """A second clone, like a colleague's PC."""
        other = os.path.join(self.root, name)
        git(self.root, "clone", "-q", "-b", self.BRANCH, self.server, other)
        self.configure(other)
        return other

    def write_version(self, version: str, repo: str = None):
        write_file(os.path.join(repo or self.work, self.VERSION_FILE), f"<version>{version}</version>\n")

    def read_version(self) -> str:
        with open(os.path.join(self.work, self.VERSION_FILE), encoding="utf-8") as file:
            return file.read().strip()

    def server_tags(self) -> list[str]:
        return git(self.server, "tag", "--list").split()

    def local_tags(self) -> list[str]:
        return git(self.work, "tag", "--list").split()

    def head_subject(self) -> str:
        return git(self.work, "log", "-1", "--format=%s")

    def server_head_files(self) -> list[str]:
        return git(self.server, "show", "--name-only", "--format=", self.BRANCH).split()

    def server_files(self) -> list[str]:
        return git(self.server, "ls-tree", "-r", "--name-only", self.BRANCH).split()

    def is_clean(self) -> bool:
        return git(self.work, "status", "--porcelain", "--untracked-files=no") == ""

    def cleanup(self):
        remove_folder(self.root)

class QuietTestCase(unittest.TestCase):
    """
    Base class for tests that call the tool.
    - The tool's screen output is caught in self.screen, not printed.
    - Its log goes to a temporary folder, not the real log/ folder.
    """

    def setUp(self):
        self.log_folder = tempfile.mkdtemp(prefix="hni_build_log_")
        self.addCleanup(remove_folder, self.log_folder)

        log_patch = mock.patch.object(command_runner, "LOG_FOLDER", self.log_folder)
        log_patch.start()
        self.addCleanup(log_patch.stop)

        self.screen = io.StringIO()
        redirect = contextlib.redirect_stdout(self.screen)
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)

    def answer(self, *answers: str):
        """Gives these answers to the tool's questions, in order."""
        stdin_patch = mock.patch("sys.stdin", io.StringIO("".join(answer + "\n" for answer in answers)))
        stdin_patch.start()
        self.addCleanup(stdin_patch.stop)

    def screen_text(self) -> str:
        """What the tool printed, without colour codes."""
        return ANSI_CODE_PATTERN.sub("", self.screen.getvalue())

    def log_text(self) -> str:
        """Everything the tool wrote to its log during this test."""
        text = ""
        for name in sorted(os.listdir(self.log_folder)):
            with open(os.path.join(self.log_folder, name), encoding="utf-8") as file:
                text += file.read()
        return text

@unittest.skipUnless(GIT_AVAILABLE, "Git is not installed")
class SandboxTestCase(QuietTestCase):
    """QuietTestCase with a fresh Sandbox (fake server + clone) for every test."""

    def setUp(self):
        super().setUp()
        self.sandbox = Sandbox()
        self.addCleanup(self.sandbox.cleanup)
