# Shiny roaming wilds

Milestone 17 gives shiny visible wilds their native alternate colours, a short
star-glint burst and a brief native chime when they appear. Later glints repeat
every 120 eligible field updates and stay silent. Existing movement uses the
same native walking animation as the party follower. No new setting is needed:
these cues accompany genuine shiny roamers at any shiny-odds setting.

Ordinary roamers have ordinary palettes and emit neither glints nor a chime.
Turning visible wilds or the encounter rate Off removes roamers; outstanding
short native effects finish and release their resources. Spawn cooldowns pause
while the field input handler is suspended for menus/scripts. Each glint burst
uses a sampled world position; a later burst samples the moving Pokemon again.

## Integration

The native palette selector recognizes only IDs FD/FA/FB. Our transient wilds
use E0-E5. Two guarded palette-local ID calls now recognize owned wilds as FD;
actual object IDs, save filtering and all other ID queries are unchanged.
Ownership checks include active flag, manager, slot pointer, map and ID. During
native synchronous construction, a bounded pending slot also checks sprite and
species. Species/form/shiny parameters are prepared first through the original
parameter-only helper on a 68-byte scratch prefix, before CreateObject runs.

Glints reuse the original native seed_kira model/animation effect, renderer 16,
with its own short-lived task and resource reference counting. It retains a
world position, never a map-object or retained-Pokemon pointer. Appearance calls
the original PlaySE with SEQ_SE_GS_KIRAKIRA (2340). Repeated bursts do not call it.
No original assets, sound banks or Pokemon records are edited. Extra diagnostics
are session-only; settings journal and native save formats are unchanged.

## Verification and limits

165 tests pass. Compiled ARM tests cover palette ownership/pending guards,
normal silence, repeated silent glints, one appearance chime and effect failure.
Original native parameter and palette-selector instructions from both ROMs run
with controlled archive bytes; scratch canaries and native NPC paths are checked.
Both final ROMs pass patch fingerprints, recorded-change checks and xdelta
round trips and reproduce their tested experiment hashes.

Mac melonDS DS 1.3.1 runs use software rendering, builtin BIOS and isolated
copies of project test saves, with no RAM fixtures. Both games display native
shiny Hoothoot colours and star glints. Selecting native odds and Some retains
two shinies and adds two ordinary wilds, without additional chimes. Ordinary and
shiny Hoothoot colours coexist. Off leaves no owned wilds, no pending cooldowns
and native effect reference/resource counts zero. Real contact battles contain
the exact retained 236-byte shiny enemy. Previous capture/save acceptance is
recorded separately in milestone 16.

Two HeartGold identity reads use a normal SELECT pause before inspection because
an unpaused emulator snapshot can interrupt native Pokemon encryption. The
inspector still rejects any private getter mutation. Audio PCM is recorded and
nonzero; API/count checks establish sound selection and one-time scheduling.
No human listening assessment is claimed.

Full species/form, busy-map, six-species/capacity, long-play and wider transition
acceptance remain pending. SoulSilver uses HG-derived project progress. These
are experimental candidates, and the complete enhancement goal is unfinished.
Exact hashes, inputs and observations are in
[milestone-17-verification.json](../enhancements/milestone-17-verification.json).
