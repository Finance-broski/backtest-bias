# Preregistration (verbatim extract)

Paper: "Survivorship Bias in Indian Equities Is Not a Number: Vintage- and
Filter-Dependence in Point-in-Time Universes" (SSRN 7099378).

The following block is reproduced verbatim from the research repository file
`PREREG_LIBRARY_SPRINT.md` as committed at 2026-07-11 14:25:01 IST
(commit 5307bdcd96f0e21a3c79f74e7fcd2c1a92fff521), before the first battery
results were committed at 14:28:53 IST (92dddd2e401478aa5df8c23625bcd1c4b4f183b4).

---

## P2 BATTERY PREREG-LITE (paper computation, descriptive — filed 2026-07-11 14:30)
Purpose: publication-grade reconciliation for the survivorship-vintage paper. NO decision
thresholds (measurement paper); trials logged; firewall: PIT construction described at
family level only in the paper; the public 99-name notebook = the replication asset.
THE 2x2 (locked): vintages {2013-01, 2015-01} x survivor filters {PANEL-ALIVE at 2026-05
(has prices after 2026-05-01), YF-RESOLVABLE today (availability check per vintage's
terminal symbols — the 2013 set gets its own fresh yfinance pass, own checkpoint CSV)}.
Construction identical across cells: PIT top-500 at vintage, EW monthly, same panel
tr_close, common END 2024-12 (windows differ only in start), honest arm = full universe,
survivor arm = filter-passing subset. Report per cell: honest CAGR, survivor CAGR, gap
pp/yr, terminal-wealth %, persistence (% months survivor>honest). Also re-extracted for
the paper: death curves (six vintages), invisibility taxonomy counts, exit examples.
4 cells + 2 availability passes = 6 logged trials. Executor self-audit inline (machinery
reuses T1/T7-audited patterns). Sign-off on the paper draft, not per-cell.
Paper-draft sign-off (P2 battery + paper v1.0, full read-through complete with 4 caught-and-fixed
issues): AJ, 2026-07-11

SIGN-OFF RECORD: all ten sign-offs above stamped AJ, 2026-07-11 on Ayan's explicit chat
instruction ("initial all 10 as AJ", 2026-07-11 16:54 IST). No verdict was excepted.
