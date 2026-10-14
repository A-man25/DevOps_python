# ============================================================
# Project      : HNI Build Automation
# File         : display.py
# Author       : Aman Rajesh Choudhari
# Created      : 14-Oct-2026
#
# Description:
# Handles console output and display formatting for the HNI
# Build Automation tool.
#
# Responsibilities:
# - Display application header
# - Display build type and extension selection menus
# - Display release/build information
# - Display build summary before execution
# - Display user-facing status messages
#
# ============================================================

def begin_msg():
    print("======================================================")
    print("                HNI BUILD AUTOMATION                  ")
    print("======================================================")

def ask_build_type_msg():
    print("Select build type:")
    print("1. Beta")
    print("2. First Aid")
    print("3. Project Based")

def ask_extension_list_msg():
    print("Select the extensions to build:")
    print("To select multiple extensions add ',' ")
    print("1. HON")
    print("2. Allsteel")
    print("3. Gunlocke")
    print("4. HBF")
    print("5. HNI-Core")

def ask_branch_info_msg():
    print("\nWhat branch do you need?")
    print("Latest [l]")
    print("Custom [c]")

def show_build_summary(build_type,extension_list,release_branch: str,release_version: str,next_build_version: str):
    print("\n======================================================")
    print("                    BUILD SUMMARY                     ")
    print("======================================================")

    print("Build Type      :", build_type.name)

    print(
        "Extensions      :",
        ", ".join(extension.name for extension in extension_list)
    )

    print("Release Branch  :", release_branch)
    print("Release Version :", release_version)
    print("Next Version    :", next_build_version)

    print("======================================================")