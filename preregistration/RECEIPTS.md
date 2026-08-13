# Git receipts

All hashes are from the private research repository (single-branch, linear history on
these paths). Hashes are SHA-1 commit ids; each commit's id commits to its full content,
its timestamp, and its parent, so the ordering below cannot be rewritten without changing
every subsequent hash.

## The P2 sequence (design before results)

```
92dddd2e401478aa5df8c23625bcd1c4b4f183b4 2026-07-11T14:28:53+05:30 P2: 2x2 battery run (bias spans 0.8-3.3pp/yr) + full paper draft v0.1
5307bdcd96f0e21a3c79f74e7fcd2c1a92fff521 2026-07-11T14:25:01+05:30 P2 battery prereg-lite: the 2x2 vintage x survivor-filter reconciliation
```

Reading order is newest-first. The sequence: prior-art sweep and repositioning
(431707f, 14:21) -> preregistration block filed (5307bdc, 14:25) -> battery run and
paper draft v0.1 (92dddd2, 14:28). Ancestry verified:
`git merge-base --is-ancestor 5307bdc 92dddd2` returns true.

## House practice: the hash-bound prereg chain from the same morning

The P2 prereg-lite was filed inside a file whose morning history shows the house
preregistration ritual on a separate set of tests (three hostile audits, then a
ratification commit that binds the design by hash):

```
093dc49db4c2dce0ab833f695af6f704347fcd3b 2026-07-11T12:05:48+05:30 Prereg RATIFIED 12:05 (binds e217dd7); T4 8h exception granted
e217dd78b821b9c35519f5ca07373c7e8e025c28 2026-07-11T11:58:32+05:30 Prereg v1.3 after third hostile audit: A0-anchored episodes, lot-rounding rules, P1 gate rework, T3 firewall, window-pinned reproduction, hash-bound ratification, codified stopping rule
cee2bf93cab3825520d40d80d64d10b34bf44f50 2026-07-11T11:53:53+05:30 Prereg v1.2 after second hostile audit: IS-only control, count-based bands, publication firewall, split reproduction gates, composition rule, verdict sign-off
62d1a78f95be21beee2ee2fe430dbe5f3226fde7 2026-07-11T11:48:46+05:30 Prereg v1.1 after hostile self-audit: matched-exposure control, composite tail metric, next-open execution, composition-run gate, recalibrated thresholds, honesty clause
cdd65f8f5a0fdf3d2891cb72338abb91ab88f361 2026-07-11T11:20:18+05:30 Prereg: library test sprint â€” 4 tests, locked metrics/thresholds/trial counts, abort criteria, no-live-wiring-before-Aug rule (pending ratification)
```

## Scope of the claim

The paper is a descriptive measurement (all four cells of the 2x2 are reported; there
are no accept/reject thresholds to tune). The preregistration therefore locks the
design: the two vintages, the two survivor definitions, identical construction across
cells, the common end date, and the reporting plan. It was committed 3 minutes 52
seconds before the first results commit. Independent verification of the timestamps
beyond the hash chain: the SSRN submission (2026-07-11 17:12 IST, screened ~3 business
days later) and this public deposit.
