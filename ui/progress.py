# ============================================================
# Project      : HNI Build Automation
# File         : progress.py
# Author       : Aman Rajesh Choudhari
# Created      : 16-Oct-2026
#
# Description:
# Draws the live progress line shown while a COP or Git
# command is running, and the result line when it finishes.
#
# Example:
#   ●○○  COP MAKE         [██████████░░░░░░░░░░░░░░]  42%  00:03:21  custom.hon.hat
#   [ OK ]  COP MAKE         00:21:03  36 item(s), 36 succeeded
#
# ============================================================

import shutil
import sys

from ui.colours import (
    CYAN,
    GREEN,
    RED,
    YELLOW,
    DIM,
    BOLD,
    RESET,
    CLEAR_LINE
)

SPINNER_FRAMES = ["●○○", "○●○", "○○●", "○●○"]
BAR_WIDTH = 24
BOUNCE_BLOCK_WIDTH = 6
TITLE_WIDTH = 16

def can_animate() -> bool:
    """The animation only works when output goes to a console, not to a file."""
    return sys.stdout.isatty()

def format_elapsed_time(elapsed_seconds: float) -> str:
    """Converts seconds into HH:MM:SS."""
    elapsed_seconds = int(elapsed_seconds)
    hours = elapsed_seconds // 3600
    minutes = elapsed_seconds % 3600 // 60
    seconds = elapsed_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def get_progress_bar(percent: int | None, frame: int) -> str:
    """
    Returns the progress bar.
    Known percent   : the bar fills up       ██████████░░░░░░░░░░░░░░
    Unknown percent : a block bounces across ░░░░░░██████░░░░░░░░░░░░
    """
    if percent is not None:
        filled = round(percent / 100 * BAR_WIDTH)
        return "█" * filled + "░" * (BAR_WIDTH - filled)

    travel = BAR_WIDTH - BOUNCE_BLOCK_WIDTH
    position = frame % (travel * 2)
    if position > travel:
        position = travel * 2 - position

    return "░" * position + "█" * BOUNCE_BLOCK_WIDTH + "░" * (travel - position)

def show_command(command: list[str]):
    """Shows the command that is about to run."""
    print(f"  {DIM}> {' '.join(command)}{RESET}")

def show_progress(title: str, elapsed_seconds: float, percent: int | None, status: str, frame: int):
    """Redraws the live progress line in place."""
    width = shutil.get_terminal_size().columns - 1
    spinner = SPINNER_FRAMES[frame // 2 % len(SPINNER_FRAMES)]
    bar = get_progress_bar(percent, frame)
    elapsed = format_elapsed_time(elapsed_seconds)
    if percent is not None:
        percent_text = f"{percent:>3}%"
    else:
        percent_text = "    "

    # A line wider than the window wraps onto a second line, and then every
    # redraw adds a new line. In a narrow window, use a short line without
    # the bar; in a normal window, cut the status to fit.
    used_width = len(f"  {spinner}  {title:<{TITLE_WIDTH}} [{bar}] {percent_text}  {elapsed}  ")
    if used_width > width:
        short_line = f"  {spinner} {title} {percent_text.strip()} {elapsed} {status}"
        print(f"\r{short_line[:max(0, width)]}{CLEAR_LINE}", end="", flush=True)
        return

    status = status[:width - used_width]

    print(
        f"\r  {CYAN}{spinner}{RESET}  {BOLD}{title:<{TITLE_WIDTH}}{RESET} "
        f"[{CYAN}{bar}{RESET}] {percent_text}  {DIM}{elapsed}{RESET}  {status}{CLEAR_LINE}",
        end="",
        flush=True
    )

def clear_progress():
    print(f"\r{CLEAR_LINE}", end="", flush=True)

def show_idle_hint(title: str, minutes: int):
    """Shown once when a command has printed nothing for a long time."""
    clear_progress()
    print(f"  {YELLOW}! {title} has printed nothing for {minutes} minutes. It may still be working.{RESET}")
    print(f"  {YELLOW}  If it looks stuck, press Ctrl+C to stop it (the full output is in the log).{RESET}")

def show_waiting_prompt(title: str, question: str):
    """
    Shows a question the running command is waiting on.
    The cursor stays after the question, so the answer can be typed there.
    """
    clear_progress()
    print(f"  {YELLOW}{BOLD}! {title} is waiting for an answer. Type it and press Enter.{RESET}")
    print(f"  {YELLOW}{BOLD}?{RESET} {BOLD}{question}{RESET} ", end="", flush=True)

def end_waiting_prompt():
    """Moves below the answered question, so the progress line does not draw over it."""
    print()

def show_error_header(line: str):
    clear_progress()
    print(f"\n    {RED}{BOLD}{line}{RESET}")

def show_error_line(line: str):
    clear_progress()
    print(f"    {YELLOW}{line}{RESET}")

def show_target_result(status: str, target: str, details: str, failed: bool):
    """Prints a COP make target that finished with errors or warnings."""
    clear_progress()
    if failed:
        colour = RED
    else:
        colour = YELLOW

    print(f"    {colour}{BOLD}{status:<8}{RESET} {target:<34} {DIM}{details}{RESET}")

def show_result(title: str, elapsed_seconds: float, success: bool, detail: str):
    """Replaces the live progress line with the final result."""
    clear_progress()
    if success:
        badge = f"{GREEN}{BOLD}[ OK ]{RESET}"
    else:
        badge = f"{RED}{BOLD}[FAIL]{RESET}"

    print(f"  {badge}  {BOLD}{title:<{TITLE_WIDTH}}{RESET} {DIM}{format_elapsed_time(elapsed_seconds)}{RESET}  {detail}")

def show_reading_errors_msg():
    print(f"\n    {DIM}Reading the compile errors from the last build...{RESET}")

def show_compile_errors(error_lines: list[str], max_lines: int = 40):
    """Shows the compile errors COP saved for the failed targets."""
    if not error_lines:
        print(f"    {YELLOW}COP gave no error details. Open the failed target's build log above.{RESET}")
        return

    print(f"\n    {RED}{BOLD}Compile errors:{RESET}")
    for line in error_lines[:max_lines]:
        print(f"    {YELLOW}{line}{RESET}")

    if len(error_lines) > max_lines:
        print(f"    {DIM}... {len(error_lines) - max_lines} more line(s) in the failed target's build log{RESET}")

def show_failure_details(failed_targets: list[str], target_logs: dict[str, str], recent_lines: list[str], cop_log_path: str, output_log_path: str, hint: str):
    """Shows what failed, the last lines printed and where to find the full logs."""
    if hint:
        print(f"\n    {YELLOW}{BOLD}{hint}{RESET}")

    if failed_targets:
        print(f"\n    {RED}Failed targets:{RESET}")
        for target in failed_targets:
            print(f"    - {target}")
            if target_logs.get(target):
                print(f"      {DIM}{target_logs[target]}{RESET}")

    print(f"\n    {YELLOW}Last output:{RESET}")
    for line in recent_lines:
        print(f"    {DIM}{line}{RESET}")

    print()
    if cop_log_path:
        print(f"    COP log         : {cop_log_path}")
    print(f"    Full output     : {output_log_path}")
