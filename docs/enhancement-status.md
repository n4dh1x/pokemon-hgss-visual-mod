# Enhancement implementation status

## Verified on 22 October 2026

- Fork: https://github.com/n4dh1x/pokemon-hgss-visual-mod
- Branch: `emerald-feature-parity`.
- Both supplied ROM ZIPs contain clean 128 MiB USA dumps, matching the upstream
  Visual+ source SHA-256 checksums and NDS game codes (IPKE and IPGE).
- Both `full` Visual+ reference builds match the upstream output SHA-256 exactly.
- All eight upstream patch binaries match their recorded checksums.
- Inventory contains 58 feature rows and covers all 41 distinct Emerald option
  keys across `3ds_extras.c` and `3ds_settings.c`.
- Fourteen tests pass in the project environment: inventory/release checks plus
  actual ARM instruction tests of TM teaching for both ROMs, all four move slots,
  HMs/itemless teaching, mismatch rejection and repeated-patch rejection.
- Both reusable-TM candidate ROMs pass xdelta round-trip verification. Only four
  ARM9 bytes differ from each Visual+ baseline; NitroFS files, overlays, ARM7 and
  banner remain identical.
- Both candidates complete 1,800-frame opening smoke runs with video/audio using
  the installed melonDS DS 1.3.1 core. HeartGold also advances to new-game help
  through button input. This is not a full teaching-flow test.
- Reusable TMs are build-time enabled in experimental milestone 01. Bag quantity
  labels and runtime toggle remain pending. Other new enhancements remain pending.
- No hardware test has been performed. Mac melonDS/RetroArch is the priority.
- The persistent goal covers the full audited scope, not only easy features.

## Local reference outputs

`build/baseline/heartgold-visual-plus-full-baseline.nds`

SHA-256: `eb0aaed35ba445f26a3fdfdc00c86ab8e1abac72b2191984f57290b383fb8379`

`build/baseline/soulsilver-visual-plus-full-baseline.nds`

SHA-256: `5b3a377d20b2aa45fa1b9e6fbab842aaddc75e4fef38c38624662c9f5e48bf8e`

These are Visual+ references, not builds containing the requested new gameplay.
Build result JSON files explicitly record `new_emerald_gameplay_features: false`.

The local xdelta3 3.2.2 macOS ARM64 release archive was checked against its
GitHub release SHA-256:
`27dcf763beb075ed28061ef136613f4bc6ea3999cb424f23a7d59f18ca2d7c8b`.
The tool and downloaded reference repositories are under ignored `local_data/`.

## Visible grass encounter integration target

Use HeartGold as the first integration target. The current hg-engine Makefile
accepts USA HeartGold only; SoulSilver requires its own hooks and validation.
The full Visual+ patch also modifies ARM9, overlay 1, overlay 12 and NARC assets,
so an entire engine patch cannot simply be applied on top of it.

Relevant verified source interfaces in the pinned `pret/pokeheartgold` tree:

- `src/field/encounter_check.c`: time-of-day tables, encounter generation,
  Repel/ability checks and `FieldSystem_CanGenerateStepEncounter`.
- `src/field/field_control.c`: field input, end-of-step and encounter checks.
- `include/map_object.h`: `MapObject_Create`, `MapObject_CreateWithParams`,
  `MapObject_Remove`, `MapObject_Delete` and saved-object synchronization.
- `src/follow_mon.c`: native follower behavior and species presentation.
- `include/field_system.h`: map-object manager, location, follower and task state.

Implementation acceptance: Route 29/30 wilds display the selected species and
level, launch the same generated Pokemon when interacted with or contacted,
respect Repels/collisions/follower, pause during scripts and menus, disappear
only when consumed or legitimately despawned, and never enter the saved NPC
object list. Test Few/Some/Many behavior, battle return, map edges and warps.
Then add cave/water encounters and all remaining edge cases in the inventory.

## Later phases

The complete ordered plan and per-feature differences are in
[emerald-parity.md](emerald-parity.md). Capture EXP, IV/EV display, reusable TMs
and Repel routines have donor code; they are not yet merged. No estimate is
claimed for full parity, and DS/3DS hardware differences are explicitly recorded.

## Milestone 01: reusable TMs

`gameplay/patches.py` verifies the exact teaching-function fingerprint independently
for both USA Visual+ full baselines, then replaces the `Bag_TakeItem` Thumb call
at `0x020825B4` with two Thumb-1 NOPs. `tests/test_reusable_tms.py` executes the
original and patched routines in Unicorn, observing external game calls. The
move, PP, PP-Up, friendship and mood paths are preserved. This narrow change
avoids enabling unrelated hg-engine mechanics or replacing Visual+ overlays.

`build_enhanced.py` builds from the supplied clean ZIP, verifies the baseline,
checks all unchanged components and verifies a clean-ROM xdelta reconstruction.
Candidate reports explicitly say `final_release: false` and
`runtime_gameplay_tested: false` until the full teaching flow is tested.

`scripts/smoke_libretro.py` uses an installed local melonDS DS core in software
mode with separate save/system directories under ignored `local_data/verification`.
It can save and resume ROM-matched checkpoints. Screenshots and memory/state
artifacts are local only. Software-rendered game opening frames and audio output
were observed in both candidates; no old player save was supplied or modified.
