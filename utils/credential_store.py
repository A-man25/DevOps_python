# ============================================================
# Project      : HNI Build Automation
# File         : credential_store.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Saves the MyConfigura login in Windows Credential Manager,
# so it does not have to be typed for every build.
#
# Responsibilities:
# - Save the login (only when the user agrees)
# - Read the saved login
# - Delete the saved login (e.g. when the password has changed)
#
# Windows encrypts the saved password with the user's Windows
# login. Only the same Windows user on the same PC can read it.
# It shows in Control Panel > Credential Manager > Windows
# Credentials as "HNI_Build_Automation/MyConfigura".
#
# ============================================================

import ctypes
from ctypes import wintypes

CREDENTIAL_NAME = "HNI_Build_Automation/MyConfigura"

# Values from the Windows API (wincred.h)
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2

class CREDENTIAL(ctypes.Structure):
    """The Windows CREDENTIALW structure."""
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.c_void_p),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR)
    ]

advapi32 = ctypes.WinDLL("advapi32")
advapi32.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
advapi32.CredWriteW.restype = wintypes.BOOL
advapi32.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
advapi32.CredReadW.restype = wintypes.BOOL
advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
advapi32.CredDeleteW.restype = wintypes.BOOL
advapi32.CredFree.argtypes = [ctypes.c_void_p]
advapi32.CredFree.restype = None

def save_login(email: str, password: str) -> bool:
    """Saves the login in Windows Credential Manager. Returns True if it worked."""
    password_bytes = password.encode("utf-16-le")
    password_buffer = ctypes.create_string_buffer(password_bytes, len(password_bytes))

    credential = CREDENTIAL()
    credential.Type = CRED_TYPE_GENERIC
    credential.TargetName = CREDENTIAL_NAME
    credential.UserName = email
    credential.CredentialBlobSize = len(password_bytes)
    credential.CredentialBlob = ctypes.cast(password_buffer, ctypes.c_void_p)
    credential.Persist = CRED_PERSIST_LOCAL_MACHINE
    return bool(advapi32.CredWriteW(ctypes.byref(credential), 0))

def load_saved_login() -> tuple[str, str] | None:
    """Returns the saved (email, password), or None if nothing is saved."""
    credential_pointer = ctypes.POINTER(CREDENTIAL)()
    if not advapi32.CredReadW(CREDENTIAL_NAME, CRED_TYPE_GENERIC, 0, ctypes.byref(credential_pointer)):
        return None

    try:
        credential = credential_pointer.contents
        password_bytes = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        return credential.UserName, password_bytes.decode("utf-16-le")
    finally:
        advapi32.CredFree(credential_pointer)

def delete_saved_login():
    """Removes the saved login, if there is one."""
    advapi32.CredDeleteW(CREDENTIAL_NAME, CRED_TYPE_GENERIC, 0)
