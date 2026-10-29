# Confirmed Pokédex actions

Press SELECT in free field play, X three times to reach Cheats, page 4, then
choose the fifth row, Pokedex actions. A opens the list:

- Complete Johto Dex registers its exact 256 species as seen and caught.
- Unlock National Dex sets both original HGSS upgrade flags and leaves entries
  unchanged.
- Complete National Dex unlocks National mode and registers all 493 HGSS species
  as seen and caught.

Each action asks for confirmation, default No. Direction buttons change Yes/No;
A confirms and B cancels. Work progresses while field NPCs remain paused. A/B
acknowledges completion. Use the game's normal Save command to retain progress.
These actions take effect when confirmed. Settings Save/Cancel applies only the
twenty saved switches; it does not undo confirmed Pokédex progress.

The actions leave the party, PC storage, money, Mom's savings, coins, Battle
Points, items, story variables/flags and gameplay RNG alone. They do not grant
ownership of the Pokédex itself; normal story acquisition still enables its app.
National actions mirror the original upgrade command's Dex flag and profile bit,
without game-clear or ownership story flags.

## Native bookkeeping

Johto membership comes from the unchanged native `a/1/3/8` table, including the
five Gen-IV additions. The table has 256 distinct nonzero regional numbers.
National covers species 1–493. A deterministic private Pokemon is created by
HGSS's original factory for each selected species, using fixed PID 1, IVs 0 and
the player's full OT ID. It supplies valid original form, gender and English
language metadata to the original caught routine, which sets seen as well.
The private Pokemon never enters the party or storage; no gameplay RNG advances.

Existing entries are retained. Native routines append compatible form/gender
history and preserve existing Spinda personality. Completion means species
seen/caught, with normal metadata; it does not fill every alternate form or
language. It does not add unique-catch statistics, trainer score or Pokemon.

The entire native Dex API region, profile upgrade helper, factory, native table
loader and table hash independently match both USA Visual+ baselines. Original
instructions and data stay unchanged. The action uses the existing enhancement
menu task, processing one selected species per update. Ownership/save identity
is checked before work and each update. Allocation failure occurs before flags
change; owner mismatch stops work and frees private allocations. Completed work
frees the scratch Pokemon and regional table. Normal save/version layouts stay
unchanged: twenty switches, 48-value/256-byte journal, 32-byte loader header.

The menu has 6/6/4/5 entries plus Save/Cancel. Dex action/UI diagnostics are
44/16 bytes. The 26,072-byte payload ends at `0x01FFF5D8`, with 2,600 bytes left in
the present ITCM reserve.

## Verification

280 regression tests pass, including eight Dex instruction/UI tests, 45 settings
checks and sixteen cleanup checks. Native Dex instruction tests retain regional
membership, seen/caught bits, languages, existing Spinda/form history, allocation
failure, ownership denial, default-No and B cancellation. External heap/Pokemon
metadata services are bounded in those instruction tests. Actual emulator checks
execute the complete original Pokemon factory and registration routines.

Mac melonDS DS 1.3.1 acceptance in both games verifies:

- Exact 256-species Johto membership and 493 National entries.
- Unlock changing only the two original flags, with unchanged 6 seen/5 caught
  starting entries; Johto completion keeps National locked.
- Unchanged entire party bytes, native hatch/score counters, currencies,
  inventory, story variables/flags and gameplay RNG during direct action controls.
- Default-No/B cancellation leaving progress and the entire cartridge save
  unchanged; confirmed actions do not write cartridge/settings storage themselves.
- Native save/cold preserving exact Dex/profile/story bytes and all inspected
  decoded party fields, economy and earlier enhancement choices.
- Original Pokédex app totals, entry/area views and field return.

The direct actions, cancellation and native save controls use only real inputs,
with no RAM fixtures. The early HG-derived project test lineage has not earned
Pokédex ownership. Separate original-app UI controls explicitly insert native
GivePokedex(291) and SetFlag(FLAG_GOT_POKEDEX0x6B), then return to the follower
script: 12 unused script-stack bytes and a four-byte script pointer. This supplies
ownership solely for app-UI verification; the enhancement never sets it. The
fixture injects no Dex entries, Pokemon, currencies, inventory or coordinates.
Earlier legendary-release/location/ball-fixture ancestry remains declared.

Native cold boot changes the HG lead's raw storage bytes while every inspected
decoded identity/battle/memo/name field stays equal. Exact party-byte preservation
is asserted for the direct menu actions, not all native reloads. Original
follower/walking effects remain possible in the separate app-UI fixture branch.

Wider alternate forms/languages, acquisition/story cases and long-play acceptance
remain pending. These are experimental candidates; the full enhancement goal is
unfinished. See [exact evidence](../enhancements/milestone-27-verification.json).
Recheck accepted local cases with
`.venv/bin/python -B scripts/verify_dex_milestone.py`.
