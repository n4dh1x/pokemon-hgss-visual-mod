# Encounter rate

Open SELECT, press X for page 2, and choose Encounter rate. Normal is the default.
Save and close applies the choice; B/Cancel discards staged edits on every page.

| Choice | Ordinary walking/surfing rate parameter | Visible spawn interval |
|---|---|---|
| Normal | Original | 60 free field input updates |
| Off | No ordinary random encounters | Disabled; existing wilds removed |
| 1/4 | 25%, integer truncation | 240 updates |
| 1/2 | 50%, integer truncation | 120 updates |
| 2x | 200%, capped at 100 | 30 updates |

The update counter advances only in the native free-input field loop, so menus
and scripts pause spawning. These are not display frames. The number of wilds
is still selected separately by Visible wilds (Few/Some/Many). Encounter rate Off
clears only owned transient wilds, including an early A interaction before the
next free-input cleanup. A generated Pokemon keeps its full identity into battle.
Native Repel filtering still applies. Turning Visible wilds Off independently
retains ordinary random encounters unless Encounter rate is Off.

The rate applies to ordinary random walking and surfing encounters, including
native cave walking; cave/water visible models are not implemented yet. Fishing,
Rock Smash, Headbutt, Sweet Scent and scripted encounters keep their native paths.
Partner, Safari, contest and Pal Park checks are excluded. Native wandering
legendary selection remains at its native rate even with this ordinary rate Off;
it still uses native Repel and battle bookkeeping. The separate optional Grass
battles: Roaming only setting continues to suppress every hidden grass-step
battle, including that native legendary branch. Visible legendary sprites remain
pending, so Normal grass policy is needed for their original hidden path.

## Native behavior and evidence

The existing guarded land/surf rate call wraps the original routine. Normal
forwards exactly one original call. A custom choice first uses the original rate
and legendary selection, retaining a successful selected pointer for the native
caller to consume once. Otherwise it performs the scaled ordinary roll and
caches no legendary, so an ordinary success cannot reroll a legendary. Custom
choices intentionally consume additional RNG; Normal retains its original call
sequence. Scaling occurs after native lead ability, held-item and flute effects,
before the original movement/tall-grass/radio/turn-step gates. It does not promise
an exact multiplier of battles after all HGSS gates and probability caps.

Visible generation bypasses this chance gate and scales its interval once, so
rate changes do not multiply twice or reroll an existing wild's PID/IVs/form.
No additional ROM hooks or save blocks are required. Slot 9/presence bit 6 extend
the same owned CRC journal; old records default Normal and unknown values survive.

147 regression tests pass. They execute the actual original rate and legendary
routine bytes from both USA baselines with bounded API fixtures, check exact
thresholds/caps and selected-pointer preservation, and reject altered native
fingerprints. Compiled field tests cover identity, intervals, Off cleanup, native
special-context delegation and stale interaction. Settings tests cover every
choice, wraparound, legacy defaults, unknown preservation and failed writes.

Bounded Mac melonDS gameplay checks cover both games' menu choices, cold Off/2x,
Cancel, visible spawn intervals and actual Off walking checks. No RAM edits are
used in these current-ROM runs. They import the project's existing native save
copies, including HG-derived progress for SS; they do not establish general save
interchangeability. Exact candidate and run hashes, inputs, screenshots and
assertions are in [milestone-15-verification.json](../enhancements/milestone-15-verification.json).

Actual Surf/cave/special-area visits and active legendary gameplay still need
acceptance. These experimental candidates do not complete the full enhancement goal.
