# Native enhancement settings

Current milestone 24: press SELECT during free field play. X/R advances through
four pages; L goes back. Up/Down selects a row, Left/Right or A changes its value,
and A on Save and close applies all pages together. B/Cancel discards staged
changes. Always catch and Instant victory are on Cheats, page 4, and default Off. Game progress still
uses the native Save command. The sections below retain each milestone’s storage
and verification history.

## Original menu and integration

Press SELECT while normal field input is available. The native DS window offers
Visible wilds (Off/Few/Some/Many), Trade evolution and Reusable TMs. Use Up/Down
to choose, Left/Right or A to change a value, and A on Save and close to apply.
B or Cancel discards staged changes. Milestone 06 adds the fourth option, Repel
prompt (On/Off); see [repel-prompt.md](repel-prompt.md). Milestone 08 adds EXP for catching; milestone 10 adds Party EXP Share. Both are
saved On/Off options and default On for legacy records. Milestone 12 adds Field HMs and Grass battles on a second page; L/R switches
pages, retaining staged values. Save and close applies both pages atomically.
The original eight-option menu uses 16-pixel row spacing. The rest of the audited enhancement list remains in scope.

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


## Milestone 14 extension

Page 2 adds IV / EV viewer (On/Off), default On. Highlighting it shows the Skills
page's Y cycle and L/R controls. X changes menu pages; native L=A input mode
retains X and Y even though it hides both shoulder buttons. Its saved value is journal slot 8, with reserved word 0 bit 5
indicating an explicit value. Legacy records default On even if unused slot 8
contains arbitrary data. The normal six-argument store preserves unactivated
auxiliary values; the menu's atomic store applies all nine settings. Unknown
slots 9..47 and future reserved bits remain preserved. Journal version, size,
ownership, alternating pages and CRC stay unchanged.

The runtime auxiliary structure is now 12 bytes and the menu state is 88 bytes;
the fixed 32-byte loader header and evolution trampoline stay unchanged. Page 2
skips its three blank rows before Save/Cancel. Both games cold-reload explicit
Off and On, and cancelling a staged change preserves the entire cartridge save.
See [summary-viewer.md](summary-viewer.md).


## Milestone 15 extension

Page 2 adds Encounter rate (Normal/Off/1/4/1/2/2x), default Normal. Left and Right
cycle in both directions and A advances a choice; X changes pages. The four-row
page skips its two blank rows before Save/Cancel. Value slot 9 and presence bit 6
in reserved word 0 persist the option. Legacy unused slot 9 is ignored without
that bit. Unknown slots 10..47 and future reserved bits survive writes; invalid
explicit choices are rejected before any write. Old six-argument callers
preserve an existing explicit rate. Version, owner, page size and CRC are unchanged.

The auxiliary runtime structure is 16 bytes, the menu is 92 bytes, and the loader
header remains 32 bytes. Both games save all choices, cold-load Off and 2x, and
Cancel preserves the whole cartridge save. See [encounter-rate.md](encounter-rate.md).


## Milestone 16 extension

Page 2 adds Shiny odds as its fifth row. Left/Right cycle six choices and A
advances; the page skips its one blank row before Save/Cancel. Slot 10 and
reserved word 0 presence bit 7 (128) store an explicit choice 0..5. Legacy padding
without that bit defaults to native odds. Unknown slots 11..47 and future bits
survive; old six-argument callers preserve the saved shiny option. Invalid values
are rejected and failed writes do not apply staged odds.

The auxiliary structure is 20 bytes and the menu 96 bytes. The fixed loader header,
256-byte journal, count/version/owner/CRC and native save layout remain unchanged.
The owner getter validates the current trainer against the loaded journal before
applying extra rolls; unavailable or changed ownership uses native creation.
See [shiny-odds.md](shiny-odds.md).

## Milestone 20 option and journal extension

The current two-page menu has twelve options, six per page. Party follower is
page 2 row 6: On by default, Off to remove the native lead follower while visible
wilds keep roaming. X changes pages; both pages apply atomically. Value slot 11
and reserved-word-0 presence bit 256 encode hide_follower; absent bit defaults
native On even if legacy padding is nonzero. Unknown later fields remain intact.
The journal stays version 1 with 48 slots and the original 256-byte layout.
Native On/Off saving and cold reload pass in both games. See
[follower-control.md](follower-control.md).

## Milestone 21 clock options

The current menu has fourteen options on three pages. X/R advance and L goes
back; page 3 has World clock and Show clock, then skips unused rows before
Save/Cancel. All three pages apply atomically. The auxiliary runtime structure
is 32 bytes and menu state 108 bytes; the loader header remains 32 bytes.
Slot 12/bit 512 stores speed, 13..17/bit 1024 store the clock anchor/bonus, and
18/bit 2048 stores the HUD. The original journal format stays unchanged.
The live preview shows applied time. See [world-clock.md](world-clock.md).

## Milestone 22 camera options

Page 3 now has World clock, Show clock, Camera angle and Camera zoom. The four-row
page skips two empty rows before Save/Cancel. Camera choices apply after Save and
close; native menus temporarily use the map's original view. Values 19/20 and
presence bits 4096/8192 store pitch/zoom. Defaults are Visual+ and 100%; legacy
padding without the presence bits is ignored. The auxiliary structure grows to
40 bytes and menu to 116 bytes. The journal and loader header retain their
formats. See [camera-controls.md](camera-controls.md).


## Milestone 23: fourth page and Always catch

The menu exposes seventeen options across four pages with 6/6/4/1 option rows.
The fourth page, Cheats, starts with Always catch. It skips five empty rows before
Save/Cancel. X/R advances with wraparound; L goes back. X also works with native
L=A enabled. Save applies all four pages atomically.

Always catch uses value 21 and reserved-word-0 presence bit 16384. Missing presence
ignores legacy padding and defaults Off. Unknown slots 22..47 and future reserved
bits survive; invalid choices and failed readback never apply. Old six-argument
settings callers preserve the extra option. The auxiliary options occupy 44 bytes,
menu state 120 bytes and catch diagnostics 20 bytes. The fixed loader header,
version-1 journal, 48 values, ownership, CRC and native save allocation are unchanged.
Both games pass explicit On/Off native saving and cold reload, and cancelling
staged changes preserves the entire cartridge save. See [always-catch.md](always-catch.md).


## Milestone 24: Instant victory

Cheats page 4 now has Always catch and Instant victory, then skips four empty
rows before Save/Cancel. The menu exposes eighteen options across 6/6/4/2 rows.
All pages apply together. Instant victory defaults Off; when On, an eligible
opponent faints before normal action selection, so disable it when you want to
catch wild Pokemon or choose ordinary battle commands.

Value 22 and presence bit 32768 store the choice in the original journal. Legacy
padding without presence is ignored; unknown slots 23..47 and future bits survive.
Invalid choices and failed readback do not apply; older settings callers preserve
the value. Auxiliary options occupy 48 bytes and menu state 124 bytes, with instant
victory staged at offset 104, page at 108 and error at 112. The fixed loader and
native save layout remain unchanged. Both games retain saved On/Off, full native
trainer rewards and previous seventeen-option saves. Cancel preserves the entire
cartridge save. See [instant-victory.md](instant-victory.md).
