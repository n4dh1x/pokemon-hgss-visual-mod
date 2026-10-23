# Cave and Surf roaming encounters

Milestone 18 extends the existing Off/Few/Some/Many visible-wild setting to
native encounter-capable cave floors and Surf water. These use the same species
models and animations as the native follower. Spawned Pokemon retain their full
identity when contacted. No new option or save format is required.

The original encounter generator supplies cave/land or Surf species and levels,
time/radio/swarm changes, abilities and Repel rules. Fishing, scripted Pokemon,
Safari/contest/partner/Pal Park contexts and native legendary-roamer selection
retain their existing separate paths. Native legendary roamers are not yet
visible models. The optional Grass battles setting remains grass-only; regular
cave/water random encounters are still enabled under its Roaming only choice.

## Placement and movement

Two guarded native tile predicates classify encounter-capable grass, other land
floors and surfable encounter water. Water spawns additionally require the
player's native Surf state. Plain paths, ice, ledges, ladders, whirlpools and
waterfalls do not become spawn surfaces through this integration.

Each session slot retains its habitat. Spawns and later movement stay on that
surface, with native terrain/elevation/gimmick and object collision checks.
Native movement interpolates position and uses the species animation; models
start at the player's native vertical plane rather than an invented zero height.
On dismount, water wilds are removed before further contact; cave wilds can then
spawn on land. Native manager deletion also clears session habitat identity.
Real object IDs and transient-NPC saving filters remain unchanged.

## Verification

170 tests pass. New compiled ARM cases cover cave and water spawns, exact retained
contact identity, Surf-only eligibility, shore/warp movement rejection and stale
surface cleanup. Original native tile functions from both supplied baselines
run against real ROM flag data. No Pokemon-generation table or original model,
animation, ARM7, banner or unrelated NitroFS asset is changed.

Both Mac melonDS DS games cold-load project cave saves, display Zubat/Geodude,
and reach actual retained cave contact battles. Surf tests walk a real cave
route and complete the normal prompt, text, HM animation and mount. A declared
one-byte isolated fixture adds only the Fog Badge bit (10 to 18 hex); party
Pokemon, moves, position, Surf state and items are not edited. The existing
Field HMs fallback supplies a user without learning Surf. The other native
badge bit and all story checks are retained.

Both games generate and move native Magikarp on water. Contact battles have the
correct water backdrop and exact retained 236-byte enemies. Real dismounts remove
the two water wilds; subsequent cave spawns remain on land. Native saving filters
two transient objects. Cold reload preserves Surf position/state and all party
records, creates fresh water Pokemon and has exactly two owned IDs E0/E1 with
no saved NPC ghosts. Route 29 regressions preserve shiny colours, star glints
and the two one-time appearance chimes.

Evidence includes 17 accepted cases and the Surf fixture/route provenance.
The first HeartGold save attempt opened Options and is excluded from save
acceptance. The first SoulSilver contact route crossed the east shore and is
excluded from battle acceptance; the later route reaches the native battle.
See [milestone-18-verification.json](../enhancements/milestone-18-verification.json).

These are bounded Dark Cave/Magikarp and Route 29 tests with HG-derived project
progress in SoulSilver. Wider map/species/form/height, six-species texture/heap,
Repel, transitions and long-play acceptance remain pending. General spawn effects,
legendary visible integration and other audited enhancements remain in the full
active goal. These candidates are experimental.
