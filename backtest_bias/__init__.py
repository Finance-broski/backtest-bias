"""backtest-bias: checks whether your backtest data is lying to you.

v0.1 shipped survivorship plus a CI gate. v0.2 added the universe check (was your member
list knowable on its start date?) and the identity check (is each ticker the same company
all the way through?). v0.3 adds the selection check: does your screen's accept/reject rule
know the year it is judged on? Roadmap: price-level look-ahead / timestamp checks.
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
from .selection import (
    SelectionReport,
    check_selection,
    eg_both_ways,
    eg_critical_value,
    return_correlation,
    zscore_rule_pnl,
)

__version__ = "0.3.0"
__all__ = ["check_survivorship", "check_identity", "check_universe", "dead_name_ratio",
           "assert_integrity", "to_wide", "expected_death_range", "SurvivorshipReport",
           "IdentityReport", "UniverseReport", "REFERENCES", "__version__",
           "check_selection", "SelectionReport", "eg_both_ways", "eg_critical_value",
           "return_correlation", "zscore_rule_pnl"]
