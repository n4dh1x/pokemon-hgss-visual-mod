# HGSS Enhanced — Emerald feature parity work

Fork of the English Visual+ project. The target is to retain HeartGold/SoulSilver's
native mechanics and Visual+ presentation while adding the missing Emerald 3DS
v0.4.0 enhancements.

**Current stage: experimental gameplay milestone 27.**
Both games now have native roaming grass encounters, using following-Pokemon
models and walking animations. Wilds retain their generated Pokemon into contact
battles. HeartGold also passes menu freeze/resume and transient-object save/reload
checks. Reusable TMs and level-40 trade alternatives remain integrated.
Press SELECT in the field for saved visible-wild, trade-evolution and reusable-TM
settings, plus the repeat-Repel prompt. Off removes wilds; Some supports four and Many six in the tested grass
area. Repel now blocks unsolicited low-level wild contact after spawning;
connected-map changes remove old-map wilds. 280 tests pass. The repeat-Repel option offers another Repel of the
same last-used type; both games pass native save/reload and full 200-step expiry.
The prompt respects native bag restrictions and rechecks access before use.
A fifth saved option adds capture EXP through the native EXP/EV task. Both games
pass successful capture, Pokédex registration, nickname decline and field return.
Both games also pass level-6 stat screens, Razor Leaf learning into an empty slot,
and native save/cold reload of rewards. Evolution and wider capture cases remain pending; milestone 19 also verifies
a native full-moveset replacement during legendary capture EXP.
A sixth saved option adds party-wide EXP Share: full EXP for participants, half
for healthy bench Pokemon, with one collective message. Both games pass ordinary
victories, saved Off controls and native save/cold reload of rewards; SoulSilver
also passes combined party/capture EXP. Follow-up verification passes native bench
level-3 stat screens in both games and full EXP for two actual HG participants.
Milestone 19 verifies native bench move learning; bench evolution and extended
battle acceptance remain pending.
Milestone 12 adds a second settings page: Field HMs and Grass battles.
Grass battles defaults to Normal at every density. Optional Roaming only removes
step-triggered regular grass battles while retaining moving contact encounters;
turning visible wilds Off restores native random encounters. Both games save and
cold-reload the option. Contextual field-HM fallback is integrated. Milestone 13 adds Bag USE NOW
actions for owned HM02 (Fly) and TM70 (Flash), with native restrictions and
confirmation. Cancel returns to the Bag; ordinary teaching remains available.
Milestone 14 verifies actual Flash lighting in Dark Cave in both games.
Full per-move gameplay acceptance is still in progress.
The ninth saved option adds an IV/EV viewer on the native Skills summary page:
Y cycles stats/IVs/EVs; L shows EVs, R shows IVs and SELECT restores normal stats.
X changes enhancement-menu pages, including with L=A enabled. Native touch/page/party
navigation restores the normal view first. Both games pass saved On/Off reloads
and unchanged encrypted party data checks. Actual PC-box UI acceptance remains pending.
The tenth saved option is Encounter rate: Normal, Off, 1/4, 1/2 or 2x. It scales
ordinary walking/surfing checks and visible spawn cadence; Off removes visible
wilds too. Native legendary decisions, fishing and scripted/special encounters
retain their separate rules. See [encounter-rate.md](docs/encounter-rate.md).
The eleventh saved option adds shiny odds for new eligible wilds, starters and
script gifts, from native odds through Always. Eggs, trades, fixed personalities
and existing Pokemon remain native. Visible shininess/PID/IVs stay intact into
battle and capture, and caught shinies survive native save/cold reload in both
games. Shiny roamers now show alternate colours, repeating star glints and one
chime on appearance. Ordinary roamers stay silent. See
[shiny-odds.md](docs/shiny-odds.md).
Milestone 18 adds roaming cave-floor and Surf-water encounters using native
tables. Both games pass cave/water contact battles, shore cleanup and native
Surf saves/cold reloads. See [visible-habitats.md](docs/visible-habitats.md).
Milestone 19 adds saved legendary-roamer models and native battle bookkeeping,
plus shiny selection on new native releases. Both games pass retained shiny
Raikou contact, capture, rewards and native save/cold reload. See
[visible-legendaries.md](docs/visible-legendaries.md). Wider legendary species,
full capacity/transition coverage, other enhancements and final validation remain.
Milestone 20 adds saved Party follower On/Off on page 2. Native lifecycle and
permission checks control the lead follower independently of roaming wilds.
Both games pass native walking/dialogue, On/Off save/cold reload and a connected
map round trip. See [follower-control.md](docs/follower-control.md).
Milestone 21 adds a saved accelerated world clock and optional field time/speed
HUD on page 3. Lighting, timed readers and active-session Berry growth follow
world time; native RTC/calendar/daily events stay separate. New seeds receive
only time after planting. See [world-clock.md](docs/world-clock.md).
Milestone 22 adds saved Camera angle and Camera zoom on page 3. Visual+/100%
retain each map's defaults; custom views yield to native tasks and menus. Both
games pass lab round trips, native saving/cold reload, reset and Cancel checks.
See [camera-controls.md](docs/camera-controls.md).
Milestone 23 adds saved Always catch on the fourth menu page, default Off.
The native ball-shake path retains ball effects and normal capture bookkeeping.
Both games pass Friend Ball capture versus failed Off controls, native rewards,
save/cold reload and Cancel. See [always-catch.md](docs/always-catch.md).
Milestone 24 adds saved Instant victory on Cheats, page 4, default Off.
Eligible opponents faint before choosing an action, with native EXP, trainer
replacement and prize money. Both games pass wild and two-Pokemon trainer
controls, native saving/cold reload, Cancel and legacy options. See
[instant-victory.md](docs/instant-victory.md).
Milestone 25 adds saved Fast egg hatching on Cheats, page 4, default Off.
One valid party egg enters the original hatch sequence every five eligible
walking steps. Daycare breeding and normal egg-cycle rules still run. Both games
pass exact four/five-step controls, native animation/naming, save/cold reload,
Cancel and older journals. See [fast-eggs.md](docs/fast-eggs.md).
Milestone 26 adds saved Infinite money on Cheats, page 4, default Off.
Native wallet reads refill the actual balance to ₽999,999. Both games pass
buy/sell and Cancel controls, Mom's normal trainer deposit, Trainer Card access,
native save/cold reload and older journals. Coins and Battle Points stay separate.
Turning it Off stops refills and keeps the actual balance. See
[infinite-money.md](docs/infinite-money.md).
Milestone 27 adds confirmed Pokédex actions on Cheats, page 4: complete Johto
(256 species), unlock National mode, or complete National (493 species). Normal
form/language records use HGSS routines, with story flags, party and currencies
retained. Both games pass Cancel, native save/cold, original Pokédex UI counts
and field return. See [pokedex-actions.md](docs/pokedex-actions.md).
These candidates are not the final release.

- [Complete 59-row feature inventory](docs/emerald-parity.md)
- [Machine-readable inventory and implementation states](enhancements/inventory.json)
- [Pinned source revisions](enhancements/sources.lock.json)
- [Current validation and next integration work](docs/enhancement-status.md)
- [Native loader and memory integration](docs/native-integration.md)
- [Visible encounters and roaming verification](docs/visible-encounters.md)
- [Enhancement menu and durable settings](docs/enhancement-settings.md)
- [Repel and connected-map verification](docs/encounter-refinements.md)
- [Same-type repeat Repel and verification](docs/repel-prompt.md)
- [Capture EXP integration and verification](docs/capture-experience.md)
- [Party-wide EXP Share and verification](docs/party-experience.md)
- [Native IV/EV summary viewer](docs/summary-viewer.md)
- [Encounter rate and visible spawn cadence](docs/encounter-rate.md)
- [Shiny odds and retained identity](docs/shiny-odds.md)
- [Bench leveling and multiple participants](docs/party-progress.md)

Verify the inventory:

```sh
python3 scripts/audit_enhancements.py --emerald-source /path/to/emerald-3ds-0.4.0
python3 -m unittest discover -s tests -v
```

Build a reference directly from a clean USA NDS or ZIP and the included patch:

```sh
python3 scripts/build_baseline.py --rom /path/to/HeartGold.zip --variant full --xdelta /path/to/xdelta3
python3 scripts/build_baseline.py --rom /path/to/SoulSilver.zip --variant full --xdelta /path/to/xdelta3
```

Outputs stay under ignored `build/baseline/`; originals remain unchanged. This
workflow uses the existing USA release patches and does not need Korean ROMs.
Rebuilding Visual+'s original port from Korean donor assets uses the upstream
workflow below. No ROMs, saves or locally extracted assets are committed.

Experimental gameplay builds (after installing `requirements-dev.txt`):

```sh
.venv/bin/python scripts/build_enhanced.py --rom /path/to/HeartGold.zip
.venv/bin/python scripts/build_enhanced.py --rom /path/to/SoulSilver.zip
.venv/bin/python -m unittest discover -s tests -v
```

Each candidate records its exact enabled changes and limitations in a JSON report,
and produces a locally verified xdelta patch. `scripts/smoke_libretro.py` can run
an installed melonDS DS core with isolated test directories and capture video,
audio counts, RAM and ROM-matched savestates. It supports recorded lower-screen
touches and isolated cartridge-save import/export. A fresh HeartGold save has
passed native Save, cold boot and Continue checks. It is a development test host;
booting alone does not prove gameplay correctness.

---

# Pokémon HG/SS Visual Mod — Visual+ English Port

English (USA) port of **Pokémon Visual+ v1.0.0**, a Korean visual enhancement
mod for Pokémon HeartGold, created by **민트초크 (MinT ChoK)** with battle
background artwork by **Young** (Pokémon Another Red). This project ports the
mod to the English HeartGold *and* SoulSilver ROMs and distributes it as
xdelta patches only.

## What Visual+ changes

1. **New battle backgrounds** — redrawn, more vivid battle background images
   — **artwork by Young** (creator of the fan game *Pokémon Another Red*)
2. **Enhanced 3D camera** — a more dramatic overworld camera angle
3. **Faster HP bar** — HP drains ~7–8× faster in battle

## Variants

| Variant | Backgrounds | Fast HP | 3D Camera |
|---|---|---|---|
| `visual-only` | ✅ | ❌ | ❌ |
| `safe` | ✅ | ✅ | ❌ |
| `full` | ✅ | ✅ | ✅ full |
| `conservative-camera` | ✅ | ✅ | ✅ 50 % blend |

The upstream mod notes the full 3D camera can glitch on a few maps — pick
`safe` or `conservative-camera` if that bothers you.

## Supported games

| Game | Status |
|---|---|
| Pokémon HeartGold (USA) | ✅ released |
| Pokémon SoulSilver (USA) | ✅ released |
| Pokémon Platinum (USA) | 🔜 planned |
| Pokémon Diamond / Pearl | 🔮 future |
| Pokémon Black / White | 🔮 future |

## Quick start

1. Obtain a **legal dump of your own cartridge** (see [Legal](docs/legal.md)).
2. Download the patch for your game/variant from the
   [Releases page](../../releases) or see [docs/download.md](docs/download.md).
3. Apply with xdelta ([Windows](docs/setup-windows.md) ·
   [Android/UniPatcher](docs/setup-android.md) ·
   [macOS/Linux](docs/setup-macos-linux.md) ·
   [AYN Thor](docs/setup-ayn-thor.md)).
4. Play on real hardware or an emulator
   ([melonDualDS guide](docs/setup-melondualds.md)).

Expected clean ROM checksums are listed in
[docs/compatibility.md](docs/compatibility.md).

## Building from source

See [docs/building.md](docs/building.md). Short version:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
brew install xdelta                      # or your package manager
.venv/bin/python scripts/verify_roms.py  # locate + verify your ROMs
.venv/bin/python scripts/port.py         # build all 8 patches
.venv/bin/python scripts/validate.py     # run the full test suite
```

Test reports: [HeartGold](docs/reports/HeartGold_Test_Report.md) ·
[SoulSilver](docs/reports/SoulSilver_Test_Report.md)

## Legal

**This project does not distribute ROMs.** Users must supply a legally
obtained ROM dump from a game they own where permitted by applicable law.
The repository contains only tools, documentation, and binary *difference*
patches. See [docs/legal.md](docs/legal.md).

## Credits

- **민트초크 (MinT ChoK)** — original Visual+ mod
- **Young** — battle background artwork (Pokémon Another Red)
- **KaioShin / Josh MacDonald** — xdeltaUI / xdelta
- **RoadrunnerWMC** — ndspy
- English port tooling — this repository

See [docs/credits.md](docs/credits.md).
