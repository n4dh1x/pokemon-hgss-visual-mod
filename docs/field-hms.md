# Field moves without learning the move

On page 2 of the SELECT enhancement menu, Field HMs defaults On. Contextual
scripts and native Surf/Waterfall input checks can choose a party member without
requiring a learned HM move. An actual learned user takes priority; otherwise a
compatible non-egg species is preferred, falling back to the first non-egg party
member. Native field use can select fainted members. No moves, HP, badges or
story flags are edited by this enhancement.

Native scripts retain their badge/story gates, prompts and animations. HGSS has
Cut, Fly, Surf, Strength, Whirlpool, Rock Smash, Waterfall and Rock Climb; Flash
is TM70 and Dive is absent. Complete per-move acceptance remains in progress.

## Bag use for Fly and Flash

Milestone 13 adds USE NOW beside the ordinary USE action on owned HM02 and TM70
in the normal field Bag, when Field HMs is On. USE keeps the native teaching
flow. USE NOW checks item ownership, party eligibility and the original native
field-move restrictions, then asks for confirmation. No/B returns to the Bag.
Yes rechecks the conditions before handing off through the real native start-menu
task. Fly opens its native destination map and uses the selected party member;
cancelling this Bag-launched map returns to the Bag. Flash uses its original
darkness/Ruins checks and native field script. Neither item is consumed by field
use. Off preserves ordinary TM/HM behavior and removes the extra action.

The native menu has five bounded action slots. The implementation reuses an
unassigned USA action slot and gives its replacement string to the native Bag's
existing cleanup. It does not enlarge the party menu. The Bag reads the native
start-menu field-check snapshot because its field overlay may be unloaded;
calling terrain routines from that overlay while the Bag is active is unsafe.
The one-shot confirmed intent is consumed before the actual native use callback,
which receives the correct StartMenuTaskData environment. Badge/party/item
changes at the handoff fail back to the Bag without teaching or consuming an item.

## Verification scope

135 regression tests pass. Native ARM tests execute original Fly/Flash checks,
the actual native use callbacks and selected-destination Fly return. They cover
badge/location/companion/costume/Safari/Pal Park/link-room restrictions, Flash's
darkness/Alph checks, confirmation/cancel, stale intents and cleanup. Both USA
ROMs accept exact guarded hook bytes; unrelated components remain unchanged.
Real unchanged personal data covers all eight HM indices and TM70 compatibility.

Bounded Mac gameplay evidence and explicitly declared isolated item/badge
fixtures are in [milestone-13-verification.json](../enhancements/milestone-13-verification.json).
Milestone 14 additionally verifies actual Flash in Dark Cave in both games: native
weather changes from 11 to 12 and the illuminated area expands. A native save and
cold reload preserve weather 12, so another Flash correctly fails there. Leaving
and re-entering through the real entrance resets weather 11 and allows Flash
again. The native item quantity remains unchanged and the selected party member
does not know Flash. See [milestone-14-verification.json](../enhancements/milestone-14-verification.json).

The initial isolated cave checkpoint uses declared temporary native warp-routing
data, restored before testing. The current candidate cold-loads its native save
and repeats entrance transitions and Flash without any RAM fixture. Earlier
TM70/HM02 and Storm Badge fixture provenance remains recorded.
Complete contextual HM coverage, actual Alph effects and broader
transitions/save acceptance remain pending. This is an experimental candidate,
not completion of the full enhancement goal.
