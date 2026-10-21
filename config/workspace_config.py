# ============================================================
# Project      : HNI Build Automation
# File         : workspace_config.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Holds the path of the extensions repo inside the CET
# workspace (where git and cop commands run).
#
# Each PC can use its own path without editing this file:
# set the Windows environment variable HNI_BUILD_REPO_PATH, e.g.
#   setx HNI_BUILD_REPO_PATH "C:\CetDev\WPF\extensions\custom"
#
# ============================================================

import os

DEFAULT_REPO_PATH = r"C:\CetDev\version16.5\extensions\custom"

def get_repo_path() -> str:
    """Returns HNI_BUILD_REPO_PATH if it is set, otherwise the default path."""
    return os.environ.get("HNI_BUILD_REPO_PATH", DEFAULT_REPO_PATH).strip()
