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
# - Display build steps and the final result
# - Display user-facing status messages
#
# ============================================================

from ui.colours import (
    CYAN,
    GREEN,
    RED,
    YELLOW,
    DIM,
    BOLD,
    RESET
)

from ui.progress import format_elapsed_time

LINE_WIDTH = 54
BOX_WIDTH = 52

def show_box(title: str, colour: str):
    """Prints a title inside a double-line box."""
    print(f"\n  {colour}{BOLD}╔{'═' * BOX_WIDTH}╗{RESET}")
    print(f"  {colour}{BOLD}║{title.center(BOX_WIDTH)}║{RESET}")
    print(f"  {colour}{BOLD}╚{'═' * BOX_WIDTH}╝{RESET}")

def show_section(title: str):
    """Prints a section heading, e.g. ── BUILD SUMMARY ──────────"""
    heading = f"── {title} "
    print(f"\n  {CYAN}{heading}{'─' * (LINE_WIDTH - len(heading))}{RESET}")

def show_end_line():
    print(f"  {CYAN}{'─' * LINE_WIDTH}{RESET}")

def show_menu_option(key: str, text: str):
    print(f"    {CYAN}{BOLD}[{key}]{RESET} {text}")

def show_value(label: str, value: str, colour: str = BOLD):
    print(f"    {DIM}{label:<16}{RESET} {colour}{value}{RESET}")

def prompt_text(text: str) -> str:
    """Returns a coloured prompt for input()."""
    return f"\n  {CYAN}{BOLD}?{RESET} {BOLD}{text}{RESET}"

def show_input_error_msg(text: str):
    print(f"  {YELLOW}! {text}{RESET}")

def show_error_msg(text: str):
    print(f"\n  {RED}{BOLD}x {text}{RESET}")

def show_warning_msg(text: str):
    print(f"\n  {YELLOW}! {text}{RESET}")

def begin_msg():
    show_box("H N I   B U I L D   A U T O M A T I O N", CYAN)

def ask_build_type_msg():
    show_section("SELECT BUILD TYPE")
    show_menu_option("1", "Beta")
    show_menu_option("2", "First Aid")
    show_menu_option("3", "Project Based")

def ask_extension_list_msg():
    show_section("SELECT EXTENSIONS")
    print(f"    {DIM}To select multiple extensions add ','{RESET}")
    show_menu_option("1", "HON")
    show_menu_option("2", "Allsteel")
    show_menu_option("3", "Gunlocke")
    show_menu_option("4", "HBF")
    show_menu_option("5", "HNI-Core")

def ask_branch_info_msg():
    show_section("RELEASE BRANCH")
    show_menu_option("l", "Latest")
    show_menu_option("c", "Custom")

def ask_myconfigura_login_msg():
    print(f"    {DIM}COP needs this to upload. Asked once per build, never saved.{RESET}")

def show_build_summary(build_type,extension_list,release_branch: str,release_version: str,next_build_version: str):
    show_section("BUILD SUMMARY")
    show_value("Build Type", build_type.name)
    show_value("Extensions", ", ".join(extension.name for extension in extension_list))
    show_value("Release Branch", release_branch)
    show_value("Release Version", release_version)
    show_value("Next Version", next_build_version, GREEN + BOLD)
    show_end_line()

def show_step(step: int, total_steps: int, name: str):
    """Prints the heading for a build step, e.g. ── STEP 3/15 · Clean workspace ──"""
    show_section(f"STEP {step}/{total_steps} · {name}")

def show_changed_files(changed_files: list[str]):
    """Shows 'git status --short' output with a colour per change type."""
    for changed_file in changed_files:
        change_type = changed_file[:2]
        file_path = changed_file[3:]
        if "D" in change_type:
            colour = RED
        elif "M" in change_type:
            colour = YELLOW
        else:
            colour = GREEN

        print(f"    {colour}{BOLD}{change_type}{RESET}  {file_path}")

    print(f"    {DIM}{len(changed_files)} file(s) changed{RESET}")

def show_build_stopped(reason: str):
    show_box("BETA BUILD STOPPED", RED)
    show_value("Reason", reason, RED)

def show_build_success(build_version: str, upload_name: str, elapsed_seconds: float):
    show_box("BETA BUILD SUCCESSFUL", GREEN)
    show_value("Build Version", build_version, GREEN + BOLD)
    show_value("Upload Name", upload_name)
    show_value("Total Time", format_elapsed_time(elapsed_seconds))


# Test
def show_dev_mode_msg():
    print(f"  {YELLOW}{BOLD}[DEV MODE]{RESET} {YELLOW}Building from origin/test/* branches{RESET}")

# Test
def ask_Test_branch_info_msg(test_branch_list: list[str]):
    show_section("TEST BRANCHES")
    for this_branch in test_branch_list:
        print(f"    {CYAN}•{RESET} {this_branch.strip()}")
