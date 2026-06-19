#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path


def _windows_peak_working_set(process: subprocess.Popen) -> int | None:
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCountersEx(ctypes.Structure):
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
            ("PrivateUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(
        int(process._handle),
        ctypes.byref(counters),
        counters.cb,
    )
    if not ok:
        return None
    return int(counters.PeakWorkingSetSize)


def _unix_peak_rss_bytes() -> int | None:
    if os.name == "nt":
        return None
    try:
        import resource
    except ImportError:
        return None
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    value = int(usage.ru_maxrss)
    if sys.platform == "darwin":
        return value
    return value * 1024


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure wall time and OS-level peak RSS/working set for a command.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command:
        parser.error("command is required")

    start = time.perf_counter()
    process = subprocess.Popen(args.command)
    return_code = process.wait()
    elapsed = time.perf_counter() - start
    peak_bytes = _windows_peak_working_set(process) or _unix_peak_rss_bytes()
    result = {
        "command": args.command,
        "return_code": return_code,
        "wall_seconds": elapsed,
        "peak_rss_bytes": peak_bytes,
        "peak_rss_mb": None if peak_bytes is None else peak_bytes / (1024 * 1024),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
