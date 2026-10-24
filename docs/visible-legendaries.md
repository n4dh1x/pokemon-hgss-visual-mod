# Native legendary roaming encounters

Milestone 19 lets the existing saved Raikou, Entei, Latias and Latios identities
participate in visible encounters. It does not release a legendary early or
create extra copies. The original native selection, active flag, location and
Repel rules still decide whether a saved identity is available.

The model keeps the native generated Pokemon, including PID, IVs, level, current
HP and status. A given saved identity can have only one owned model at a time.
If its saved record or map changes, the stale model is removed. Contact copies
the whole retained Pokemon into a native ROAMER battle (type 0x100), refreshing
the player's current party and Bag. Native battle code continues to handle
fleeing, HP/status persistence, capture flags and relocation.

Both native land encounter-start branches are intercepted during model
generation, including the legendary branch. Generation cannot silently start
a hidden legendary battle. With Grass battles set to Roaming only, contact with
the moving legendary remains available; the setting still defaults to Normal.

New native releases also honor the saved shiny odds. Their factory initially
uses the visible half of the trainer ID, but encounter reconstruction uses the
full owner ID. Selection therefore checks shininess against the final full ID
while leaving the original factory OT arguments and initialization intact.
Existing saved personalities are never rerolled. Genuine shiny models retain
the native alternate palette, star glints and one appearance chime.

## Verified scope

176 tests pass. Compiled ARM tests cover saved-record/pointer validation,
duplicate prevention, exact retained contact Pokemon and battle type, plus
stale HP/status/PID/active/map removal and early interaction guards. A hook test
requires every native encounter-start call in the original land generator to
be intercepted. New-release shiny tests cover all four species, final full OT,
default/fixed/wrong-owner guards and unchanged native arguments.

Both final candidates reproduce their tested experiment ROMs byte for byte,
with an 18,252-byte payload. Both pass baseline and hook fingerprints, bounded
recorded changes and xdelta round trips.

On Mac melonDS DS 1.3.1, both games show one saved shiny Raikou among six moving
wilds. Contact starts a native roamer battle with the exact retained 236 bytes,
PID 4226739189, the original IVs and 125/128 HP. Native Master Ball captures clear
the saved roaming record and set the native captured flag. Native saves and
cold boots keep the captured party member and do not respawn it.

Combined capture/party EXP completes: 1234 for Chikorita and 617 for each of three
bench members. Native stat screens, empty-slot move learning and Synthesis
replacing Tackle through the full-moveset forget UI succeed in both games.
Chikorita finishes at level 13 and all three bench Pokemon at level 8. EXP, EVs,
moves and PP match after native save and cold reload.

These tests use isolated project progress; SoulSilver uses HG-derived progress.
A declared native-script fixture releases Raikou through the original VM and
factory, rather than playing the full Burned Tower story. Five location bytes
place that native identity in the current map; four Bag bytes supply one Master
Ball before battle setup. No Pokemon, HP/status, EXP or engine-code bytes are
forged by these fixtures. A prototype's earlier hidden encounter is recorded
only as a native damage/flee/save control, not visible-model acceptance.

Runtime Entei/Latias/Latios, positive status, defeated/respawn story paths,
other species/forms, wider Repel/transition/capacity cases and long play remain
pending. This is an experimental milestone; the full enhancement goal remains
unfinished. See [exact evidence](../enhancements/milestone-19-verification.json).
