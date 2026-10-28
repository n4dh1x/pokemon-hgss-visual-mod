# HGSS project rules

- Run project cleanup after every build attempt, successful or failed. The ROM builders enforce this through `scripts/cleanup_builds.py`; after other/manual build commands run `.venv/bin/python -B scripts/cleanup_builds.py --apply`.
- Keep the two newest gameplay milestones and the newest verified milestone. Keep baselines, patches, reports, source files, original ROMs/ZIPs and all saves. Retain generated ROMs with companion saves too. Remove an older generated ROM only after its retained patch reconstructs the exact recorded SHA-256 from the unchanged original ROM.
- Preserve verification evidence. On macOS, compress completed snapshot files transparently only after byte-for-byte SHA-256 verification; keep their paths and logical bytes unchanged. Skip snapshot maintenance while verification is running.
- Do not write build ROMs in place. Use a temporary file and atomic replacement, and refuse to replace a different existing candidate. Never overwrite an accepted verification run; use a new run name.
- Build and full test runs share `build/native` and baselines: never run them concurrently. Native emulator runs using fixed experiment ROMs may use separate output directories concurrently.
- Keep ROMs, saves and generated game assets out of Git. Commit only the changes for the task; preserve unrelated work in progress.
