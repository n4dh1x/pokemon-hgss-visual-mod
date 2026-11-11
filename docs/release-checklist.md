# English HGSS Enhanced release checklist

Scope revised 6 November 2026 from the user's explicit clarification. This is the
current release checklist; the 59-row Emerald audit remains a historical source
comparison, not a list of 59 features that must be newly implemented.

## Required scope

- English USA HeartGold and SoulSilver with Visual+ retained.
- Actual gameplay improvements and useful interface improvements.
- Keep native HGSS 3D maps, battle scenes, followers, controls and story mechanics.
- Mac melonDS / RetroArch first. Use emulator fast-forward, normal audio/timing
  and FPS tools rather than adding matching ROM settings or 3DS-specific pacing.
- Keep existing camera angle/zoom controls and Visual+ artwork.
- No extra language variants, voxel/classic renderer switch, tilt-shift blur,
  world-map battle renderer, stereoscopy/depth, 400-pixel UI/widescreen conversion
  or Emerald Home Menu forwarder. These are excluded, not unfinished features.
- Retain HGSS follower interactions; no Emerald-specific item-finding rules.

## Implemented enhancements: wider acceptance still required

The inventory records 28 integrated rows, including the retained native shop controls. `integrated_untested` is the historical
label for integration with incomplete full acceptance; targeted tests and native
emulator checks are recorded separately. It does not mean every feature has no
tests, or that all contexts have passed.

- Moving visible wild Pokemon using native follower walking animations;
  Off/Few/Some/Many density, native Repel filtering, retained battle identity,
  cave/Surf support and bounded native legendary-roamer support.
- Optional contact-only regular grass encounters; Normal remains the default.
- Shiny field colours, repeating glints and one appearance chime.
- Capture EXP and party-wide EXP Share.
- Level-40 trade evolution alternatives and reusable TMs.
- Field HM use without learning the move, retaining native eligibility gates.
- IV/EV viewer and repeat-Repel prompt.
- World-clock speed and HUD; follower On/Off; camera angle and zoom.
- Encounter rate and shiny odds controls.
- Always catch, instant victory, fast eggs and infinite money.
- Johto Dex completion, National unlock/completion and item giver.
- Persistent enhancement settings.

Shiny field effects are part of the visible/shiny rows. Native HGSS options and functionality are retained separately.

## Recent milestones and remaining feature work

- Milestone 30 verified native quick ball throws, cycling, normal Bag use and
  last-ball persistence. SELECT + L opens Enhancements in the field.
- Milestone 31 adds the read-only trainer, badge and party overview on Y and
  the event gift catalogue. Both builds passed native queue activation,
  save/restart and overview checks. See [Event gifts](event-gifts.md).
- The native Buy screen passed touchscreen ±1, ±10 and wallet-limited
  purchases in both games. Exercise the native Bag's Sell and Toss touch
  controls in the release builds.
- SoulSilver's native event runs reached Sinjoh Ruins and completed the
  Spiky-eared Pichu award through a cold reload. Verify the Sinjoh reward,
  Celebi, the Enigma Stone, later catalogue batches and HeartGold story paths.
- Milestone 33 lets players select one gift at a time. The picker rejects
  already-owned and already-queued Pokéwalker courses. Verify native course
  delivery and complete the wider event checklist.
- The catalogue includes all Gen I–IV Mythical species and selected unique
  event gifts. Continue checking unique-gift coverage against the scope.

## Remaining release verification and delivery

- Finish native teaching flows, bag presentation, trade evolution and cancellation.
- Exercise all HM contexts, badge/story checks, animations and transitions.
- Broaden visible encounters across maps, species/forms, all densities, Repels,
  capacity, special encounters, shiny effects, transitions and longer play.
- Broaden EXP move-learning/evolution, held-item and special-battle checks.
- Exercise IV/EV UI in PC/egg contexts, follower transitions, world clock,
  camera/culling, shops, giver/Dex/story restrictions and cheat On/Off controls.
- Verify normal save/cold restart, old enhancement journals and existing HGSS
  save compatibility without changing unrelated progress. This is not a promise
  of arbitrary HG-to-SS interchange or GBA/Emerald save compatibility.
- OpenHome 1.17.1 opens populated raw 512 KiB saves for both titles. The
  independent milestone-31 SoulSilver save shows the delivered Mew in Box 1.
  Both games cold-booted saves edited by the headless OpenHome v1.18.1
  storage writer. Retest the final builds and check GUI write-back and
  transfer between saves using disposable copies.
- Finish independent SoulSilver story progression and general long-play checks.
  Most earlier SoulSilver runtime evidence uses a HeartGold-derived lineage.
- Complete Mac melonDS/RetroArch checks and publish reproducible patches, build
  instructions and final local NDS outputs. A local builder already exists;
  remaining work is release packaging/validation, not a new Emerald PAK system.
- Continue tested commits/pushes and cleanup after every build. Keep original
  ROMs and saves unchanged; never commit ROMs, saves or generated game assets.

Physical hardware has not been tested and is not the primary acceptance target.
This scope change removes irrelevant work; it does not mark untested gameplay
or the final release complete.

## Audit accounting

All 59 historical rows remain for traceability: 28 scoped enhancement rows
(28 integrated with broader acceptance still open), 17 retained-native rows, 3 emulator-provided rows,
2 delivery/compatibility rows and 9 excluded rows. The follower-interaction row
is retained-native even though its old audit state says `not_integrated` for
Emerald-specific differences. Never count those excluded or retained differences
as missing release enhancements.
