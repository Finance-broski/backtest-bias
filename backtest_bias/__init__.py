"""backtest-bias: checks whether your backtest data is lying to you.

v0.1 ships one killer check done properly - survivorship - plus a CI gate.
Roadmap: look-ahead/PIT violations (v0.2), rename-continuity & corporate-action gaps (v0.3).
"""
from .core import (
    REFERENCES,
    SurvivorshipReport,
    assert_integrity,
    check_survivorship,
    dead_name_ratio,
    to_wide,
)

__version__ = "0.1.1"
__all__ = ["check_survivorship", "dead_name_ratio", "assert_integrity", "to_wide",
           "SurvivorshipReport", "REFERENCES", "__version__"]
