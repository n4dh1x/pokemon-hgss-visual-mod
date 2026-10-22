# Native enhancement integration

This is a checked integration into the USA Visual+ full builds, retaining the
original engine and overlays. It does not apply an entire hg-engine ROM patch.
Both clean source hashes and baseline hashes are recorded in candidate reports.

## Resident memory

The original ARM9 autoload layout has a main section at `0x02000000`, an ITCM
section at `0x01FF8000` of size `0x620`, and a DTCM section at `0x027E0000` of
size `0x60` plus `0x20` BSS. `gameplay/native.py` checks this layout and the
code-settings offset `0xBA0` before modifying it.

The new autoload section starts at `0x01FF9000`. The linker rejects growth past
`0x02000000`. The injector also changes the audited SDK ITCM arena-start literal
at `0x020D2C68` from `0x01FF8620` to the payload end, preventing SDK allocations
from using the payload region. Original resident sections stay byte-identical.
This is a limited code region, not a general solution for every future renderer.

In milestone 02 the payload is 268 bytes, ending at `0x01FF910C`. Both emulator
RAM dumps contain that value in the runtime ITCM arena-low slot at `0x023FFDAC`.
The exact payload occurs once in each serialized emulator state and nowhere in
the dumped main RAM after startup, consistent with its resident ITCM load.
Both games reached the new-game help screen. This proves startup integration;
it does not prove every hooked gameplay flow has run successfully.

## Evolution hook and ABI

The injector checks the original evolution-context SHA-256 before replacing
the first sixteen bytes of `GetMonEvolution` at `0x02070E34`. The Thumb-1
absolute branch preserves arguments r0-r3, SP and LR. The original prologue is
relocated to `OriginalEvolution` at `0x01FF9021`, with another preserving branch
back to `0x02070E45`. Stone evolution tests specifically verify the item in r3
survives both branches.

The C wrapper uses native APIs at their audited USA addresses: GetMonData,
GetItemAttr and LoadMonEvolutionTable. It does not redefine Pokemon encryption,
save structures, evolution records on disk or the evolution animation task.
It preserves native evolution method 6 for held-item trades, allowing the
original successful-completion helper to perform item removal. Cancellation
flow still needs full emulator verification.

## Options and build

The first 32 payload bytes hold a versioned runtime configuration. Milestone 04
adds a SELECT field menu for trade evolutions, reusable TMs and visible encounters
(Off/Few/Some/Many). The teaching call now goes through a resident wrapper: On
retains TMs; Off calls the original Bag_TakeItem with its original arguments.
The older static patch remains available for regression comparisons only.
Defaults without a valid owned settings journal are On/On/Few. See
[enhancement-settings.md](enhancement-settings.md) for the audited flash layout,
CRC journal, recovery behavior and bounded emulator verification.

Build with ARM-targeting clang and LLD, plus `requirements-dev.txt`. Set
`HGSS_CLANG` or `HGSS_LLD` if automatic discovery cannot find the tools. The
build uses freestanding Thumb-1 code for ARM946E-S and records compiler/linker
versions, symbols and payload SHA-256 in each candidate JSON. It rejects
unrecorded ARM9 changes and verifies an xdelta reconstruction from the clean ROM.

The SDK arena behavior was inspected against `ntrtwl/NitroSDK` revision
`9eec6c92c9d7bba9350732b11296ed16aab3a8bc` (`libraries/os/src/os_arena.c`).
That source is an audit reference, not a linked payload dependency. The pinned
pokeheartgold tree's SDK wrap references a different SDK revision; actual ROM
instructions, layouts and runtime arena values are checked independently.

ARM routine tests use Unicorn with controlled external game APIs. ROM-backed
tests require locally built baselines and skip if unavailable; a ROM-free test
run alone must not be reported as complete gameplay verification. Full teaching,
evolution, cancellation, save/reload and later gameplay integration remain
required before a final release.

## Milestone 03 field code

The resident payload is now 4,336 bytes, ending at `0x01FFA0F0`. It includes
session-only wild slots and movement state. The original ITCM/DTCM contents stay
unchanged, and the SDK arena advances beyond this larger payload. New field
hooks replace five recorded ARM9 sites and six calls in overlays 1/2. Full
component verification rejects any other file, descriptor or ARM9 mutation.
See [visible-encounters.md](visible-encounters.md).

## Milestone 04 settings and field menu

The payload is 7,648 bytes, ending at `0x01FFADE0`. It now includes a native
window/task menu, runtime TM wrapper and two-copy settings journal state. It
uses the existing field hooks; the TM teaching BL targets the new wrapper.
The build guards the native flash allocation table and size/access routines
before enabling journal writes. Original ITCM/DTCM content remains unchanged.

## Milestone 05 contact and connected maps

The payload is 7,904 bytes, ending at `0x01FFAEE0`. The field code reads the
native Repel flag through guarded USA save APIs and scans the current party for
HGSS's first alive non-egg member before unsolicited contact. It preserves
deliberate contact. Object ownership now includes map ID; free field input
releases old-map objects on connected transitions. Two appended diagnostic
counters record blocked contacts and map releases; existing slot offsets remain
unchanged. See [encounter-refinements.md](encounter-refinements.md).
