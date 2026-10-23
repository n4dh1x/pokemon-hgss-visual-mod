# Native enhancement settings — milestone 04

Press SELECT while normal field input is available. The native DS window offers
Visible wilds (Off/Few/Some/Many), Trade evolution and Reusable TMs. Use Up/Down
to choose, Left/Right or A to change a value, and A on Save and close to apply.
B or Cancel discards staged changes. Milestone 06 adds the fourth option, Repel
prompt (On/Off); see [repel-prompt.md](repel-prompt.md). Milestone 08 adds EXP for catching; milestone 10 adds Party EXP Share. Both are
saved On/Off options and default On for legacy records. Milestone 12 adds Field HMs and Grass battles on a second page; L/R switches
pages, retaining staged values. Save and close applies both pages atomically.
The eight-option menu uses 16-pixel row spacing. The rest of the audited enhancement list remains in scope.

The menu uses HGSS's field task, window, font and input routines. NPC movement
pauses while it is open, and prior NPC pause flags are restored on exit. The
visible-wild field lock also freezes in-progress native walking. The regular
party follower keeps its original system. The TM teaching hook calls the native
consumption routine when Reusable TMs is Off, and retains the item when On.
HM and itemless teaching paths retain their original behavior.

## Persistent record

The builder checks both USA games' native extra-save allocation table and
size/access routines. Main data occupies at most 35 sectors per 256 KiB bank;
the six native extra chunks end at bank offset `0x2ED60`, including footers.
The enhancement journal uses one 256-byte page at `0x3F000` and one at `0x7F000`
in the original 512 KiB save. Native save blocks, checksums and chunk sizes are
unchanged. The game's full save-erasure operation erases these pages too.

Records contain magic, version, sequence, full trainer ID, 48 value slots,
reserved words and CRC-32 over the first 252 bytes. Milestone 06 activates value
3 for Repel prompt and reserved word 0 bit 0 to distinguish an explicit Off from
legacy zero padding. Legacy records default the new option On. Unused value slots
do not constitute implemented enhancements.
The newest valid record belonging to the current trainer is loaded. Defaults
without a valid owned record are On trade evolutions, On reusable TMs and Few
visible wilds, with Repel prompt On.

Writes alternate pages, read back and compare the result before updating runtime
options. A failed or partial write leaves the previous valid page available.
Sequence comparison handles wraparound. Uniform FF or zero pages count as blank,
covering cartridge erasure and emulator initialization. Occupied unknown/future
formats are preserved; unavailable storage leaves the menu open with an error.
Settings save immediately when applied; game progress still uses the normal
Save command. No existing player save was supplied, so general older-save
compatibility has not been established.

## Verified scope

Milestone 04 passed 53 tests; milestone 06 passes 75. The observations below
record the original milestone 04 scope. Native ARM settings tests exercise CRC damage,
ownership/version rejection, sequence wrap, alternating writes, zero/FF blank
pages, interrupted writes, cancellation, NPC flag restoration and deferred Apply.
The actual native teaching function executes through the runtime wrapper with
both option values in each USA game, including HM and itemless cases. External
game APIs in instruction tests are controlled fixtures; full teaching/evolution
UI flows remain pending.

On Mac melonDS DS 1.3.1 with isolated project-created save copies:

- HeartGold saves Many/Off/Off and cold-boots with those values. Its first Apply
  changes only the 256-byte first journal page. Cancel after staging Some leaves
  the whole cartridge save unchanged and reopening shows Many.
- HeartGold then saves Off/On/On to the other journal page and removes all wild
  objects. A normal native game Save preserves both journal pages; a cold boot
  still loads Off/On/On.
- Corrupting the newer journal CRC in a separate test copy makes HeartGold load
  the older valid Many/Off/Off record without overwriting the damaged copy.
- SoulSilver loads the stored values, renders the menu, applies Some to the
  second page, then Many to the first. Four and six active moving wilds are
  observed respectively, with no allocation failures in these short runs.
- Both games show six active roaming wilds in Many. This Route 29 test is not a
  stress test of six distinct species, all maps, long sessions or all transitions.

ROM/state hashes, input sequences and bounded memory diagnostics are recorded in
[milestone-04-verification.json](../enhancements/milestone-04-verification.json).
Source/save/ROM/state/screenshot artifacts remain local and ignored. SoulSilver
tests use a copy of the project-created HeartGold fixture; they do not establish
a fresh SoulSilver story playthrough or universal save interchangeability.

Milestone 08 adds the fifth setting, EXP for catching. It defaults On for legacy
records and persists explicit Off using value 4 and reserved word 0 bit 1. The
native menu grows to seven rows including Save/Cancel and fits the DS screen.
The journal version, page size and flash offsets remain unchanged. The current
suite passes 85 tests. See [capture-experience.md](capture-experience.md).

## Milestone 10 storage extension

Journal value 4/reserved word 0 bit 1 stores capture EXP; value 5/bit 2 stores
party EXP. All three presence bits preserve legacy defaults and explicit Off
without changing the journal version, length, ownership or CRC. Unknown values
and reserved bits survive writes. Both games show the six options, cold-reload
Off and On, and retain rewards after native game saving. The regression suite
passes 95 tests. See [party-experience.md](party-experience.md).


## Milestone 12 extension

Page 2 has Field HMs (On/Off, default On) and Grass battles (Normal/Roaming only,
default Normal). The short page skips empty rows when moving to Save/Cancel.
Cancel on either page discards all staged values. Roaming only applies when
visible wilds are enabled in regular grass. Turning visible wilds Off restores
native random encounters even if Roaming only remains selected.

Journal values 6 and 7, with reserved word 0 presence bits 3 and 4, store these
options. Legacy records get defaults; unknown values and bits survive writes.
The fixed loader configuration remains 32 bytes; the extra runtime options use
separate resident storage. Journal version, page size, ownership and CRC are
unchanged. Both games render page 2 and cold-reload Roaming only. Native ARM tests
cover cross-page staging/cancel, write failures and legacy/unknown preservation.
