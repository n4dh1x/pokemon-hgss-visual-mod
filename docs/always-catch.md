# Saved native Always catch

Press SELECT during free field play, then X three times for Cheats, page 4.
Always catch offers Off (default) and On. Save and close applies the choice; B or
Cancel discards staged changes. The option is separate from shiny odds, encounter
rate, visible wilds and the ball you choose.

When enabled, eligible wild catches pass the native ball-shake comparisons.
The original battle RNG still advances once per requested roll. The ball remains
the ball actually thrown: native effects such as Friend Ball friendship, quantity
consumption, capture animation, Dex, party/storage and capture/party EXP continue
through the original routines. Native catch eligibility and trainer deflection
remain intact. This does not replace the ball with a Master Ball or skip the
successful-capture side effects.

Supported wild flags cover ordinary singles, double/partner wilds, Safari,
legendary roamers and Bug-Catching Contest. Trainer, link, Frontier and unknown
formats retain original rolls. Tutorial and Pal Park keep their original native
success path before the hook. A missing or changed trainer owner uses native rolls.
Actual special-format gameplay acceptance remains pending beyond instruction tests.

## Integration and persistence

The installer fingerprints the complete native shake calculator, RNG, battle-type
getter, caller and trainer-deflection gate independently in each USA baseline.
It changes only the RNG call inside that calculator. Original SDK division and
native shake math stay intact, including the low/zero adjusted catch-rate boundary.

Value 21/presence bit 16384 stores explicit Off/On in the existing version-1
journal. Legacy unused padding is ignored without presence; unknown later values
and bits survive. Readback must succeed before runtime changes. The fourth menu
page skips its empty rows before Save/Cancel. All pages apply together.

## Verification and limits

226 tests pass. Seven catch cases execute original calculators, native RNG and
SDK division in Unicorn. Only external base-stat/type/mon services and square-root
hardware are controlled. Both games cover failed Off rolls, four successful On
shakes and native Friend Ball friendship 200, RNG progression, supported/forbidden
flags, trainer ownership, HP/status/rate boundaries and immediate native successes.
Settings tests cover legacy defaults, explicit values, invalid choices, unknown
fields, atomic writes, failed writes and cancellation.

Both exact candidate images and patches reproduce the tested experiments. Mac
melonDS DS 1.3.1 acceptance uses the project's existing native-released Raikou with
its saved PID/IVs, level 40 and 125/128 HP. Nine new fixture bytes place that saved
roamer on Route 29 and supply three Friend Balls. No Pokemon, HP, status, player
coordinates, story flags or rewards are injected. Existing Repel is used through
the native Bag to isolate the high-level legendary; its roaming model moves and
contacts the player autonomously.

Both On runs succeed with four forced shake rolls. Both matched Off controls fail
with the first original roll and Raikou flees normally. Each consumes one actual
Friend Ball. Captures retain PID, IVs, shininess, moves, level, HP and status, set
stored ball 22 and friendship 200, clear the native roaming record and set its
captured flag. Capture EXP and party EXP complete once: the lead gains 1234 EXP,
each healthy bench member 617 EXP, including native level/move dialogs and
Synthesis replacing Tackle. Off controls receive no rewards or captured flag.

Ordinary native saving and cold reload preserve the captured Raikou byte for byte,
Friend Ball fields and EXP/EV/moves/PP in both games. The lead follower's native
mood resets from 127 to 0 on cold initialization; applying only that original native
setter to a private preboot copy exactly reproduces all 236 cold lead bytes.
No live data is changed by inspection. Both saved On/Off choices persist, and
Cancel preserves the entire cartridge save.

These cases do not establish all ordinary/Safari/contest/partner battles, every
ball, full-party/storage limits, positive legendary status, fresh story release or
long-session acceptance. SoulSilver uses HG-derived project progress, not a fresh
story or general save-interchange claim. The nine-byte supply/location fixtures
retain the declared native-release fixture ancestry from milestone 19. The full
enhancement goal remains unfinished; these are experimental builds.
See [exact evidence](../enhancements/milestone-23-verification.json).
