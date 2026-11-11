# HGSS Enhanced milestone 33

This playable milestone includes the individual event-gift picker. The full
release checklist is still open. Use your clean English USA cartridge dump.
Keep your original dump and save files in a separate folder.

## Apply the supplied patch

Install `xdelta3`. If your ROM is in a ZIP, extract the `.nds` file first.
From the folder containing the patches, run the command for your game.
Replace the clean ROM path with the location of your own dump.

```sh
xdelta3 -d -s "/path/to/HeartGold USA.nds" heartgold-visual-plus-gameplay-milestone-33.xdelta "HeartGold Enhanced.nds"
xdelta3 -d -s "/path/to/SoulSilver USA.nds" soulsilver-visual-plus-gameplay-milestone-33.xdelta "SoulSilver Enhanced.nds"
```

The bundle's `manifest.json` lists the expected SHA-256 values for each clean
ROM, patch and output ROM. On macOS, use `shasum -a 256` to compare a file.
The patched ROM opens in melonDS or the RetroArch melonDS DS core. In the
field, hold **SELECT + L**, then release both buttons to open Enhancements.

## Rebuild from source

Install Python 3, xdelta3, Clang with the ARM cross-compiler target, and
ARM-capable LLD. The build recognizes `HGSS_CLANG` and `HGSS_LLD` if you
need to supply explicit tool paths.

```sh
git clone https://github.com/n4dh1x/pokemon-hgss-visual-mod.git
cd pokemon-hgss-visual-mod
git switch --detach f2f0636a80b8533961944669bffd8e4b079432e7
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/build_enhanced.py --rom "/path/to/HeartGold USA.zip" --xdelta "$(command -v xdelta3)"
.venv/bin/python scripts/build_enhanced.py --rom "/path/to/SoulSilver USA.zip" --xdelta "$(command -v xdelta3)"
```

The source builder accepts either a clean `.nds` or a ZIP containing one
clean `.nds`. It writes the enhanced ROM, xdelta patch and verification
report to `build/candidates/`.
