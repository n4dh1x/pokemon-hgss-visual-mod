# EXP for catching — milestone 08

The fifth SELECT setting controls capture EXP and defaults On for older option
records. A confirmed normal wild capture runs HGSS's EXP task before Pokédex,
nickname and storage handling. It uses native participation/held EXP Share rules,
formulas, item bonuses, EV calculation, EXP bar, level-up and move-learning code.
Party-wide EXP Share remains separate work. Off preserves native capture behavior.

The capture wrapper waits at the native confirmed-catch delay. It creates a
separate native SysTask and 0x58-byte GetterWork allocation while the catch parent
waits. Native EXP completion destroys only that child, then restores the catch
context before the original task resumes. Allocation/task failure resumes the
original capture. Tutorial, trainer, link and special battle formats are excluded;
normal wild, double-wild and roaming formats are eligible. An alive non-egg
participant is required before native EXP division. Failed balls never reach the
confirmed-catch point. Broad double/roamer and failure flows still need emulator
verification.

Original EXP, EV and Pokemon crypto routines are retained. The only new overlay 12
edit is its guarded capture callback pointer. Config word 6, journal value 4 and
reserved word 0 bit 1 add a durable option while preserving legacy defaults and
explicit Off. Unknown future journal fields remain preserved.

## Verification

All 85 project tests pass without skips. Compiled ARM tests cover parent/child
ownership, single execution, context restoration, disabled/special formats,
egg/fainted/missing participation, allocation/task failure and right-side double
target selection. Native EXP completion instructions execute for both USA games;
callback guards reject altered code and component checks reject unrelated edits.
Journal tests exercise legacy defaults, explicit Off/On and invalid values.

Mac melonDS DS 1.3.1 software runs use isolated project-created save copies:

- Both games render the fifth option and successfully capture an ordinary wild.
  HG displays 16 EXP from a level-2 Rattata; SS awards 24 EXP from a level-3 Hoothoot.
  Native EXP tasks complete, Dex registration appears, nickname is declined and
  the original capture task stores the Pokemon and returns to the field.
- HG's Chikorita changes from 135 to 151 EXP with one Speed EV; SS changes from
  135 to 159 EXP with one HP EV. Native saved-party getters read those values
  after battle return; each party gains its captured Pokemon.
- Both games save Off in the native menu and load it after a cold boot. Actual
  disabled capture controls store the Pokemon without changing Chikorita's EXP/EVs.

Declared RAM fixtures seed three Master Balls and clear the pre-existing Repel
counter only in isolated test checkpoints. No catch-rate or reward formula is
patched. Original saves/states remain untouched. All ROM/save/state/RAM/screenshots
stay local and ignored. A reproducible native getter inspector is available as
`scripts/inspect_party_state.py`; it executes original getters on a private RAM
copy and requires a matching candidate ROM/report. Detailed bounded hashes and
inputs are in [milestone-08-verification.json](../enhancements/milestone-08-verification.json).

## Remaining acceptance

Native code reuse does not establish every flow. Level-up, new moves/forgetting,
evolution/cancellation, failed throws, held EXP Share/Lucky Egg, level 100, full
party/PC storage, double/roamer capture, special-area story flows and save/reload
after these rewards remain pending. Battle presentation and long sessions need
further checks. The inventory remains `integrated_untested` for full acceptance;
the complete enhancement goal remains active.
