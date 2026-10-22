# HGSS Enhanced — Emerald feature parity work

Fork of the English Visual+ project. The target is to retain HeartGold/SoulSilver's
native mechanics and Visual+ presentation while adding the missing Emerald 3DS
v0.4.0 enhancements.

**Current stage: experimental gameplay milestone 05.**
Both games now have native roaming grass encounters, using following-Pokemon
models and walking animations. Wilds retain their generated Pokemon into contact
battles. HeartGold also passes menu freeze/resume and transient-object save/reload
checks. Reusable TMs and level-40 trade alternatives remain integrated.
Press SELECT in the field for saved visible-wild, trade-evolution and reusable-TM
settings. Off removes wilds; Some supports four and Many six in the tested grass
area. Repel now blocks unsolicited low-level wild contact after spawning;
connected-map changes remove old-map wilds. Sixty-one tests pass.
Cave/water encounters, full capacity and transition
coverage, other enhancements and final gameplay validation remain.
These candidates are not the final release.

- [Complete 58-row feature inventory](docs/emerald-parity.md)
- [Machine-readable inventory and implementation states](enhancements/inventory.json)
- [Pinned source revisions](enhancements/sources.lock.json)
- [Current validation and next integration work](docs/enhancement-status.md)
- [Native loader and memory integration](docs/native-integration.md)
- [Visible encounters and roaming verification](docs/visible-encounters.md)
- [Enhancement menu and durable settings](docs/enhancement-settings.md)
- [Repel and connected-map verification](docs/encounter-refinements.md)

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
