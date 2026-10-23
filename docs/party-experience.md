# Party-wide EXP Share — milestone 10

The sixth SELECT option defaults On for older settings records. Every healthy
non-egg participant receives the full base EXP; every other healthy non-egg party
member receives half, rounded down with a minimum of one. Empty slots and fainted
Pokemon are skipped. Off restores HGSS's original participant/held EXP Share rules.

The native EXP task applies Lucky Egg, trainer and trade bonuses, EVs, level-up,
stat screens and move learning. A held EXP Share does not add a second reward
while party-wide sharing is On. Native level-100 behavior is retained. One message
says “The rest of your team gained EXP. Points!” for the bench; participant and
level-up/move messages keep their native presentation. Capture EXP uses the same
party distribution when both options are On.

## Integration and preservation

Three guarded overlay 12 edits route the EXP calculation, task callback and only
the gained-EXP message call. The capture child delegates to this same task wrapper.
Original participation masks and reward fields are restored between task ticks;
completion never reads the native allocation after it has been freed. A new task
at a reused address starts a fresh distribution and message session.

One owned English string is appended as message 1276 to battle bank 197 of
`a/0/2/7`. Every existing encrypted message and every other bank stays byte-identical.
The builder checks the complete original archive, relevant native code and the
recorded new archive. Reports contain hashes, never extracted message assets.
An independent check executes the pinned original C++ msgenc decrypt routines
and recovers the complete owned text from both built ROMs.

Config byte 28, journal value 5 and reserved word 0 bit 2 store the switch. The
32-byte configuration and version-1 journal retain their size. The native menu
uses 16-pixel option spacing for six options plus Save/Cancel; its diagnostic
state is 72 bytes. The new party EXP diagnostic state is 68 bytes. The payload is
11,120 bytes, ending at `0x01FFBB70`; the explicit Thumb/ARM veneer calls the SDK's
unsigned divider. Further options need additional runtime storage and menu pages.

## Verification on Mac melonDS DS 1.3.1

All 95 project tests pass with no skips. Compiled ARM checks cover full/half
recipients, eggs/fainted/empty slots, double-side masks, reused task addresses,
Off passthrough, collective-message suppression and capture context restoration.
Original HG/SS reward instructions execute through the wrapper for held EXP
Share, Lucky Egg, trainer/trade bonuses and level 100. The actual ARM SDK divider
executes across representative quotient cases. Journal tests verify migration,
explicit Off/On, invalid values and preservation of unknown fields.

Normal game input, without new RAM/Pokemon/EXP/item edits, establishes:

| Observation | HeartGold | SoulSilver |
|---|---|---|
| Ordinary victory, participating Chikorita | 183→207 (+24) | 191→207 (+16) |
| Bench rewards with sharing On | 8→20 for all three | 27→35 and 64→72 |
| Collective bench messages | One; two suppressed | One; one suppressed |
| Sharing Off, participating Chikorita | 183→207 | 191→207 |
| Bench EXP with sharing Off | All remain 8 | Remain 27 and 64 |
| Native game save/cold reload of earned rewards | Passed | Passed |
| Saved Off and saved On after cold restart | Passed | Passed |

Eligible recipients also receive native EVs: HeartGold's Hoothoot victory grants
one HP EV to each recipient; SoulSilver's Rattata victory/capture grants one Speed
EV. SoulSilver also completes a capture with both options On: the existing three
members gain 16/8/8 EXP before nickname/storage, while the newly caught level-2
Rattata enters the party with its original 8 EXP and no awarded EVs. Its Master
Ball came from the already declared milestone-08 isolated fixture. No new fixture
is used here. Native saving and cold reload preserve all four caught-party members,
rewards, HP, moves and PP. Old source saves/states remain unchanged.

The native party inspector now requires a settled field frozen with SELECT and
rejects implausible decoded fields. A frame during battle-to-field transition can
contain temporarily unsettled party data and is excluded from reward evidence.

## Remaining acceptance

This is an integrated candidate, with acceptance incomplete. Full bench move/evolution flows, multiple participating Pokemon in SoulSilver,
held-item cases in the emulator, repeated/double/roamer/special-area
battles, fainting/eggs in the emulator, and hardware remain pending. The combined
capture case is verified in SoulSilver; HeartGold's combined emulator case remains
pending. Prior capture-presentation and broader capture acceptance items remain.
One immediately opened post-battle menu showed a transient footer redraw artifact;
settled/cold-reloaded menus render correctly, and that transition needs follow-up.
The full Emerald enhancement set is not complete.

Bounded inputs, ROM/save/state/RAM/screenshot hashes and native party values are in
[milestone-10-verification.json](../enhancements/milestone-10-verification.json).

## Milestone 11 follow-up

Native bench level-3 stat screens and game-save/cold-reload persistence pass in
both games. HeartGold additionally switches participants during battle and awards
full 16 EXP to both, while each bench member receives 8. SoulSilver awards 8 to
all three bench members and advances each to level 3. The ROM code is unchanged;
see [party-progress.md](party-progress.md) and
[milestone-11-verification.json](../enhancements/milestone-11-verification.json).
