"""
PDF dependency helpers.

Goal: end-users should never see missing-PDF-engine errors when clicking download
buttons. We attempt a one-time, on-demand install and then retry imports.
"""

from __future__ import annotations

import importlib
import sys
import subprocess
from typing import Optional


_REPORTLAB_READY: Optional[bool] = None


def ensure_reportlab_installed(logger=None) -> bool:
    """
    Ensure the `reportlab` package is importable.

    Returns True if reportlab can be imported after this call, otherwise False.
    """
    global _REPORTLAB_READY

    if _REPORTLAB_READY is True:
        return True

    try:
        import reportlab  # noqa: F401

        _REPORTLAB_READY = True
        return True
    except Exception:
        pass

    # Try a one-time install
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "reportlab"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            if logger:
                logger.warning(
                    "Auto-install of reportlab failed (exit %s): %s",
                    proc.returncode,
                    (proc.stderr or proc.stdout or "").strip(),
                )
            _REPORTLAB_READY = False
            return False

        importlib.invalidate_caches()
        import reportlab  # noqa: F401

        _REPORTLAB_READY = True
        return True
    except Exception as e:
        if logger:
            try:
                logger.exception("Auto-install of reportlab raised exception: %s", e)
            except Exception:
                pass
        _REPORTLAB_READY = False
        return False

