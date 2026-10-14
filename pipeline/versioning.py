# ============================================================
# Project      : HNI Build Automation
# File         : versioning.py
# Author       : Aman Rajesh Choudhari
# Created      : 14-Oct-2026
#
# Description:
# Handles build-version calculation for the HNI build
# automation pipeline.
#
# Responsibilities:
# - Filter Git tags belonging to a specific release
# - Determine the latest build number for that release
# - Calculate the next build version
#
# Example:
# Release Version : 16.5.9
# Existing Tags   : 16.5.9.8, 16.5.9.9, 16.5.9.10
# Next Version    : 16.5.9.11
#
# ============================================================

def get_release_build_tags(tags : list[str], release_version : str) -> list[str]:
    release_tags = []
    prefix = release_version + "."
    for tag in tags:
        tag = tag.strip()
        if tag.startswith(prefix):
            release_tags.append(tag)

    return release_tags

def get_latest_build_number(release_tags: list[str]) ->int:
    build_number = 0
    for tag in release_tags:
        tag = tag.strip()
        this_tag = int(tag.split(".")[-1])
        if this_tag > build_number:
            build_number = this_tag

    return build_number

def get_next_build_version(release_version: str, latest_build_number: int) -> str:
    next_build_number = latest_build_number + 1
    return f"{release_version}.{next_build_number}"

def get_beta_upload_name(build_version: str) -> str:
    """Converts a build version into the Beta upload name."""
    return build_version.replace(".", "-") + "@BETA"