# ============================================================
# Project      : HNI Build Automation
# File         : input_handler.py
# Author       : Aman Rajesh Choudhari
# Description  : Handles user input and converts selections
#                into build type and extension enums.
# Created      : 14-Oct-2026
# ============================================================

from .display import (
    ask_build_type_msg,
    ask_extension_list_msg,
    ask_branch_info_msg,
    prompt_text,
    show_input_error_msg,

    # Test
    ask_Test_branch_info_msg
    )

from models.enums import (
    Build_Type,
    Extension
)

def get_build_type()->Build_Type:
    ask_build_type_msg()
    user_input = input(prompt_text("Enter choice: :) "))
    build_type = get_build_type_enum(user_input)
    if(build_type == Build_Type.NONE):
        show_input_error_msg("Incorrect input.")
        return get_build_type()

    return build_type

def get_build_type_enum(input_str: str)->Build_Type:
    build_type_en = Build_Type.NONE
    input_str = input_str.lower().strip()
    if input_str == "1" or input_str == "beta":
        build_type_en = Build_Type.BETA
    elif input_str == "2" or input_str == "first aid":
        build_type_en = Build_Type.FIRST_AID
    elif input_str == "3" or input_str == "project based":
        build_type_en = Build_Type.PROJECT_BASED

    return build_type_en


def get_extension_list()->list[Extension]:
    ask_extension_list_msg()
    user_input = input(prompt_text("Enter your choices: :) "))
    input_list = user_input.split(",")
    extension_list = get_extension_enum(input_list)
    if Extension.NONE in extension_list:
        show_input_error_msg("Incorrect extension entered.")
        return get_extension_list()

    return extension_list

def get_extension_enum(input_list: list[str]) -> list[Extension]:
    extension_list = []
    for this_input in input_list:
        this_input = this_input.lower().strip()
        if this_input == "1" or this_input == "hon":
            extension = Extension.HON
        elif this_input == "2" or this_input == "allsteel":
            extension = Extension.ALLSTEEL
        elif this_input == "3" or this_input == "gunlocke":
            extension = Extension.GUNLOCKE
        elif this_input == "4" or this_input == "hbf":
            extension = Extension.HBF
        elif this_input == "5" or this_input in ("hni core", "hnicore"):
            extension = Extension.HNI_CORE
        else:
            extension = Extension.NONE

        if extension not in extension_list:
            extension_list.append(extension)

    return extension_list

def get_release_branch_input() ->str:
    """If user specifies a release branch, use that one.
    Otherwise, use the latest available release branch.
    """
    ask_branch_info_msg()
    input_str = input(prompt_text("Enter your choice [l/c]: "))
    input_str = input_str.lower().strip()
    if input_str == "l":
        return "l"
    elif input_str == "c":
        return "c"

    show_input_error_msg("Incorrect input.")

    return get_release_branch_input()


def get_custom_release_branch()->str:
    user_input = input(prompt_text("Enter release branch: "))
    return user_input

def get_build_confirmation() -> bool:
    user_input = input(prompt_text("Proceed with build? [y/n]: "))
    user_input = user_input.lower().strip()
    if user_input == "y" or user_input == "yes":
        return True
    elif user_input == "n" or user_input == "no":
        return False
    show_input_error_msg("Incorrect input.")
    return get_build_confirmation()

def get_git_changes_confirmation() -> bool:
    """Confirms whether the displayed Git changes are safe to commit."""
    user_input = input(prompt_text("Are these changes correct and safe to commit? [y/n]: "))
    user_input = user_input.lower().strip()
    if user_input == "y" or user_input == "yes":
        return True
    elif user_input == "n" or user_input == "no":
        return False

    show_input_error_msg("Incorrect input.")
    return get_git_changes_confirmation()

def get_git_changes_push_confirmation() -> bool:
    """Confirms whether the displayed Git changes are safe to push."""
    user_input = input(prompt_text("Are these changes correct and safe to push? [y/n]: "))
    user_input = user_input.lower().strip()
    if user_input == "y" or user_input == "yes":
        return True
    elif user_input == "n" or user_input == "no":
        return False

    show_input_error_msg("Incorrect input.")
    return get_git_changes_push_confirmation()

# Test
def get_test_branch_input(test_branch_list: list[str]) ->str:
    """Shows the available test branches and asks for one.
    Accepts origin/test/<name>, test/<name> or <name>.
    """
    ask_Test_branch_info_msg(test_branch_list)
    user_input = input(prompt_text("Enter test branch: "))
    return user_input
