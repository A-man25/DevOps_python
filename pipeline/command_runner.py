# ============================================================
# Project      : HNI Build Automation
# File         : command_runner.py
# Author       : Aman Rajesh Choudhari
# Created      : 16-Oct-2026
#
# Description:
# Runs COP and Git commands with one live progress line
# instead of their raw output.
#
# Responsibilities:
# - Run a command and read its output live
# - Move the progress bar from COP and Git progress lines
# - Print errors and warnings in full
# - Save the full output to the log folder (one file per day)
# - Report command success or failure
#
# ============================================================

import codecs
import os
import queue
import re
import subprocess
import threading
import time
from collections import deque
from datetime import datetime

from ui.progress import (
    can_animate,
    show_command,
    show_progress,
    show_error_header,
    show_error_line,
    show_target_result,
    show_result,
    show_failure_details
)

# Full output of every command is saved here
LOG_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")

# Removes colour codes from command output
ANSI_CODE_PATTERN = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

# COP progress line, example: "Work in progress 42% | custom.hon.hat"
COP_PROGRESS_TEXT = "Work in progress"
PERCENT_PATTERN = re.compile(r"(\d{1,3})\s*%")

# Git progress line, example: "Receiving objects:  45% (1234/2742), 1.20 MiB | 2.30 MiB/s"
GIT_PROGRESS_PATTERN = re.compile(r"([A-Za-z][A-Za-z ]+):\s+(\d{1,3})%")

# COP make target, example: "01) custom.hon      C:\CetDev\...\custom.hon.17.5.0.4-win64.cmext.buildLog.cmtxt"
TARGET_PATTERN = re.compile(r"^(\d+)\)\s+(\S+)\s*(.*)$")

# COP make result, one per finished target, example: "* Warning    custom.hbf      (worker1, time: 00:01:04)"
RESULT_PATTERN = re.compile(r"^\*\s+(\w+)\s+(\S+)\s*(.*)$")
FAILED_STATUS_LIST = ["error", "errors", "failed"]

# COP prints these when a command fails but still exits with code 0
FAILURE_TEXT_LIST = [
    "No files to upload",
    "Upload finished with errors",
    "Upload completed with errors",
    "Error: not all files were successfully uploaded"
]

# COP make summary, example:
# "===== Work completed in 00:21:03: 36 item(s), 35 succeeded, 0 with warnings, 1 failed, 0 skipped or cancelled ====="
SUMMARY_COUNTS_PATTERN = re.compile(r"\d+ item\(s\).*")
FAILED_COUNT_PATTERN = re.compile(r"(\d+) failed")

# COP prints this when it needs a MyConfigura login it cannot ask for
LOGIN_NEEDED_TEXT = "Login via console is not available"
LOGIN_HINT = "COP needs a MyConfigura login. Run 'cop login' once in a normal terminal, then start the build again."

FRAME_SECONDS = 0.1
RECENT_LINE_COUNT = 15
MAX_ERROR_LINES = 40

def read_output(process: subprocess.Popen, output_queue: queue.Queue):
    """
    Reads command output and passes it to the main thread line by line.
    COP and Git end some lines with \\r instead of \\n when they
    redraw them, so both are treated as the end of a line.
    """
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    partial_line = ""
    while True:
        chunk = process.stdout.read1(4096)
        if not chunk:
            break

        lines = re.split(r"\r\n|\r|\n", partial_line + decoder.decode(chunk))
        partial_line = lines.pop()
        for line in lines:
            output_queue.put(line)

    if partial_line:
        output_queue.put(partial_line)

def run_command_live(command: list[str], cwd: str, title: str, detail: str = "") -> bool:
    """
    Runs a COP or Git command and shows one animated progress
    line instead of its raw output.

    - Progress lines move the progress bar
    - Other lines are shown as the current status
    - Errors and warnings are printed in full
    - The full output is saved to the log folder

    detail is shown next to [ OK ] when the command succeeds.
    Returns True if the command succeeds.
    """
    show_command(command)

    os.makedirs(LOG_FOLDER, exist_ok=True)
    output_log_path = os.path.join(LOG_FOLDER, f"build_{datetime.now():%Y%m%d}.log")

    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Output is read on a separate thread so the animation
    # keeps moving while the command is quiet
    output_queue = queue.Queue()
    reader_thread = threading.Thread(target=read_output, args=(process, output_queue), daemon=True)
    reader_thread.start()

    animate = can_animate()
    start_time = time.monotonic()
    last_output_time = start_time
    frame = 0
    percent = None
    status = "Starting..."
    summary = ""
    cop_log_path = ""
    target_logs = {}
    finished_targets = []
    failed_targets = []
    failure_text = ""
    recent_lines = deque(maxlen=RECENT_LINE_COUNT)
    in_error_section = False
    error_line_count = 0
    login_needed = False

    with open(output_log_path, "a", encoding="utf-8") as output_log:
        output_log.write(f"\n===== {datetime.now():%H:%M:%S}  {' '.join(command)} =====\n")

        while True:
            # Handle every line printed since the last frame
            while not output_queue.empty():
                line = output_queue.get()
                last_output_time = time.monotonic()
                output_log.write(line + "\n")

                line = ANSI_CODE_PATTERN.sub("", line).strip()
                if not line:
                    continue

                if COP_PROGRESS_TEXT in line:
                    percent_match = PERCENT_PATTERN.search(line)
                    if percent_match:
                        percent = min(int(percent_match.group(1)), 100)

                    # Text after the "|" is what COP is working on
                    if "|" in line:
                        status = line.split("|", 1)[1].strip()
                    continue

                git_progress_match = GIT_PROGRESS_PATTERN.search(line)
                if git_progress_match:
                    status = git_progress_match.group(1).strip()
                    percent = min(int(git_progress_match.group(2)), 100)
                    continue

                # Remember each target's build log, but keep the long path off the screen
                target_match = TARGET_PATTERN.match(line)
                if target_match:
                    target_logs[target_match.group(2)] = target_match.group(3)
                    status = f"Found {len(target_logs)} target(s)"
                    continue

                recent_lines.append(line)
                result_match = RESULT_PATTERN.match(line)

                if LOGIN_NEEDED_TEXT in line:
                    login_needed = True

                for this_text in FAILURE_TEXT_LIST:
                    if this_text in line:
                        failure_text = this_text

                if line.startswith("Log file path:") or line.startswith("Log file is available here:"):
                    cop_log_path = line.split(":", 1)[1].strip()
                elif "Work completed" in line:
                    summary = line.strip("= ")
                    in_error_section = False
                elif result_match and result_match.group(2) in target_logs:
                    # A COP make target has finished: move the bar
                    result_status, target, result_details = result_match.groups()
                    finished_targets.append(target)
                    percent = len(finished_targets) * 100 // len(target_logs)
                    status = f"{len(finished_targets)}/{len(target_logs)} done · {target}"

                    target_failed = result_status.lower() in FAILED_STATUS_LIST
                    if target_failed:
                        failed_targets.append(target)

                    # Only targets with errors or warnings stay on screen
                    if target_failed or result_status.lower().startswith("warn"):
                        show_target_result(result_status, target, result_details, target_failed)
                elif "ERRORS / WARNINGS DURING BUILD" in line:
                    in_error_section = True
                    show_error_header(line)
                elif in_error_section:
                    error_line_count += 1
                    if error_line_count <= MAX_ERROR_LINES:
                        show_error_line(line)
                    elif error_line_count == MAX_ERROR_LINES + 1:
                        show_error_line("... more errors in the full output log")
                else:
                    status = line

            # The command has exited, but processes it started (like COP's
            # build workers) can keep its output open. Stop once nothing
            # new arrives for 1 second.
            if process.poll() is not None and time.monotonic() - last_output_time >= 1:
                break

            if animate:
                show_progress(title, time.monotonic() - start_time, percent, status, frame)

            frame += 1
            time.sleep(FRAME_SECONDS)

    elapsed_seconds = time.monotonic() - start_time

    failed_match = FAILED_COUNT_PATTERN.search(summary)
    has_failed_items = failed_match is not None and int(failed_match.group(1)) > 0
    success = process.returncode == 0 and not has_failed_items and not failed_targets and not failure_text

    # COP make: only the counts, e.g. "36 item(s), 36 succeeded, ..."
    counts_match = SUMMARY_COUNTS_PATTERN.search(summary)
    if counts_match:
        detail = counts_match.group()
    elif failure_text:
        detail = failure_text
    elif not success:
        detail = f"exit code {process.returncode}"

    show_result(title, elapsed_seconds, success, detail)
    if not success:
        hint = ""
        if login_needed:
            hint = LOGIN_HINT
        show_failure_details(failed_targets, target_logs, list(recent_lines), cop_log_path, output_log_path, hint)

    return success
