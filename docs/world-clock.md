# World clock and optional field HUD

Press SELECT in the field, then X twice for page 3. World clock cycles through
1x, 6x, 12x, 24x, 60x and 120x. Show clock controls a small time-and-speed display
on the top field screen. Defaults are 1x and HUD Off. Save and close applies all
three pages together; B/Cancel discards staged choices. The live preview shows
the currently applied clock, so a staged speed takes effect only after Save.

The world clock controls native outdoor lighting/daypart, time-dependent wild
encounter selection, time-based evolution checks and the encounter preview.
HGSS's original species tables, evolution rules and lighting assets remain in
use. Existing visible wilds retain their generated Pokemon when time changes;
new spawns use the current world time. The native Pokegear clock still reports
the real RTC. Calendar dates, daily events and RTC penalty bookkeeping continue
through the original game code, independently of accelerated world time.

Returning to 1x keeps the accumulated world-time offset. Game saving stores the
clock anchor after successful native saving. While the game is closed, a shifted
clock resumes at 1x, with no accelerated offline Berry bonus. A backward system
clock rebases the anchor without reversing world time. Settings also save an
anchor when applied; use the normal game Save for current progress and time.

## Berry Pots

The original Berry update applies real elapsed minutes. A separate bonus adds
only the extra active-session time at the selected speed, through the native
Berry growth routines. The bonus is consumed once. It can accumulate while the
app is closed and is applied when the app updates. Native modal menus defer the
idle update until they close.

Returning from the Bag settles the bonus for existing plants before calling the
native planting routine. This prevents a new seed receiving time accumulated
before it existed. Growth, moisture, stage transitions, harvest and mulch rules
otherwise remain native. Offline real-time growth still uses HGSS's RTC rules.

## Persistence and HUD lifecycle

The version-1 journal remains 256 bytes with 48 value slots and the original
ownership/CRC/alternating-page checks. Slot 12/presence bit 512 stores speed;
slots 13..17/presence bit 1024 store world seconds, RTC anchor, shifted flag and
bonus minutes/seconds. Slot 18/presence bit 2048 stores HUD On/Off. Missing fields
default safely, unknown later fields survive, and failed writes do not apply
staged options. Native save block layouts and checksums retain their format.

The HUD retains one native window/string during idle field input and redraws
only when time or speed changes. It releases both before native field tasks,
menus, battle setup or field teardown. Area-name banners defer it until their
shared background finishes scrolling. Original task-constructor assertion,
arguments, field assignment and return value are preserved by a guarded hook.
The clock also respects the original frozen-photo time state.

## Verification

The regression suite passes 203 tests, including compiled ARM clock arithmetic,
all six speeds, midnight rollover, owner/frozen-photo guards, original daypart
readers, forward/backward RTC, offline resume, overflow bounds, journal failures,
menu staging and retained HUD lifecycle. A planting test verifies growth-before-
seed ordering, unchanged native arguments and one-time bonus consumption. Both
ROMs independently check every callsite/context; native RTC/calendar code stays
byte-identical. See the exact acceptance results and limits in
[milestone-21-verification.json](../enhancements/milestone-21-verification.json).

Both final ROMs reproduce the tested experiments byte for byte and pass xdelta
round trips. On Mac melonDS DS 1.3.1, both games render the HUD, retain it in idle
field input, and release/recreate resources around the party menu and the
Route 29–New Bark connection. Daytime Route 29 spawns are Pidgey/Sentret while
the real RTC is at midnight. SoulSilver also passes night Rattata contact/flee
with no HUD during battle.

Ten-byte isolated supply/registration fixtures provide Berry Pots and Oran
Berries. Native UI plants a fresh seed, then original native growth advances it
to sprout over 124 real RTC seconds. No pot, clock or Pokemon state is injected.
Native saving/cold reload preserves all four pots, all five party Pokemon,
EXP/EV/moves/PP and captured legendary records. A later cold RTC proves offline
time advances at 1x; extra bonus accounts only for active 120x time. Saved 1x/HUD
Off cold-loads without any HUD allocation, and Cancel preserves the entire save.
Native date, day count and penalty remain separate throughout the listed runs.
SoulSilver uses HG-derived project progress, not a fresh story playthrough.

These are experimental candidates. Broader time-based evolution, all timed
areas, Berry varieties/mulches/harvest cycles, special menus and long-session
acceptance remain part of the full unfinished goal.
