# Native moving grass encounters

Wild Pokemon now appear and roam in Route 29 grass in both USA games over Visual+.
They use HGSS's native following-Pokemon species/form/gender models and normal
walking commands. The party follower retains its native behavior. This is a
working grass integration, not complete Emerald feature parity.

## Current behavior

- Press SELECT in the field for Off/Few/Some/Many (0/2/4/6 slots).
  Save and close applies and stores the choice; B or Cancel discards changes.
  Few is the default without valid owned settings. See
  [enhancement-settings.md](enhancement-settings.md).
- Generation reuses native HGSS land encounters: route/time data, radio/swarm
  substitutions, abilities, Repel checks and the actual Pokemon generation path.
  The full encrypted 236-byte Pokemon is retained. Its species, level, PID, IVs,
  nature, gender and form are not rerolled at contact.
- Native species models walk independently on grass with randomized waits,
  turns and a three-tile home radius. Destination terrain, elevation/gimmick
  collision and current/previous object occupancy are checked before issuing
  native movement commands. Position changes use native interpolation.
- Moving into a wild, interacting with it, or a wild walking into the player
  starts its retained battle through the normal native encounter task. Current
  player party/bag data is initialized at contact, not snapshotted at spawn.
- Repel keeps its native level rule: below the first alive non-egg party member
  is suppressed; equal/higher levels remain eligible. Rarity and rolled levels
  are unchanged. If Repel is used after spawning, lower-level wilds remain visible
  but cannot initiate a battle by walking into the player. Deliberate player
  contact remains allowed, matching Emerald's visible-encounter behavior.
- Grass battles is a separate saved option on page 2 (L/R). Normal is the
  default for Few, Some and Many and keeps native random encounters. Roaming only
  removes walking-triggered regular grass battles; collision/interaction with a
  moving visible wild starts its retained battle. Visible Off restores native
  random encounters. Water, caves and special contexts keep native behavior.
  Safari, contest, Pal Park and partner contexts are excluded from spawning.
- Native legendary roamers do not yet have visible sprites. Their hidden grass
  step-battle branch is also suppressed while Roaming only applies. Use Normal
  for their native encounters until explicit visible-roamer support is added.
- Owned wilds freeze, including in-progress native movement, while field control
  is locked. Closing both a party screen and its parent field menu resumes them.
- Only owned temporary objects are skipped by the native saved-object iterator.
  Player, follower and authored NPC entries remain. Manager teardown clears wild
  ownership before the original heap allocations are freed. Consumed wilds are
  removed; unconsumed wilds retain their identities over the tested battle return.
- Connected-map changes remove remaining old-map wilds even if the object
  manager is reused. Ownership includes the object's map as well as ID, pointer
  and manager, preventing removal/save-filtering of a reused new-map NPC.

## Verified evidence

Sixty-one tests pass across the project. Field tests execute compiled ARM code for identity copying,
contact from either direction, ordinary encounter fallback, special contexts,
save exclusion, cleanup, native walking selection, collision constraints and
freeze/resume. Both baselines independently accept the exact guarded hook bytes;
unexpected file changes and invalid branch encodings are rejected.

On melonDS DS 1.3.1, both final milestone ROMs load a separate copy of the
project-created save, spawn visible moving wilds and enter native battles. The
native battle task's BattleSetup enemy party contains a byte-identical copy of
the stored spawn Pokemon in each game. HeartGold also demonstrates a roaming
wild initiating contact with the stationary player; no movement input was sent
after Continue in that run.

The party-menu test holds for 600 frames. Wild vectors, tile positions and
movement phases are unchanged, then walking resumes after the menu layers close.
Native saving skips two active wilds, retaining the player/follower/NPC entries.
A cold reload successfully recreates the two current-mode wilds. The original
HeartGold test save was created through normal story inputs; using its isolated
copy in SoulSilver does not establish a fresh SoulSilver story playthrough.

Full hashes, inputs and bounded diagnostics are in
[milestone-03-verification.json](../enhancements/milestone-03-verification.json).
ROMs, saves, state files, screenshots and logs remain local and ignored.

Inspect a run without altering it:

```sh
.venv/bin/python -B scripts/inspect_visible_state.py \
  --run local_data/verification/hg03d-idle-contact \
  --report build/candidates/heartgold-visual-plus-gameplay-milestone-03.json
```

The inspector checks ROM hashes, state format, resident config uniqueness and
RAM bounds. It follows the native battle task to the enemy party rather than
treating an arbitrary memory-pattern match as identity proof.

Milestone 05 verifies actual native Repel use after spawning in both games, followed
by protected and matched unprotected contact runs. Both games also cross Route 29
to New Bark Town with no carried wild objects. HeartGold deliberate contact under
Repel retains the exact enemy, and returning to grass demonstrates spawn filtering
and new identity generation after a declared simulated expiry. See
[encounter-refinements.md](encounter-refinements.md) for exact scope and fixture use.

## Remaining acceptance work

Milestone 04 adds a native settings menu and persistent modes. HeartGold shows
six active moving wilds in Many; SoulSilver shows four in Some and six in Many.
HeartGold Off removes all owned wilds. Both games read saved values on cold boot;
the test area includes Hoothoot and Rattata, not six distinct simultaneous species.

Do not mark the overall feature verified yet. Cave/water support,
all Few/Some/Many/off capacity cases, six-species texture/heap limits,
busy maps, long play, further connected-map crossings/warps and party/Repel edge cases,
shiny sparkle, spawn/despawn effects, capture and additional script/fade cases
still require implementation or verification. The original full encounter
specification in [emerald-parity.md](emerald-parity.md) remains authoritative.

Milestone 06 adds a central eligibility check before native early A contact can
launch a wild battle: current map, mode/capacity and regular field context must
still match. Four compiled ARM regressions cover map change, Off and special
contexts. The complete project suite now passes 75 tests; broad acceptance above
remains pending.


## Milestone 12 optional grass policy

This replaces the earlier implicit Many-only suppression with an explicit user
choice. Every density defaults to Normal. Both games save Roaming only and load
it after a full core restart. HeartGold records seven blocked grass-step checks
and five walking commands without a battle in the bounded walk. Both games
also start contact battles with byte-identical retained spawns while the option
is active. Compiled ARM tests also cover Normal at all densities, visible Off,
special contexts, cave/water fallback, Repel after spawning and exact contact
identity. These bounded checks do not establish all-map or all-species acceptance.
See [milestone-12-verification.json](../enhancements/milestone-12-verification.json).
