"""HR Attendance integration adapters."""
try:
    from .zkteco_adapter import ZKTecoAdapter
except Exception:
    ZKTecoAdapter = None

__all__ = ['ZKTecoAdapter']
