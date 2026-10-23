# IV / EV summary viewer

Enable IV / EV viewer on page 2 of the SELECT enhancement menu. It defaults On.
On a Pokemon's native Skills summary page:

- Y cycles normal stats, IVs and EVs.
- L shows EVs (0..255).
- R shows IVs (0..31).
- SELECT restores normal stats and the original ability description.

X changes enhancement-menu pages. X and Y remain available with the native L=A
button option, which hides shoulder buttons. Native A actions remain intact.

The six numbers retain HGSS's order: HP, Attack, Defense, Sp. Atk, Sp. Def,
Speed. The small HP label becomes EV or IV and the description area explains
the range and controls. The ability name stays visible. Native page, party and
touch controls restore normal stats before acting; changing Pokemon resets the
view. Off keeps the native screen and controls. The chosen view is session-only;
the enable/disable setting is saved.

## Implementation and evidence

Two guarded ARM9 call sites wrap the original input handler and stats renderer.
The viewer uses the native summary Pokemon selector, GetMonData for party/raw
Pokemon, and GetBoxMonData for PC-box sources. It never writes Pokemon values or
the native cached stats. Standard native number/text/window routines render the
new views. The fixed HP-label window is only two tiles wide, so EV and IV fit
without overlapping the HP bar. Native refreshes always restore HP, including
touch navigation. Normal stats retain their original ability description.

135 regression tests pass, including original encrypted-data getters for real
party/raw and PC-compatible box data, native accessor order, data preservation,
input priority, touch refresh, On/Off/legacy persistence and both USA hook guards.
The crypto tests use the local ROM-matched native summary checkpoint; no game
assets or save data are distributed with the tests.

Bounded Mac melonDS checks cover both games: IV/EV/normal rendering, a second
Pokemon's own IVs, navigation, cancellation, saved Off and On after full core
restart, and encrypted party bytes unchanged after returning to the field.
The read-only inspector independently executes original getters on a private RAM
copy and rejects ROM mismatches or inactive custom views:

```sh
.venv/bin/python -B scripts/inspect_summary_state.py \
  --run local_data/verification/hg14d-summary-cycle \
  --report build/candidates/heartgold-visual-plus-gameplay-milestone-14.json \
  --rom build/candidates/heartgold-visual-plus-gameplay-milestone-14.nds
```

Actual PC storage UI, eggs and additional special contexts still need gameplay
acceptance. PC-box native accessor tests alone do not prove that full UI flow.
Exact candidate/run hashes and fixture provenance are recorded in
[milestone-14-verification.json](../enhancements/milestone-14-verification.json).
These builds are experimental; the whole enhancement goal remains incomplete.
