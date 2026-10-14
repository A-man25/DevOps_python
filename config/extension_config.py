# ============================================================
# Project      : HNI Build Automation
# File         : extension_config.py
# Author       : Aman Rajesh Choudhari
# Created      : 14-Oct-2026
#
# Description:
# Handles mapping between application-level HNI extension
# enums and the corresponding COP extension group tokens.
#
# Responsibilities:
# - Accept a list of Extension enum values
# - Convert each extension into its COP group representation
# - Return COP-compatible extension group strings
#
# Example:
# Input  : [Extension.HON, Extension.ALLSTEEL]
# Output : ["[hon]", "[asi]"]
#
# ============================================================

from models.enums import Extension

def get_cop_extension_groups(extensions: list[Extension]) -> list[str]:
    """Converts HNI Extension enums into COP extension group tokens."""
    cop_groups = []
    for extension in extensions:
        if extension == Extension.HON:
            cop_groups.append("[hon]")
        elif extension == Extension.ALLSTEEL:
            cop_groups.append("[asi]")
        elif extension == Extension.GUNLOCKE:
            cop_groups.append("[gunlocke]")
        elif extension == Extension.HBF:
            cop_groups.append("[hbf]")
        elif extension == Extension.HNI_CORE:
            cop_groups.append("[hniCore]")

    return cop_groups