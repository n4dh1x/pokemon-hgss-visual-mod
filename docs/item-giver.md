# Native all-pocket item giver

Press SELECT in free field play, X three times to reach Cheats, page 4, then
choose the sixth row, Item giver. The picker has Pocket, Item, Quantity, Give
item and Back. Up/Down selects a row; Left/Right or A changes the first three
values. A on Give item adds the selected amount. B/Back returns to Cheats.

All eight HGSS pockets are supported: Items, Medicine, Poké Balls, TMs/HMs,
Berries, Mail, Battle items and Key items. Quantities are 1/5/10/50/99. Keys always
use one and reject an already-owned copy. Native Bag routines enforce pocket
capacity, one stack per item, maximum 999 generally and 99 for machines, and
normal machine/Berry sorting. Failure leaves inventory intact and gives feedback.
Native Bag permissions and full save ownership are rechecked before giving.

Picker choices stay staged until Save and close applies enhancement settings.
Main-menu B/Cancel discards those staged choices. Giving changes game progress
immediately; cancelling settings does not remove items already given. Use the
game's normal Save command to retain inventory. Saving only settings and cold
booting loads the saved picker choices with the older native game inventory.
The menu explicitly reminds the player that native saving keeps given items.

## Native resources and responsiveness

Only IDs 1–536 with a real native parameter mapping, matching pocket and valid
native name can be selected. Twenty-three unused mappings, empty names and names
starting with the placeholder question mark are skipped. The picker includes
named special/legacy records present in HGSS data; it does not grant associated
quest flags or make every item usable in every story/context. Native use rules
still apply. Native English item names retain their original DS characters.

Repeated item-file scans initially delayed pocket changes and missed quick input.
The accepted implementation derives a 269-byte packed pocket lookup from each
independently audited ROM: two four-bit pocket IDs per byte, 15 for invalid.
The builder verifies mapping, item-data and name-bank hashes, inserts the derived
table and checks its exact payload bytes. Generated lookup binaries live only in
ignored temporary build directories. No game assets are committed. Item naming
and actual Bag operations still use the original routines. Idle picker updates
do not reload names or repeat giving.

Native instruction guards cover the complete item loader/attribute/name region,
Bag arithmetic/sorting/getters and the mapping table. Native item data and English
name bank 222 remain unchanged. Private giver operations never add Pokemon,
change party/storage, charge money or set story variables/flags.

Twenty switches and three picker preferences occupy four pages with 6/6/4/6
entries plus Save/Cancel. Values 25/26/27 and presence bits
262144/524288/1048576 store pocket/item/count; older journals default 0/0/0 and
preserve every earlier choice. Item 0 selects the pocket's first valid item when
opening. Unknown later slots remain intact. Journal version 1, 48 values,
256-byte pages, 1,060-byte settings state and 32-byte loader header are unchanged.
Auxiliary/menu/item-giver state sizes are 68/144/28 bytes. The 28,012-byte payload
ends at `0x01FFFD6C`, leaving 660 bytes in the current ITCM reserve.

## Verification

294 regression tests pass, including twelve native item-giver tests and 47
settings checks. Original Bag instructions execute for all pockets/quantities,
999/99 stack caps, unique keys, sorting and full Items/Balls/Key pockets filled
with distinct valid records. Native metadata/name/permission services are bounded
in those instruction tests. The derived lookup matches all 537 native records
in both games. Both final ROMs and patches reproduce their fixed 28b experiments.

Mac melonDS DS 1.3.1 acceptance in both games covers:

- Real giving in every pocket, with exact quantities and only intended stack
  changes. All five quantities occur; keys force one even with 99 selected.
- Duplicate-key rejection, native Potion saturation at 999 and machine saturation
  at 99, without a partial write after a rejected attempt.
- Exact untouched party bytes, hatch/score counters, currencies, profile, Dex,
  story variables/flags and gameplay RNG during direct menu giving.
- Default picker values from an older twenty-option journal; staged Save/Cancel
  and normal settings/game-save separation verified through cold boot.
- All eight given stacks and picker choices surviving normal game saving and
  cold boot, with earlier enhancement choices retained.
- The original Bag showing the saved Potion stack; normal native Potion use
  restores the lead from 28/36 to 36/36 and consumes one Potion (10→9).
- Native saving/cold boot retaining the consumed stack, healed HP and Pokemon
  identity, IVs, ability, moves, PP, experience and nickname.

Accepted cases use real inputs without RAM fixtures. Source saves are the
declared HG-derived project lineage with earlier legendary/location/ball-fixture
ancestry and milestone-27 Dex actions. The earlier 28a file-scanning picker and
its intentionally stopped pre-optimization regression run are excluded. Only
28b candidates and the fresh complete 294-test suite support this milestone.

Normal field return after settings Save allows native NPC activity and RNG
advancement; untouched RNG is asserted for direct giving while the field is
paused. Native reload can change the HG lead's raw storage bytes while every
inspected decoded field remains equal. Whole-party byte preservation is not
claimed for every native reload or ordinary item-use effect.

Actual full-pocket saturation, restricted-map UI, broader item/quest effects,
TM teaching and further story/long-play acceptance remain pending. These are
experimental candidates; the full enhancement goal is unfinished. See
[exact evidence](../enhancements/milestone-28-verification.json). Recheck accepted
local cases with `.venv/bin/python -B scripts/verify_item_milestone.py`.
