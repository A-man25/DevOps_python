# ============================================================
# Project      : HNI Build Automation
# File         : enums.py
# Author       : Aman Rajesh Choudhari
# Created      : 14-Oct-2026
#
# Description:
# Contains nessecary enums
# ============================================================

from enum import Enum
class Build_Type(Enum):
    NONE=0
    BETA=1
    FIRST_AID=2
    PROJECT_BASED=3

class Extension(Enum):
    NONE=0
    HON=1
    ALLSTEEL=2
    GUNLOCKE=3
    HBF=4
    HNI_CORE=5