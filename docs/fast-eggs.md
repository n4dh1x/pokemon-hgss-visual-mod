# Saved five-step egg hatching

Milestone 25 adds **Fast egg hatching** on Cheats, page 4. Press SELECT in free
field play, X three times, then choose the third row. It defaults Off. Save and
close applies the choice; B/Cancel discards staging. Use the native Save command
to retain game progress.

When On, every five eligible native daycare steps prepares the first valid party
egg for hatching. Invalid/checksum-failed eggs are skipped. The enhancement sets
only the native egg-cycle field, then returns to the original field caller. The
caller increments the native hatch statistic/score and starts standard script
2021. Original application overlay 95 handles animation and the nickname prompt;
the native task applies egg status, trainer memo, species name, Pokedex and field
return. PID, OT, IVs, ability, moves and shininess are retained.

The original daycare step always executes first. Parent EXP steps, breeding
rolls/phone notifications, 230/255-step calendar cycles, Flame Body/Magma Armor
and normal ready-egg results remain. A naturally ready egg can hatch earlier.
Menus, waiting, blocked movement and turning alone do not call the native step
update. Some native map/event handling precedes that update; the five-step
counter measures eligible updates, not every coordinate change in every context.
Party reordering keeps walking progress. Off, no valid egg or ownership mismatch
resets it on the next update. The counter is session-only, as in Emerald's source;
loading a native save starts it at zero. Egg data and the saved choice persist.

## Integration

Both USA baselines independently match the complete native daycare routine,
calendar/ability helpers, valid-egg selector, hatch launcher and field handoff.
Only overlay-1 BL at `0x021E78A2` changes to the resident wrapper. Original
`HandleDaycareStep` at `0x0206CD1C`, selector at `0x0206CE44`, hatch launcher and
standard script remain unchanged. The selector already skips invalid eggs.

Nineteen settings occupy 6/6/4/3 rows. Value 23/presence bit 65536 defaults Off
for old journals; unknown later slots are preserved. The journal remains version
1 and 256 bytes with 48 values. Auxiliary state is 52 bytes, menu 128 bytes, and
fast-egg diagnostics 32 bytes. The 24,120-byte payload ends at `0x01FFEE38`, with
4,552 bytes left in the current reserved ITCM region. Both final ROMs and patches
reproduce their tested experiments, and unrelated-data/xdelta checks pass.

## Verification

247 regression tests pass, including eight native ARM egg tests and 43 settings
checks. Original daycare/selector instructions execute with controlled external
services for calendar, ability, breeding and invalid/multiple-egg cases.

Mac melonDS DS 1.3.1 acceptance in both games covers:

- Native-created Togepi eggs with identical On/Off bytes within each game.
- Four walking steps with unchanged eggs, then the fifth native hatch prompt.
- Original animation, nickname decline, custom SPARK entry and field return.
- Unchanged PID/OT/IVs/ability/moves/PP/shininess; native hatch count +1, score +27,
  friendship 120 and hatch memo applied by the original task.
- Native saving/cold reload of eggs, hatched Pokemon, custom names and choices.
- A saved four-step egg starting at zero after cold boot, remaining an egg after
  four new steps and triggering on the fifth.
- Cancel preserving the entire cartridge save and legacy eighteen-option
  journals defaulting this option Off while retaining previous choices.

The isolated native-VM gift fixture inserts GiveEgg(Togepi175, gift offset0) and
a jump back to the existing follower script: 12 unused script-stack bytes plus a
four-byte script pointer. It injects no Pokemon, egg cycles, coordinates, hatch
results or save flags. Source progress is the declared HG-derived project test
lineage, including earlier legendary-release/ball fixtures. No fresh story or
universal HG/SS save compatibility is claimed. Shiny Always is enabled in these
controls, but the native egg factory remains excluded; these eggs are ordinary.

Wider actual daycare breeding, other species/egg sources, cycling/Surf/forced
movement, transition/event edges and long-play acceptance remain pending. These
are experimental candidates and the full enhancement goal remains unfinished.
See [exact evidence](../enhancements/milestone-25-verification.json).
