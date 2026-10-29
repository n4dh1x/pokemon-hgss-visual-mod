# Emerald 3DS v0.4.0 → HGSS + English Visual+ inventory

Audited 22 October 2026. Scope: every user-facing option in Emerald v0.4.0's SETTINGS, ENHANCEMENTS and CHEATS pages, plus its published interface/platform features. Historical bug fixes, tooling internals and Hoenn story content are not new HGSS gameplay enhancements. All 41 distinct serialized option keys are covered; item-giver subcontrols are grouped into one feature.

The fork contains upstream Visual+, this audit, native roaming grass encounters, reusable TMs, trade alternatives, repeat Repel, capture EXP, party-wide EXP Share and an eleven-option saved settings menu over two pages. **The final enhancement set is not complete.** Donor availability does not mean a feature is installed; the machine-readable inventory tracks integration and verification separately. Native HGSS equivalents are retained; differences in runtime toggles and presentation are called out.

Baseline: [Emerald v0.4.0](https://github.com/ZallaxDev/emerald-3ds/tree/v0.4.0), [Visual+](https://github.com/DosukaSOL/pokemon-hgss-visual-mod), [HGSS source](https://github.com/pret/pokeheartgold), [hg-engine](https://github.com/BluRosie/hg-engine). Exact audited revisions and source fingerprints are in [sources.lock.json](../enhancements/sources.lock.json).

## Categories

- **Already in base HGSS:** 16 feature rows.
- **Already in Visual+:** 0 feature rows.
- **Partly present / adaptation needed:** 10 feature rows.
- **Donor implementation available:** 4 feature rows.
- **Needs custom implementation:** 21 feature rows (including the user-added grass policy).
- **Emulator/platform equivalent:** 3 feature rows.
- **3DS-specific; no direct NDS equivalent:** 5 feature rows.

## Enhancements

| Feature | Base HGSS | English Visual+ | Category / work required |
|---|---|---|---|
| Game speed: 1x / 1.5x / 2x / 3x / 4x | Normal DS timing. | No speed setting. | **Emulator/platform equivalent**. Use melonDS fast-forward initially; a matching in-game speed menu is separate work, with DS hardware limits. |
| Real-time pacing | Native DS audio/timing, not the Emerald 3DS DSP-clock implementation. | Unchanged. | **Emulator/platform equivalent**. Use emulator audio/timing controls; do not transplant the 3DS-specific pacing code into DS. |
| EXP for catching | Not present. | Not added. | **Donor implementation available**. Native capture EXP/EV task and fifth saved On/Off option integrated. Both games pass capture, Dex registration, nickname decline, field return, saved-Off controls, level-6 stat screens, Razor Leaf learning into an empty slot and native save/cold reload of rewards. Finish full movesets/forgetting, evolution/cancellation, failed balls, held-item and full double/roamer capture verification. |
| Party-wide EXP Share | Held-item EXP Share only; not party-wide. | Not added. | **Needs custom implementation**. Milestone 10 integrates the sixth saved option, full EXP for healthy participants, half for healthy bench Pokemon and one group message. Native held-item/trainer/trade bonuses are retained without double sharing. Both games pass ordinary victories, actual Off controls and native save/cold reload; SoulSilver also passes combined capture EXP. Milestone 11 passes native bench level-3 stat screens and game-save/cold-reload persistence in both games, plus full rewards for two actual HG participants. Bench move/evolution, actual multi-participant SS and wider emulator acceptance remain pending. |
| Trade evolutions at level 40 | Trade requirements remain. | Not added. | **Needs custom implementation**. Milestone 02 adds level >=40 alternatives with native held-item completion. Milestone 04 adds the saved runtime toggle. ARM tests pass; full in-game evolution/cancellation remains pending. |
| Field moves without learning the move | Party must know the field move. | Not added. | **Needs custom implementation**. Contextual fallback and saved control integrated in milestone 12; milestone 13 adds owned HM02/TM70 Bag USE NOW, native checks and safe Fly/Flash handoff. Native badge/story scripts retained; full per-move acceptance remains pending. See [field-hms.md](field-hms.md). |
| Visible wild Pokemon: Off / Few / Some / Many | Random grass/cave/water encounters plus specific scripted overworld Pokemon; no general roaming-spawn system. | Not added. | **Needs custom implementation**. Native follower models walk as grass wilds retain their generated Pokemon into contact battles. Saved Off/Few/Some/Many controls are integrated. Milestone 05 adds current native Repel checks on unsolicited contact and map-aware cleanup; both games pass protected/control contact runs and Route 29 to New Bark transitions. Milestone 18 adds native encounter floors and Surf water, surface-bound movement, shore cleanup, retained cave/water battles and native Surf save/cold reload. Milestone 19 adds saved legendary identities, duplicate/stale guards and native ROAMER battle bookkeeping; both games pass shiny Raikou contact/capture/rewards/native save/cold reload. Finish other legendary species, full mode/capacity/map/party/Repel coverage and general spawn effects. Milestone 17 adds native shiny palettes, silent repeating glints and one appearance chime; both games pass mixed-colour and Off cleanup checks. |
| Grass battles: Normal / Roaming only (user addition) | Native random grass encounters. | Unchanged. | **Needs custom implementation**. Optional saved contact-only regular grass mode integrated; Normal remains default. Moving wilds retain exact battle identity. Native legendary-roamer sprites and wider acceptance remain pending. |
| IV / EV summary viewer | Stats shown; exact IVs/EVs not exposed as a summary page. | Not added. | **Donor implementation available**. Milestone 14 integrates a saved optional native Skills viewer: Y cycles stats/IVs/EVs, L EVs, R IVs, SELECT normal stats. Native party/raw/PC-box getters preserve data. Party views, touch/party navigation and saved On/Off controls pass in both Mac games. Actual PC-box UI and egg/special-context acceptance remain pending. |
| Use another Repel prompt | Wear-off message without this option. | Not added. | **Integrated; acceptance incomplete**. Same-last-type native prompt and saved On/Off option integrated. Both games pass native save/cold reload and natural 200-step Super Repel expiry, Yes/No and saved Off; all three durations and no substitution are checked. Native bag restrictions and acceptance rechecking are integrated, with compiled ARM and matched bag-locked emulator controls. Finish full special-area story visits and broader save/context acceptance. |
| Reusable TMs | TMs consumed; HMs reusable. | Not added. | **Donor implementation available**. Milestone 04 routes native teaching through the saved reusable-TM toggle in both USA games. ARM instruction tests cover On/Off, HMs and itemless teaching. Full teaching-flow validation and bag count presentation remain. |
| Running indoors | Indoor running is native; map-header runningAllowed is unused. Scripted movement restrictions still apply. | Retained. | **Already in base HGSS**. Retain HGSS behavior; do not bypass cutscene or movement locks to imitate the Emerald switch. |
| Physical / special move split | Native Gen IV mechanic, with move categories. | Retained. | **Already in base HGSS**. Keep HGSS mechanics; no conversion needed. Emerald's optional Gen III fallback is not needed for baseline HGSS. |
| Day / night outdoor lighting | Native time-of-day lighting and windows; its artwork differs from Emerald's lighting. | Retained. | **Already in base HGSS**. Keep HGSS native lighting. An Off/Auto override and exact Emerald-style extra lighting would be new optional work. |
| World clock: 1x / 6x / 12x / 24x / 60x / 120x | Uses real RTC; no independent accelerated world clock. | Not added. | **Needs custom implementation**. Milestone 21 integrates saved world time, native lighting/timed readers and active-session Berry growth. Native calendar stays separate. Broader gameplay acceptance remains; see [world-clock.md](world-clock.md). |
| Morning / day / night wild encounter tables | Native time-dependent HGSS encounters. | Retained. | **Already in base HGSS**. Preserve Johto/Kanto tables and modifiers; do not copy Hoenn species tables. Off/Timed override would be additional UI. |
| Show clock on map / bottom-screen HUD | Clock exists in Pokegear; not Emerald's always-visible map clock. | Not added. | **Partly present / adaptation needed**. Milestone 21 integrates optional top-field time/speed HUD and live menu preview. Native Pokegear RTC retained; wider layout/context acceptance remains. |
| Lead Pokemon follower | Native follower, interaction, cries, animations and held leaves/accessory-related behavior. | Retained. | **Partly present / adaptation needed**. Milestone 20 adds saved native Party follower On/Off, default On with legacy journal compatibility. Native permission and deferred lifecycle preserve party species/form/shiny initialization and wild-model independence. Both games pass walking/dialogue, On/Off native save/cold reload and Route29-NewBark round trip. Finish wider species/forms, cycling/Surf, story/partner/HM and long-play acceptance; audit item-finding differences separately. |

## Cheats

| Feature | Base HGSS | English Visual+ | Category / work required |
|---|---|---|---|
| Encounter rate: Normal / Off / quarter / half / double | Normal game encounter-rate modifiers only. | Not added. | **Needs custom implementation**. Milestone 15 adds saved Normal/Off/1/4/1/2/2x, ordinary walking/surfing scaling and visible cadence control. Off removes visible wilds. Original legendary decisions are preserved separately; fishing, scripted and special contexts remain native. Both Mac games pass menu choices, Off/2x cold reload, Cancel, visible intervals and ordinary Off walking. Surf/cave/special-area and actual legendary gameplay acceptance remain pending. |
| Shiny odds: 1/8192, 1/4096, 1/1024, 1/256, 1/64, always | Original odds and fixed scripted exceptions. | Not added. | **Needs custom implementation**. Milestone 16 adds saved nominal odds with 1/2/8/32/128 rolls and constrained Always for new wilds/starters/script gifts. Existing/fixed/egg/trade/preset paths remain native. Both games retain shiny PID/IVs into actual contact, capture, native save and cold reload. Milestone 17 adds native field palettes, repeating silent glints and one appearance chime; both games pass mixed shiny/ordinary and native contact checks. Milestone 19 adapts new native releases and verifies shiny Raikou retained contact/capture/native save/cold reload. Finish other legendary species/story and full starter/gift/egg/trade/species/form acceptance. |
| Always catch | Normal catch calculations. | Not added. | **Integrated; acceptance incomplete**. Milestone 23 adds saved default-Off guarantee at native ball-shake rolls, retaining native eligibility, ball effects and rewards. Both games pass Friend Ball Raikou On/Off, native friendship, capture/shared EXP, save/cold and Cancel. Broader ordinary/special formats and capacity acceptance remain; see [always-catch.md](always-catch.md). |
| Instant victory | Normal battle flow. | Not added. | **Integrated; acceptance incomplete**. Milestone 24 adds saved default-Off native automatic faints, overlay handoff and normal faint/EXP/replacement/outcome paths. Both games pass retained wild controls, declared native-VM trainer replacement/payout, ordinary Off controls, save/cold, Cancel and legacy options. Wider real NPC/story and special-context acceptance remains; see [instant-victory.md](instant-victory.md). |
| Fast egg hatching | Original egg cycles and ability effects. | Not added. | **Integrated; acceptance incomplete**. Milestone 25 adds saved default-Off five-step hatching through the original daycare/hatch sequence. Both games pass native gift-egg timing controls, animation/naming, native save/cold, Cancel and legacy journals. Wider actual daycare, species and special walking contexts remain; see [fast-eggs.md](fast-eggs.md). |
| Infinite money | Normal balance. | Not added. | **Integrated; acceptance incomplete**. Milestone 26 adds saved default-Off wallet refill on native reads, retaining the exact capped setter and Mom ledger. Both games pass native buy/sell/Cancel, Trainer Card, Mom trainer payout, save/cold and legacy settings. Casino coins and Battle Points stay unchanged. Wider shop/story/link acceptance remains; see [infinite-money.md](infinite-money.md). |
| Complete regional Pokedex | Normal Johto Pokedex progression. | Not added. | **Integrated; acceptance incomplete**. Milestone 27 adds confirmed native Johto completion for its exact 256 species, retaining normal form/language bookkeeping. Both games pass exact membership, unchanged progress controls, Cancel, native save/cold and original app totals/return with declared ownership fixtures. Wider forms/languages/story acceptance remains; see [pokedex-actions.md](pokedex-actions.md). |
| Unlock National Pokedex | Normal story unlock. | Not added. | **Integrated; acceptance incomplete**. Milestone 27 adds confirmed National unlock through both original Dex/profile upgrade flags. Both games pass exact flag-only change, Cancel and native save/cold. Story completion and Pokedex ownership flags remain native; wider acquisition acceptance remains. |
| Complete National Pokedex | Normal progression. | Not added. | **Integrated; acceptance incomplete**. Milestone 27 adds confirmed completion for 493 native HGSS species and both upgrade flags. Both games pass unchanged progress controls, Cancel, native save/cold and original app totals/entry/return with declared ownership fixtures. Wider forms/languages/story acceptance remains; see [pokedex-actions.md](pokedex-actions.md). |
| Item giver: pocket, item, quantity, give | Normal bag acquisition. | Not added. | **Needs custom implementation**. Add field-only item UI, valid item filtering, capacities and unique key-item checks; adapt all HGSS pockets. Quantities 1/5/10/50/99. |

## Settings

| Feature | Base HGSS | English Visual+ | Category / work required |
|---|---|---|---|
| 3D overworld / voxel toggle | Already uses 3D environment geometry and 2D character sprites. | Camera changes expose more existing geometry. | **Partly present / adaptation needed**. Keep native HGSS maps. An exact voxel replacement and classic/voxel toggle would require a separate renderer and asset pipeline. |
| Adjustable 3D camera angle | Native camera. | Full or 50%-blended camera table chosen at build time. | **Partly present / adaptation needed**. Milestone 22 integrates saved Visual+/34/37/40/43/46-degree native pitch with task/controller ownership. Broader map/cutscene acceptance remains; see [camera-controls.md](camera-controls.md). |
| Adjustable 3D camera zoom | Native fixed/game-controlled distances. | No independent zoom setting. | **Needs custom implementation**. Milestone 22 integrates saved 90/100/110/120-percent relative zoom and native projection handling. Lab round trips pass; wider culling/maps/runtime orthographic acceptance remains. |
| 3D tilt-shift blur: Off / 10-100% | No equivalent user-selectable postprocess. | Not added. | **Needs custom implementation**. Requires new DS rendering effect or emulator shader; DS VRAM/fill-rate feasibility must be measured. |
| Battles over the rendered overworld | Separate battle scenes with Pokemon sprites, not battles in the live field map. | Redrawn backgrounds only. | **Needs custom implementation**. Major rendering/camera integration; Visual+ backgrounds do not implement this. Pokemon remain sprites in Emerald too. |
| Stereoscopic world: Auto / On / Off | DS screens are not stereoscopic. | Not available. | **3DS-specific; no direct NDS equivalent**. Cannot provide native 3DS stereoscopy in an NDS ROM. Would require a different platform/renderer, not a DS patch. |
| Stereoscopic depth: 25-200% | No stereoscopic depth slider. | Not available. | **3DS-specific; no direct NDS equivalent**. Not applicable to native NDS hardware; emulator-specific stereo would be a separate project. |
| Show FPS | No player-facing FPS counter. | Not added. | **Emulator/platform equivalent**. Use melonDS FPS display; an in-game counter would be separate instrumentation. |
| Run without holding B | Native touchscreen running-shoes lock. | Retained. | **Already in base HGSS**. Retain native running toggle. |

## Interface and platform

| Feature | Base HGSS | English Visual+ | Category / work required |
|---|---|---|---|
| Quick ball throw, remembered ball and cycling | Bag/battle item interface, not Emerald's R-button + dedicated cycling plate. | Not added. | **Needs custom implementation**. Add optional one-button throw and ball selection; single eligible wild battles only; retain last choice, validate bag stock and storage. |
| Touchscreen field menus: party, bag, save, options, dex | Native dual-screen touch menus for those functions. | Retained. | **Already in base HGSS**. Keep HGSS interface rather than replace it with Hoenn-specific layouts. |
| Touch battle commands and move details | Native touch battle menu and move categories/details. | Retained. | **Already in base HGSS**. Keep native battle UI; exact Emerald move-button typography/graphics would be new UI work. |
| Touchscreen shop / bag quantity controls | Native DS shop/bag interfaces. | Retained, not redesigned. | **Partly present / adaptation needed**. Functional shopping is present; Emerald's particular touch-drag quantity interaction would need a UI rewrite. |
| Trainer / badges / party save overview | Native save confirmation and trainer/party screens. | Retained. | **Partly present / adaptation needed**. Exact combined Emerald save card would be a new optional UI. |
| Touchscreen map, Pokedex and regional units | Pokegear map, native Pokedex and region-specific presentation. | Retained. | **Already in base HGSS**. Keep HGSS equivalents; no Hoenn-specific table or translation fixes needed. |
| HD battle information / text boxes | DS native screens are 256x192 each; Emerald 3DS top screen is 400x240. | Background artwork changes only. | **3DS-specific; no direct NDS equivalent**. Cannot obtain 400x240 native UI from DS hardware. Emulator upscaling improves rendered 3D but does not automatically redraw 2D text. |
| 400-pixel field, effects, transitions and cutscenes | DS native aspect and resolution. | No widescreen conversion. | **3DS-specific; no direct NDS equivalent**. Use a separately validated emulator widescreen hack if desired; Emerald's per-scene widening code is not applicable. |
| Local trading / battling / multiplayer activities | Native DS local wireless, Union Room and game-specific minigames/facilities. | Retained. | **Already in base HGSS**. Retain DS protocols and activities; test emulator networking separately. Hoenn-only Berry Blender/contests are not HGSS content. |
| Soft reset | Native DS soft reset. | Retained. | **Already in base HGSS**. Retain existing reset path and release transient encounter state on reset. |
| Persistent enhancement / cheat settings pages | Native options save only the original settings. | Build-time variants, no enhancement menu. | **Needs custom implementation**. Milestone 04 adds a native SELECT menu for three integrated options and a versioned, trainer-owned, CRC-protected alternating journal in audited unused flash pages. Both games apply/load settings; HeartGold Cancel, native Save preservation and damaged-newer-copy fallback pass. Add remaining settings pages and broader compatibility/transition verification. |
| Follower talk / cries / animations / item finding | Native follower interaction system is richer in some areas but has different item rules. | Retained. | **Partly present / adaptation needed**. Keep native interactions, shiny/forms and transitions; audit item-finding differences before adding any Emerald-specific behavior. |
| English / Spanish / French / Italian build variants | We have clean USA English HG and SS; official other-language HGSS ROMs are separate. | English port of a Korean visual mod, not translation of the entire game. | **Partly present / adaptation needed**. English target is already native. Additional languages need their own ROMs, hooks and validation; do not apply USA offsets across regions. |
| Build game data locally from the user ROM | NDS ROM embeds its data, unlike Emerald's 3DSX + pack. | xdelta patches use the clean USA ROM. | **Partly present / adaptation needed**. Keep local ROM-to-patched-NDS workflow, checksum verification and original ROM preservation; no Emerald PAK needed. |
| Preserve existing saves | HGSS has its own DS save format. | Upstream states Visual+ preserves it. | **Partly present / adaptation needed**. Prove compatibility for every new setting and feature; do not claim Emerald .sav or GBA save compatibility with HGSS. |
| 3DS Home Menu forwarder / Homebrew Launcher | NDS application, not a native 3DSX. | Outputs a patched NDS ROM. | **3DS-specific; no direct NDS equivalent**. Use melonDS on Mac or an appropriate DS loader on hardware; Emerald's CIA/Luma launcher and DSP firmware instructions do not apply. |

## Original options

| Feature | Base HGSS | English Visual+ | Category / work required |
|---|---|---|---|
| Text speed | Native text speed option. | Retained. | **Already in base HGSS**. No enhancement implementation needed. |
| Battle animations | Native battle-scene option. | Retained. | **Already in base HGSS**. No enhancement implementation needed. |
| Battle style: Shift / Set | Native battle-style option. | Retained. | **Already in base HGSS**. No enhancement implementation needed. |
| Sound: mono / stereo | Native sound option. | Retained. | **Already in base HGSS**. No enhancement implementation needed. |
| Button mode / L=A | Native button-mode option; control mappings differ by platform. | Retained. | **Already in base HGSS**. No enhancement implementation needed. |
| Message window frame | Native frame selection; artwork differs by game. | Retained. | **Already in base HGSS**. No enhancement implementation needed. |

## Visual+ additions retained

These are additions of Visual+ itself, not extra Emerald enhancement settings: redrawn battle backgrounds, the full or conservative camera table, faster HP drain in all variants except visual-only, and the existing English port credit screen. The camera can glitch on some maps. The full and conservative-camera builds are separate compile/patch variants, not live in-game controls.

## Exact visible-encounter parity requirements

1. Off/Few/Some/Many map to 0/2/4/6 active wild slots. User-requested adaptation: all densities default to Normal grass battles. A separate optional Roaming only setting removes regular grass step encounters when visible wilds are enabled. Water/cave policy remains native until those visible encounters are implemented.
2. Grass first, followed by caves and surfable water; use HGSS route tables, levels, morning/day/night, swarms/radio/ability modifiers where appropriate. Never import Hoenn encounter data.
3. Roll the actual Pokemon at spawn: species, level, personality, IVs, form, gender and shiny result must survive into battle. A shiny sprite is not a promise if battle generation rerolls the Pokemon.
4. Display native species/form sprites and shiny palettes, idle/walk direction and shiny sparkle. Wilds must roam using the native follower-model walking animations, with collision/terrain checks and script/menu pauses. Grass rustle/water ripple and spawn fade/grow effects need a native implementation.
5. Touch/contact and interaction trigger the displayed encounter; normal trainer/NPC collisions, doors, ledges, elevations and the player follower keep working.
6. Repels and encounter-rate controls apply consistently. No spawning without an eligible non-egg party member; no inaccessible/occupied tiles.
7. Keep unconsumed spawns through menus, unrelated battles and connected-map crossings; remove the consumed spawn, and clear appropriately on warps/reset. Session-only objects must not leak into the saved NPC object list.
8. Freeze during scripts, fades, menus and battle startup; avoid duplicate launches. Exclude Safari Zone, Bug-Catching Contest, scripted legendaries/roamers and link/facility contexts initially, then add explicit support where compatible.
9. Keep special encounter mechanics, event scripts, fishing, Headbutt and Rock Smash intact. The optional grass policy must not suppress these separate interactions. Native legendary roamers need explicit visible support; their hidden grass-step branch is suppressed only when Roaming only applies.
10. Measure DS object/texture/heap limits with six wilds plus follower and busy NPC maps; test transitions, battle return, save/load and long play.

## Implementation order

1. Verify both clean USA inputs and build reproducible Visual+ reference ROMs. Keep originals unchanged and keep ROMs/assets out of Git.
2. Implement and test visible grass encounters in HeartGold, then caves/water and the persistence/shiny/repel edge cases. A portable policy test alone does not count as an NDS implementation.
3. Integrate selected capture EXP, IV/EV viewer, reusable TMs and the adapted Repel prompt; resolve shared ARM9/overlay ownership before adding more hooks.
4. Add runtime settings/persistence, party EXP, trade evolution and badge-gated field moves. Keep feature changes configurable.
5. Finish cheats and quick ball controls, and broader acceptance of the integrated world clock/HUD, with single-player restrictions.
6. Audit/implement runtime camera and rendering features individually. Stereo/native 400x240 are recorded platform limits, not silently marked complete.
7. Revalidate SoulSilver against its own symbols/offsets and ROM; never apply HeartGold-only hg-engine hooks blindly.

## Integration constraints

Visual+ owns ARM9 offsets 0x300 (44-byte cave) and 0xA18 (branch), map-header background IDs, overlay 1 (visual byte and camera table), overlay 12 (HP constants) and NARC subfiles in a/0/0/7, a/0/0/8 and a/2/6/2. hg-engine also changes game code and resources. Applying both whole-ROM xdelta patches sequentially is not a supported merge. Source-level integration or verified component transplantation with explicit collision detection is required.

hg-engine is HeartGold USA-specific and changes many mechanics by default, including features outside this request. Reusing selected routines is preferable to silently enabling Fairy/Mega/dex/AI/save expansion changes. Its project terms and all original Visual+ art/tool credits must be preserved.

The stock USA ROM is already English. “English Visual+” is a port of the Korean visual modifications; it does not require translating the game script.

## Audit tooling

Run `python3 scripts/audit_enhancements.py --emerald-source /path/to/emerald-3ds-0.4.0` to verify exact option-key coverage. Run `python3 -m unittest discover -s tests -v` for ROM-free checks. The feature records and implementation states live in `enhancements/inventory.json`.
