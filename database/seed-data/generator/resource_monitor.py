#!/usr/bin/env python
"""
Resource Monitor for Dataset Scaling

Monitors system resources (memory, CPU) during generation.
Prevents memory exhaustion and excessive CPU usage.
"""

import logging
import os

import psutil

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor system resources during dataset generation."""

    MAX_MEMORY_PCT = 85
    MAX_CPU_PCT = 95

    def __init__(self):
        """Initialize resource monitor."""
        self.process = psutil.Process(os.getpid())

    def check_memory(self) -> tuple[bool, str]:
        """
        Check system memory usage.

        Returns:
            (is_ok: bool, message: str)
        """
        try:
            mem = psutil.virtual_memory()
            mem_used_pct = mem.percent
            mem_available_gb = mem.available / (1024**3)

            msg = f"System Memory: {mem_used_pct:.1f}% used ({mem_available_gb:.1f} GB available)"

            if mem_used_pct >= self.MAX_MEMORY_PCT:
                msg += f"\n  ❌ CRITICAL: Memory at {mem_used_pct:.1f}% (threshold: {self.MAX_MEMORY_PCT}%)"
                return (False, msg)

            if mem_used_pct >= 75:
                msg += f"\n  ⚠️  WARNING: Memory at {mem_used_pct:.1f}%"
                return (True, msg)

            msg += "\n  ✅ OK"
            return (True, msg)

        except Exception as e:
            return (False, f"Memory check: ❌ {e}")

    def check_process_memory(self, limit_mb: int = 2048) -> tuple[bool, str]:
        """
        Check current process memory usage.

        Args:
            limit_mb: Memory limit in MB (default 2048)

        Returns:
            (is_ok: bool, message: str)
        """
        try:
            process_mem_mb = self.process.memory_info().rss / (1024**2)

            msg = f"Process Memory: {process_mem_mb:.1f} MB (limit: {limit_mb} MB)"

            if process_mem_mb >= limit_mb:
                msg += "\n  ❌ CRITICAL: Process memory exceeds limit"
                return (False, msg)

            if process_mem_mb >= (limit_mb * 0.8):
                msg += f"\n  ⚠️  WARNING: Process memory at {(process_mem_mb / limit_mb * 100):.1f}% of limit"
                return (True, msg)

            msg += "\n  ✅ OK"
            return (True, msg)

        except Exception as e:
            return (False, f"Process memory check: ❌ {e}")

    def check_cpu(self) -> tuple[bool, str]:
        """
        Check CPU usage.

        Returns:
            (is_ok: bool, message: str)
        """
        try:
            cpu_pct = psutil.cpu_percent(interval=1)

            msg = f"CPU Usage: {cpu_pct:.1f}%"

            if cpu_pct >= self.MAX_CPU_PCT:
                msg += f"\n  ⚠️  WARNING: CPU at {cpu_pct:.1f}%"
                return (True, msg)

            msg += "\n  ✅ OK"
            return (True, msg)

        except Exception as e:
            return (False, f"CPU check: ❌ {e}")

    def check_all(self, process_limit_mb: int = 2048) -> tuple[bool, str]:
        """
        Run all resource checks.

        Args:
            process_limit_mb: Memory limit for process in MB

        Returns:
            (all_ok: bool, combined_message: str)
        """
        checks = [
            self.check_memory(),
            self.check_process_memory(process_limit_mb),
            self.check_cpu(),
        ]

        all_ok = all(check[0] for check in checks)
        message = "\n".join(check[1] for check in checks)

        return (all_ok, message)
