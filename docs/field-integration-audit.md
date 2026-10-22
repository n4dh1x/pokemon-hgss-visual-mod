# Field integration audit

These contexts were checked independently against both USA Visual+ full
baselines. Milestone 03 now installs guarded calls within them, plus the normal
field-control dispatch at `0x0203E0D0`. Full implementation and verification
limits are in [visible-encounters.md](visible-encounters.md).

| Routine/site | Image | Address | Checked bytes | SHA-256 |
|---|---|---|---|---|
| Normal field-input call | ARM9 | `0x0203E270` | `0x4` | `4cfc182bf31c832bdd17005e0e4384312960881b3fdfbdb14c07ca54c92e1a16` |
| FieldSystem_Control | ARM9 | `0x0203E15C` | `0x198` | `652e669711e0f8af6e082cad86640e34db51b0229ece1b731001b3f19bc49f16` |
| FieldInput_Process | Overlay 1 | `0x021E6AF4` | `0x2D0` | `0b22495d52b5131c68a2b20749a33064d7af8589aa5c25211b53d58371e041a7` |
| Ordinary step encounter gate | Overlay 1 | `0x021E7114` | `0x84` | `71e23a58ecd82a89f42f2e87edc9f504a579fbe1beae6e5e0bfb93d3bb016970` |
| Land/surf generation context | Overlay 2 | `0x02246C8C` | `0x2E0` | `2774f4f3deddfce2d71849c774885c82017a033979d9e2c39512802e0d6aba18` |
| FieldSystem_SyncMapObjectsToSaveEx | ARM9 | `0x0205E5EC` | `0x5C` | `d1e26d932f67ffa9f3172f1a2b8965b464f434e2ecc03a824159c97a29b29ea6` |

Each listed digest is identical in the two baselines. The normal call is Thumb
`a8f140fc`, targeting `0x021E6AF4`. Its caller only invokes that normal field
path while movement is allowed, and treats return values 1/2 as scripted/menu
events. Colosseum, Union Room and Battle Tower paths have separate dispatch.
The input routine processes on-frame scripts, trainers, step effects, field
moves, random encounters, NPC interaction, transitions and menu actions in order.
A wrapper must respect those priorities; being in the field is not sufficient
permission to spawn or start a battle.

## Generation and identity

The original land/surf generator already handles current HGSS tables, time,
swarm/radio substitutions, abilities, Repel, forms and generated Pokemon data.
Its successful ordinary battle-start call is at `0x02246F2E`, targeting
`sub_02050B08`. Its roamer branch has a separate call at `0x02246DD0`.
Do not turn a roamer into a generic visible spawn. Safari, contest and partner
paths need explicit exclusions before reusing this generator.

Retaining an entire BattleSetup for every visible wild would also retain a
snapshot of the player's party/bag. Battle setup must use current player data
at contact. Retain the generated enemy Pokemon identity, then build or refresh
player-side battle data when launching; never roll the enemy again at contact.

## Objects, persistence and capacity

`MapObject_Create` is at `0x0205E294`, and its extended entry is at `0x0205E2B4`.
The standard helper starts with object ID zero before constructing an object.
Reusing it with an existing ID/map combination can return an existing object;
unique spawn ownership must be established without modifying ordinary NPCs.
The native follower uses species/form/gender model selection and separate shiny
parameters, not a generic static sprite. Use the native species presentation.

The save synchronizer iterates every active object. It does not automatically
exclude dynamically created wilds. A correct integration must filter only
owned transient wild objects and preserve all normal NPC/follower save entries.
Object-manager deletion, map connections, warps and overlay unload must also
release or rebind owned references before their backing memory disappears.

The active field manager in the fresh fixture has 64 object slots. Measure busy
maps and graphics/heap use with six wilds and the follower before claiming that
Many is supported. The field heap is `0x1C000` bytes; do not reserve six complete
battle setups without measuring their allocations and lifecycle.

All semantics and acceptance cases remain in [emerald-parity.md](emerald-parity.md).
The new cold-loadable local save removes the introduction from subsequent
integration loops; it does not replace actual encounter, transition and save tests.
