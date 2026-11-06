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

The inventory records 25 integrated rows. `integrated_untested` is the historical
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

Shiny field effects are part of the visible/shiny rows, not extra rows in the
25-row count. Native HGSS options and functionality are retained separately.

## Remaining feature implementation / completion

1. **Quick ball throw:** finish native R/touch throws, L/Y and touch cycling,
   normal Bag interaction and saved last-ball behaviour. Current development
   code has targeted tests and partial native verification; not yet an accepted
   milestone or final build.
2. **Shop quantity controls:** add the useful quantity-selection improvement;
   retain HGSS shop screens and native purchase/sale rules. No exact Emerald
   artwork/layout copy is required.
3. **Save overview:** add a useful combined trainer/badges/party overview around
   native saving; no exact Emerald save-card styling is required.

The SELECT + L enhancement-menu shortcut is implemented in development and has
bounded native verification. The last accepted milestone 29 uses SELECT alone.
The shortcut must be included in the next accepted build.

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
- Validate both USA games independently. Existing SS evidence uses HG-derived
  progress; a fresh SS story playthrough and general long-play acceptance remain.
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
(25 integrated, 3 unfinished), 17 retained-native rows, 3 emulator-provided rows,
2 delivery/compatibility rows and 9 excluded rows. The follower-interaction row
is retained-native even though its old audit state says `not_integrated` for
Emerald-specific differences. Never count those excluded or retained differences
as missing release enhancements.
