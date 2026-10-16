# ============================================================
# Project      : HNI Build Automation
# File         : colours.py
# Author       : Aman Rajesh Choudhari
# Created      : 16-Oct-2026
#
# Description:
# Console colours shared by every screen of the tool.
#
# ============================================================

import ctypes
import os

CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Clears from the cursor to the end of the line
CLEAR_LINE = "\033[K"

def enable_console_colours():
    """Turns on colour support in a Windows cmd window.
    Windows Terminal and VS Code already support colours.
    """
    if os.name != "nt":
        return

    kernel32 = ctypes.windll.kernel32
    stdout_handle = kernel32.GetStdHandle(-11)
    console_mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(stdout_handle, ctypes.byref(console_mode)):
        # 0x0004 = ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(stdout_handle, console_mode.value | 0x0004)
