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
- Ten ROM-free tests pass, including upstream release tests and new option
  coverage/duplicate/new-option detection.
- Baselines have not been tested interactively in an emulator or on hardware.
- No new gameplay enhancement has been hooked into a playable NDS build.

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

## First gameplay implementation: visible grass encounters

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
