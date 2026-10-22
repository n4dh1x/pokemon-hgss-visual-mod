# Repel and connected-map behavior — milestone 05

Repel filters wilds by level. It does not increase rarity, change encounter-table
weights, raise levels or limit the difference above the party lead. HGSS uses the
first alive non-egg party member: lower-level wilds are suppressed, equal-level
and higher wilds are allowed. A route with no qualifying wild levels can have no
new encounters while Repel is active.

New visible spawns already pass through native HGSS encounter generation,
including its current Repel check. Milestone 05 adds a check when an existing
wild attempts to walk into the player, using the current party and Repel state.
A suppressed wild stays visible, waits and continues roaming. The player can
deliberately walk into or interact with it, matching the audited Emerald visible
encounter behavior. Native HGSS still consumes the Repel item and decrements its
step counter. The additional "use another Repel?" enhancement remains pending.

Object ownership now checks the stored map in addition to object pointer, ID
and manager. A connected-map transition releases remaining old-map wilds in the
free-input update. An object reused for an authored NPC on a different map is
left alone and remains included in native saving. Full manager teardown retains
the previous ownership-forget behavior.

## Verification

Sixty-one project tests pass. Compiled ARM tests cover Repel activated after
spawning, expiry, equal-level permission, current first alive party selection
with eggs/fainted members, deliberate interaction, connected-map release and
same-address/ID reuse on a new map. The new native save APIs are fingerprinted
independently in both USA Visual+ baselines.

Actual Mac melonDS DS 1.3.1 runs use copies of the project-created HeartGold
fixture, with six active wilds and the level-5 Chikorita:

- A declared four-byte developer fixture adds two Repels to an empty bag slot
  in each game. Normal bag inputs use one: quantity changes to one and the native
  step counter becomes 100. The existing six wild identities are retained.
- During 15,000 free-field frames with no player input, HeartGold blocks seven
  unsolicited contacts and SoulSilver four. All six wilds remain; native walking
  continues and no battle launches.
- Matched control copies change only the Repel counter from 100 to zero before
  running the same idle interval. Each enters a battle with a byte-identical
  copy of a stored spawn in the native enemy party.
- In HeartGold, deliberate downward movement under active Repel contacts a
  level-2 Hoothoot. The native battle enemy matches retained slot 3 exactly.
- Both games walk from Route 29 (map 33) into New Bark Town (map 60). No owned
  wild remains; two remaining old-map objects are explicitly released per run,
  with others already despawned by distance. HeartGold naturally walks back.
- HeartGold's Repel counter falls from 100 to 81, then 63, through normal movement.
  Re-entering grass with Repel still active leaves no low-level spawns. A separate
  copy simulates expiry by setting only that counter to zero. Returning to the
  same grass position produces six fresh native-generated identities, taking the
  session's generated count from six to twelve.

The free-input transition path is verified. Native A interaction runs earlier
in the input dispatcher; contact during an immediate map/option/context change
still needs its own eligibility guard and tests before full transition acceptance.
The simulated expiry does not establish the complete real wear-off dialogue or
the pending repeat-Repel prompt. Tests do not cover every party change in the
emulator, every map/warp, caves/water, long sessions or six distinct species at
once. SoulSilver uses a copied HeartGold fixture, not a fresh story playthrough.

## Isolated developer fixtures

`smoke_libretro.py --ram-fixture MANIFEST --load-state STATE` is only a verification
aid. It requires matching ROM and complete 4 MiB RAM hashes, exact expected bytes,
bounded non-overlapping changes and reasons. It validates every change before
writing the isolated process's RAM, records the exact manifest/applied hashes,
and never edits the input checkpoint or cartridge save. Fixture states and all
ROM/save/memory/screenshot artifacts remain local and ignored. Native API
instruction fixtures do not replace the real emulator observations above.

Hashes, input intervals, fixture declarations and bounded state diagnostics are
in [milestone-05-verification.json](../enhancements/milestone-05-verification.json).
