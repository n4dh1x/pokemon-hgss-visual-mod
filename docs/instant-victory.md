# Saved native Instant victory

Press SELECT during free field play and X three times for Cheats, page 4.
Instant victory defaults Off. When On, an eligible opposing Pokemon faints before
ordinary action selection. Native fainting, EXP, replacement Pokemon, prize money
and battle-result scripts still run. Native trainer switch prompts still ask you
to keep battling or switch. Disable this option to catch wild Pokemon or choose
normal battle commands; Always catch does not prevent an automatic faint.

Ordinary and trainer battles, wild doubles/partners, legendary roamers and contest
flags are eligible. Link, facilities, Safari, Pal Park, tutorials, recordings and
unknown formats remain ordinary. A missing/changed trainer owner also uses the
original path. Special-format gameplay acceptance remains pending beyond the
compiled guards.

## Native handoff

The installer changes two original controller table pointers: new-battle setup
clears interrupted work, and selection input handles the optional faint. Before
starting, all selection states must be untouched, the player's battler must be
alive, and native faint/EXP work must be clear. Native menu overlay 10 yields to
battle overlay 7 using the original loader helper, as normal action selection
does. This matters for replacement-ball animations and battle rendering.

The original UpdateHP script receives a negative HP amount and its passive-update
flag. It updates the health bar and native party copy and queues fainting. The
original faint, EXP, outcome and replacement helpers finish before another
opponent is considered. Native context cleanup returns to trainer messages and
entry abilities without advancing ordinary turns or ticking field/status timers.
The enhancement never writes a battle win result, prize amount or trainer flag.

A fresh native battle clears interrupted state even when both heap addresses are
reused. Work already started finishes through the native helpers before checking
whether another faint should be injected. Owned settings gate new injections.
The complete native table, helpers and original scripts are fingerprinted
independently in both USA baselines.

## Settings

Value 22/presence bit 32768 stores Off/On in the existing version-1 journal. Missing
presence ignores old padding and defaults Off. Unknown later values/bits survive,
readback must succeed before runtime changes, and all four pages apply together.
There are eighteen options with 6/6/4/2 rows. Save applies; B/Cancel discards.
Game progress still uses the normal Save command.

## Verification and limits

237 tests pass. Nine instant-victory cases cover owner/format/input/queued-work
constraints, original faint and EXP dispatch, repeated and double-target selection,
interrupted context reuse, failed fingerprint checks, and the original overlay
handoff with controlled loader APIs. Forty-one settings cases include legacy
padding, invalid records, unknown fields, atomic retry, Cancel and page navigation.
The original native calculator/helpers run on private instruction-test copies;
external game services remain controlled where stated.

Both exact candidates and patches reproduce the corrected native experiments.
Mac melonDS DS 1.3.1 acceptance uses isolated native project progress. Actual
roaming wilds retain the same 236-byte enemy identities in matched On/Off controls.
On grants native rewards without spending HP/PP; Off waits for normal commands
and fleeing grants no rewards.

A declared trainer fixture redirects an existing native field script through
TrainerBattle for Youngster Mikey, checks the native win result, conditionally runs
the native trainer-flag command, then resumes its original continuation. It changes
35 unused stack bytes plus one four-byte pointer. No trainer team, Pokemon, HP,
move, reward, coordinate or save flag is written by the fixture. Original trainer
factories generate Pidgey level 2 and Rattata level 4.

Both games complete automatic faints, native switch prompts, replacement send-out,
EXP and field return. Ordinary Off controls use Razor Leaf twice. Both award
70 participant EXP, 34 EXP to each of four bench members and 64 money, with the
native 150% trainer modifier retained. On keeps all PP; Off spends two Razor Leaf
PP. The native win result permits the declared script to set Mikey's defeat flag.
Native saving/cold reload preserves rewards, PP, payout, flag and explicit choice.
Cancel preserves the whole save. Previous seventeen-option saves retain Always
catch On and default Instant victory Off.

These are bounded VM-initiated trainer cases, not a real NPC story playthrough.
SoulSilver uses HG-derived project progress. Wider trainer/story, doubles/partners,
roamer/contest, volatile statuses/abilities, capacity, level/evolution and long-play
acceptance remain pending. Early experimental builds that missed the native
overlay handoff are excluded from acceptance. The full enhancement goal is still
unfinished. See [exact evidence](../enhancements/milestone-24-verification.json).
