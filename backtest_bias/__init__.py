"""backtest-bias: checks whether your backtest data is lying to you.

v0.1 shipped survivorship plus a CI gate. v0.2 adds the universe check (was your member
list knowable on its start date?) and the identity check (is each ticker the same company
all the way through?). Roadmap: price-level look-ahead / timestamp checks (v0.3).
"""
from .core import (
    REFERENCES,
    IdentityReport,
    SurvivorshipReport,
    UniverseReport,
    assert_integrity,
    check_identity,
    check_survivorship,
    check_universe,
    dead_name_ratio,
    expected_death_range,
    to_wide,
)

__version__ = "0.2.0"
__all__ = ["check_survivorship", "check_identity", "check_universe", "dead_name_ratio",
           "assert_integrity", "to_wide", "expected_death_range", "SurvivorshipReport",
           "IdentityReport", "UniverseReport", "REFERENCES", "__version__"]
