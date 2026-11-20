"""Process RSS in megabytes. Returns None when the OS does not expose it."""

from __future__ import annotations

import sys
from pathlib import Path


def rss_mb() -> float | None:
    try:
        if sys.platform == "win32":
            return _windows_rss_mb()
        status = Path("/proc/self/status").read_text(encoding="utf-8")
    except OSError:
        return None
    for line in status.splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024.0
    return None


def _windows_rss_mb() -> float | None:
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    fn = getattr(kernel, "K32GetProcessMemoryInfo")
    fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    fn.restype = wintypes.BOOL
    handle = kernel.GetCurrentProcess()
    if not fn(handle, ctypes.byref(counters), counters.cb):
        return None
    return counters.WorkingSetSize / (1024.0 * 1024.0)
