# Shiny odds

Open SELECT, press X for page 2 and choose Shiny odds. Native 1/8192 is the default.
Save and close applies it; B/Cancel discards staged changes.

| Label | New eligible Pokemon selection |
|---|---|
| 1/8192 | Original game, no extra RNG calls |
| 1/4096 | Up to 2 total PID rolls |
| 1/1024 | Up to 8 total PID rolls |
| 1/256 | Up to 32 total PID rolls |
| 1/64 | Up to 128 total PID rolls |
| Always | Select a shiny PID satisfying the caller's constraints |

The boosted labels are nominal, as in Emerald. Multiple rolls do not produce an
exact reciprocal probability, and native constraints such as Cute Charm can
already affect the original distribution. Selection stops on the first shiny.
Nature stays the same on the wild nature path; the gender-constrained path also
keeps its original gender and any explicit Unown-letter constraint. Native
ability/stat/IV/move initialization happens once from the selected PID. Extra
rolls naturally advance RNG before those new values are generated.

Visible wilds roll when created. Their whole generated Pokemon is retained for
contact; entering battle does not roll again. Changing the option leaves existing
wilds, party members and boxes unchanged. The native XOR<8 shiny test is not
patched globally. A captured shiny keeps its PID/IVs and shininess through normal
party storage and saving. Its ordinary met/capture data is filled by native code.

## Creation scope

Four guarded calls wrap native initialization from wild nature creation,
wild gender/nature/letter creation, starter selection and script GiveMon.
The original creator and other call sites stay intact. Eggs, trades, trainer
teams, UI preview mons, fixed/preset personalities and stored native roamers
remain native. New native roamer creation currently uses its preset-OT path and
is also unchanged; further adaptation/acceptance is tracked in the inventory.
This is not a patch to every fixed or scripted special Pokemon.

Unloaded settings or a trainer owner mismatch uses native creation. The option
does not enable custom odds before a valid active trainer/settings context.
Original naturally shiny PIDs are kept without extra rolls. Always enumerates
the finite 524,288 native shiny PID possibilities from a randomized starting
point, avoiding an unbounded until-shiny loop even with a stuck RNG. Constraint
failure is counted and retains the original PID; no such failure occurred in
the all-nature/gender/all-Unown-letter tests or observed gameplay.

## Verification and remaining work

159 tests pass, including actual native nature and Cute Charm caller instructions
from both USA ROMs, exact roll budgets, early stop, owner/default/preset/fixed
guards, initialization once, constrained PIDs and mutation rejection. The
original egg/trade/trainer/roamer calls and native creation/shiny routines remain
byte-identical. Tests of those exclusions are not full story/egg/trade playthroughs.

Both Mac games display all six labels and cold-load native, 1/64 and Always.
The observed 1/64 runs use 128 rolls per non-shiny generated wild. Existing shiny
spawns remain identical after selecting native odds; Cancel preserves the whole
cartridge save. A read-only inspector executes the original native data/shiny
getters on private snapshot copies and rejects ROM mismatches:

```sh
.venv/bin/python -B scripts/inspect_wild_shiny_state.py \
  --run local_data/verification/hg16a-contact1 \
  --report build/candidates/heartgold-visual-plus-gameplay-milestone-16.json \
  --rom build/candidates/heartgold-visual-plus-gameplay-milestone-16.nds
```

Both games reach real shiny Hoothoot contact battles with exactly the retained
236-byte enemy. Native catches, nickname decline, capture EXP, field storage,
native game saves and cold reloads retain the caught PID/IVs/shiny flag. Capture
checks seed only a declared four-byte slot (10 Poke Balls) in an isolated native
Bag before battle setup copies it. No Pokemon, HP, EXP or story values are edited.
The test saves were empty of balls; empty-bag and late-seeded attempts are recorded
as diagnostics and excluded from capture acceptance. SS uses HG-derived project
test progress, not a fresh SS playthrough or a general save interchange guarantee.

Field sprites still need palette correction and sparkle. A true native object
shiny parameter does not establish that its displayed palette is shiny; observed
Hoothoot field sprites still use ordinary colors while battle sprites are shiny.
Full starter/gift, newly released roamer, egg/trade exclusions and additional
species/forms/abilities require gameplay acceptance. The full enhancement goal
remains incomplete. Exact hashes, inputs, fixture ancestry and observations are
in [milestone-16-verification.json](../enhancements/milestone-16-verification.json).
