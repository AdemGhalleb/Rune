"""Windows OneDrive Files-On-Demand / cloud-placeholder detector."""

import ctypes
import os
import sys
from pathlib import Path


def is_onedrive_placeholder(file_path: Path) -> bool:
    """Check if file is a cloud-only placeholder (OneDrive Files-On-Demand / recall point).

    If true, opening the file would trigger a download or hang/fail.
    """
    if sys.platform != "win32" or os.name != "nt":
        return False

    try:
        # GetFileAttributesW
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
        if attrs == 0xFFFFFFFF:
            return False

        # FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS (0x00400000)
        # FILE_ATTRIBUTE_RECALL_ON_OPEN (0x00040000)
        # FILE_ATTRIBUTE_OFFLINE (0x1000)
        recall_on_data_access = 0x00400000
        recall_on_open = 0x00040000
        offline = 0x00001000

        if (
            bool(attrs & recall_on_data_access)
            or bool(attrs & recall_on_open)
            or bool(attrs & offline)
        ):
            return True

    except Exception:
        pass

    return False
