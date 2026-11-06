# Quick ball controls and verification

Milestone 30 adds an optional shortcut to the native single-wild battle menu:
R throws the displayed ball, L cycles forward, Y cycles backward. The visible
Prev/Next labels and ball label also accept touch. A throw uses the native Bag
response, consumes one ball through the original item handler, and retains the
normal catch calculation, effects, capture EXP and party rewards. Ordinary Bag
ball use also updates the remembered ball. Normal game saving commits that
history; saving enhancement settings alone does not commit unsaved gameplay.

Native eligibility remains: no trainer/link/double/facility/Safari/contest
shortcut, no unavailable stock, blocked target, fainted battler or full storage.
An eligible native legendary-roamer single battle is supported. Special-format,
full-storage and failed-save controls have compiled ARM coverage; their broad
native gameplay acceptance is not claimed complete.

SELECT + L now opens Enhancements in the field in either button order. Release
both buttons before using the menu. Physical L works even with native L=A mode.
Milestone 29 and older use SELECT alone.

The serial full regression suite passes 314 tests (665.389 seconds). Targeted
settings and quick-ball suites pass 50 and 13 tests. Native melonDS checks cover:

- Both games: previous saved preferences, command UI, real Ultra Ball capture,
  normal capture/party EXP, PC identity and original ball, one-ball stock cost,
  native saving and cold restart with Ultra Ball remembered.
- HG: a failed Poke Ball, no capture EXP on failure, next-turn UI/quantity update,
  touch cycling and successful touch throw. An immediately following native
  wild contact was escaped before saving; it is not mistaken for a failed catch.
- SS: seven hardware cycles, R throw, normal Bag selection/Use and last-ball
  tracking without a quick throw request.
- Native SELECT+L both games, held-button/release and order controls; actual
  native Options L=A selection and shortcut in HG. These earlier 30c shortcut
  checks exercise the unchanged shortcut source; they are separate from 30h
  quick-ball captures.

The final milestone-30 ROMs and patches exactly reproduce the 30h experiments.
Read-only verification: `.venv/bin/python -B scripts/verify_quick_ball_milestone.py`.
Evidence: `enhancements/milestone-30-verification.json`. This is bounded Mac
verification using the existing owned test-save lineage (HG-derived progress in
SS), not a fresh SS story playthrough, physical hardware test or final release.
No RAM fixtures were used in the accepted 30h cases.
