# Enhancement implementation status

## Verified on 23 October 2026

- Fork: https://github.com/n4dh1x/pokemon-hgss-visual-mod
- Branch: `emerald-feature-parity`.
- Both supplied ROM ZIPs contain clean 128 MiB USA dumps, matching the upstream
  Visual+ source SHA-256 checksums and NDS game codes (IPKE and IPGE).
- Both `full` Visual+ reference builds match the upstream output SHA-256 exactly.
- All eight upstream patch binaries match their recorded checksums.
- Inventory contains 59 feature rows and covers all 41 distinct Emerald option
  keys across `3ds_extras.c` and `3ds_settings.c`.
- 111 tests pass, including compiled ARM field logic and independently checked
  field hooks for both games, plus the prior TM/evolution/loader tests.
- Milestone 03 adds native grass spawns that roam with follower model animations.
  Both games reach visible contact battles with the exact stored 236-byte Pokemon
  in the native enemy party. In HeartGold, a wild contacted a stationary player.
- The current 12,260-byte resident payload, recorded ARM9/overlay changes and xdelta
  round trips are checked. Unrelated NitroFS, ARM7 and banner data are unchanged.
- HeartGold wild positions and movement phases stay identical across 600 frames
  in the party menu and resume afterward. Native saving filters the two transient
  objects; a cold reload recreates wilds without saved NPC ghosts.
- Milestone 04 adds a native SELECT settings menu and durable journal for visible
  wilds, trade evolutions and reusable TMs. Both games show six moving wilds in
  Many; SoulSilver also shows four in Some. HeartGold Off removes all wilds.
- Both games load saved values. HeartGold Cancel preserves the whole save; native
  Save preserves both journal pages, and damaged-newer-copy recovery passes.
- Milestone 05 verifies native Repel use after spawning in both games: seven and
  four blocked unsolicited contacts, with retained-identity battles in matched
  unprotected controls. HeartGold deliberate contact under Repel also passes.
- Both games cross Route 29 to New Bark Town with old-map wilds cleared. HeartGold
  returns to grass, filters low-level spawns and regenerates fresh identities in
  a separate declared simulated-expiry copy.
- Cave/water support, full mode/capacity/transition/Repel coverage and sparkle/spawn
  effects remain pending. No complete visible-encounter parity claim is made.
- Reusable TMs and trade evolution now have saved runtime controls; full teaching
  and evolution/cancellation flows and bag quantity labels remain pending.
- All remaining new enhancements are still included in the persistent goal.
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
[emerald-parity.md](emerald-parity.md). IV/EV display has donor code and remains unmerged. Capture EXP is now integrated
with bounded verification in milestone 08.
The repeat-Repel prompt is integrated with bounded verification in milestone 06. Reusable TMs and trade evolutions are integrated as described below. No estimate is
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

## Milestone 02: level-40 trade evolutions and resident code

`native/evolution.c` wraps the original USA evolution routine in both games.
At level 40 or above, ordinary trade evolutions become level-up alternatives;
held-item trade evolutions still require their matching item. Normal trades
continue to work. A qualifying held item selects Slowking over Slowbro for
Slowpoke; other native evolutions remain fallback behavior. Everstone retains
the native Kadabra exception. The native successful-completion path removes
trade items; eligibility checks never remove them.

`tests/test_trade_evolutions.py` executes the actual hooked and original ARM
instructions with controlled game API fixtures and native ROM evolution tables.
It checks every trade entry, level boundaries, items, eggs, Everstone, normal
trading, disabled config, stone-use arguments and all non-trade species. It
also executes native held-item cleanup. Full evolution/cancellation UI has
not yet been exercised in the emulator.

The injector adds a small ITCM autoload section and advances the SDK arena
start beyond it. It verifies original instructions, loader layout and exact
recorded changes. See [native-integration.md](native-integration.md) and
[milestone-02-verification.json](../enhancements/milestone-02-verification.json).

## Fresh gameplay verification fixture

A new isolated HeartGold game has progressed through starter selection and
Pokegear acquisition with normal input. Chikorita and its native follower were
observed in Visual+. The game saved through its native Save menu; a cold boot
with the exported 512 KiB cartridge save showed Continue and restored the map,
player and follower. Save/state/screenshot data remains local and ignored.
Hashes and bounded observations are in
[field-fixture-verification.json](../enhancements/field-fixture-verification.json).
This checks normal early-game compatibility, not full TM or trade-evolution flows.

The emulator harness now records button/touch inputs, exports cartridge RAM and
accepts an isolated copy with `--load-save`. Loading a cartridge save and a
savestate simultaneously is rejected. Imports require exactly 512 KiB and a
matching core memory size; savestates still require an exact ROM hash.

```sh
.venv/bin/python -B scripts/smoke_libretro.py \
  --rom build/candidates/heartgold-visual-plus-gameplay-milestone-02.nds \
  --output local_data/verification/reload-example \
  --load-save local_data/verification/hg02-save-05/cartridge.sav \
  --frames 2400 --press A:1810:1814 --press START:1970:1974
```

`--touch X:Y:START:END` targets the lower 256x192 DS screen in the fixed
top-bottom layout. The fixture save was created for this project; no existing
player save was supplied or modified. A gameplay fixture is not a guarantee
of compatibility between every future build and every older save.

## Milestone 03: moving native grass encounters

See [visible-encounters.md](visible-encounters.md) for behavior, hooks, bounded
verification and remaining acceptance cases. Source and detailed evidence are
recorded in [milestone-03-verification.json](../enhancements/milestone-03-verification.json).
The normal build command now produces milestone 08 candidates for both games.
Previous experimental revisions remain local under ignored `build/experiments`.

## Milestone 04: native settings menu and durable controls

See [enhancement-settings.md](enhancement-settings.md) for controls, the audited
flash journal, corruption recovery, runtime TM behavior and verification limits.
Detailed bounded evidence is in
[milestone-04-verification.json](../enhancements/milestone-04-verification.json).

## Milestone 05: Repel and connected-map cleanup

See [encounter-refinements.md](encounter-refinements.md) for native level rules,
protected/control emulator comparisons, current-party behavior, deliberate contact
and map ownership. Declared test fixtures seed only isolated checkpoints; the
simulated expiry does not verify the complete natural wear-off dialogue.
Detailed evidence is in
[milestone-05-verification.json](../enhancements/milestone-05-verification.json).

## Milestone 06: same-type repeat Repel

The fourth saved option defaults On, including migration from the older three-option
journal. Native successful bag use records the last Repel type in the normal game
save. Wear-off offers only that same type, with Yes/No and inventory rechecking.
Both games pass natural 200-step expiry after native saving and a cold reload;
accepted and declined prompts, all three item durations, saved Off and no-substitution
fallback are also checked. Early native A interaction now checks map/mode/context
eligibility before a wild battle. Seventy-five tests pass. Special-area restrictions
and the broader inventory remain pending. See [repel-prompt.md](repel-prompt.md) and
[milestone-06-verification.json](../enhancements/milestone-06-verification.json).

## Milestone 07: native bag restrictions for repeat Repel

The prompt now follows native bag inhibition: Safari permits bag use; the
Bug-Catching Contest, Pal Park and Battle Tower partner room do not. Normal
bag unlock and map inhibition come from the guarded native helper. Acceptance
rechecks permission and shows a clear refusal without consuming an item if it
changed. All 78 tests pass, including actual USA normal-menu/Tower instructions.
Both games pass full 200-step saved expiry again. Matched isolated bag-locked
states show the native wear-off message; normal states offer and consume only
Super Repel. HeartGold also refuses after access is revoked during the prompt.
Full visits through each special-area story flow remain pending. See
[milestone-07-verification.json](../enhancements/milestone-07-verification.json).

## Milestone 08: native capture EXP

The fifth saved option defaults On and adds native EXP and EV rewards after a
confirmed capture, before Dex/nickname/storage. A separate native EXP task keeps
the capture parent alive, then restores its context. Both games complete capture
and field return with the expected EXP/EV values; saved Off survives a cold boot
and has actual capture controls. All 85 tests pass. Level-up, move-learning,
evolution, failed balls, held-item and full double/roamer flows remain pending.
See [capture-experience.md](capture-experience.md) and
[milestone-08-verification.json](../enhancements/milestone-08-verification.json).

## Milestone 09: capture level-up, moves and native save persistence

This expands verification of the unchanged milestone 08 ROMs. HG earns 135→151→
167→183 EXP over three captures; SS earns 135→159→191 over two. Both reach level 6,
show native stat screens and learn Razor Leaf into an empty slot with 25 PP.
Normal game saving and a cold restart preserve the complete captured party,
EXP, EVs, HP, level, moves and PP. Native saving preserves both options journal
pages. The read-only native party inspector now reports moves/PP. Full movesets,
evolution, held-item, failed-throw and wider capture cases remain pending. See
[capture-progress.md](capture-progress.md) and
[milestone-09-verification.json](../enhancements/milestone-09-verification.json).

## Milestone 10: party-wide EXP Share

The sixth saved option adds full EXP for each healthy participant and half for
healthy bench Pokemon, without double rewards from a held EXP Share. It reuses
native bonuses, EVs and progression, with one appended owned group message.
Both games pass normal victories, actual Off controls, saved On/Off cold reload
and native saving/reloading of rewards. SoulSilver also passes combined party and
capture EXP through nickname/storage. All 95 tests pass. Extended bench progression,
multiple-participant, held-item emulator and battle-format cases remain pending.
See [party-experience.md](party-experience.md) and
[milestone-10-verification.json](../enhancements/milestone-10-verification.json).

## Milestone 11: bench levels and multiple participants

On unchanged milestone-10 ROMs, bench members reach level 3 through native
individual stat screens. HeartGold switches to Rattata: both participants gain
full 16 EXP, and the two Hoothoot gain half 8. SoulSilver's isolated shared fixture
advances all three bench members with 8 each. Both native game saves cold-reload
all rewards, stats, moves and PP, preserving both option journal pages. No new
RAM/Pokemon/EXP/item fixture edits are used. Full bench move/evolution and wider
battle acceptance remain pending. See [party-progress.md](party-progress.md) and
[milestone-11-verification.json](../enhancements/milestone-11-verification.json).


## Milestone 12: optional contact-only grass and contextual HMs

The eight saved settings use two pages (L/R changes page). Grass battles defaults
to Normal at all visible densities. Roaming only blocks regular grass walking
battles while native generation, walking and retained contact encounters continue.
Visible Off restores native encounters. Both games save and cold-reload the new
option. Native legendary roamers still need visible support; their hidden grass
branch is suppressed when this option applies. Water/caves/special contexts keep
their native behavior. See [visible-encounters.md](visible-encounters.md).

Field HMs defaults On, allowing contextual HM-user fallback without editing moves.
The script command and Surf/Waterfall input checks are integrated; native badge
and story scripts are retained. Instruction tests cover both ROMs and real personal
compatibility data. Live checks execute on Mac; complete field-use animations and
Fly/Flash menu access remain pending. See [field-hms.md](field-hms.md).

111 tests pass. Exact build hashes, bounded Mac runs and limitations are recorded
in [milestone-12-verification.json](../enhancements/milestone-12-verification.json).
The full enhancement goal remains active; these are experimental candidates.
