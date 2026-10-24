# Saved party follower control

Open SELECT, press X for page 2 and choose Party follower, the sixth option.
On is the default. Save and close applies both pages; B/Cancel discards changes.
The option controls the party follower independently of visible wild Pokemon.
Wilds continue to use their native walking animations and shiny effects.

The original native follower permission checks remain authoritative when On,
including species, map, size and story/player-state restrictions. Off rejects
follower creation in the two native initialization paths. Their manager-to-field
calls first load the owned settings journal, so a saved Off applies during cold
initialization. Four guarded ARM9 calls and one overlay-1 permission call change;
the original native permission function itself remains intact.

For live toggles, the free-input handler requests the native deferred follower
refresh. Off removes the party object and clears its native active flag. On
uses native creation and renderer initialization, restoring current party
species/form/shininess and native script/animation behavior. It never fabricates
a Pokemon or changes the shared follower palette/model system used by wilds.
Busy field tasks and unsupported avatar states defer changes. Native calendar,
story inhibit flags and Pokemon data are not rewritten by the option.

## Persistence

The existing version-1 256-byte journal uses value slot 11 for hide_follower and
presence bit 256 in reserved word 0. Zero means native On; an absent presence bit
also defaults On, ignoring legacy padding. Other fields and unknown later slots
are retained, writes remain atomic, and runtime changes apply only after verified
flash readback. Older store callers preserve the option. Native save layouts,
checksums and allocated chunks retain their original format.

## Verification and remaining work

184 tests pass. New compiled ARM cases cover native permission forwarding,
loading settings before initialization, original native deferred-refresh
instructions with controlled factory/render APIs, removal/restoration, independent
wild objects, busy/task/avatar deferral, native forbidden-map/no-healthy-party
controls and both-ROM fingerprints/mutation guards. Journal/menu tests cover
legacy padding, explicit Off, invalid values, failed writes, Cancel, atomic
Save, unknown-slot preservation and six options on each page.

Both final ROMs match the tested experiments byte for byte; their 18,636-byte
resident payloads, checked edits and xdelta patch round trips pass. On Mac
melonDS DS 1.3.1, both games keep the default follower from milestone-19 project
progress. Off removes it while five wild models remain active and walk. On
restores Chikorita's native walking and ordinary follower dialogue. Native saves
and cold boots preserve both On and Off, Pokemon identities and EXP/EV/moves/PP,
and retain both enhancement journal pages.

Both games also keep Off across Route 29 to New Bark Town, allow restoration
there, and walk back with the follower enabled. Travel uses the normal saved
Encounter rate Off control to isolate map behavior; earlier toggles keep visible
wilds enabled. No RAM fixtures are used in these milestone-20 runs. SoulSilver
uses HG-derived project progress, not a fresh story playthrough.

Cycling/Surf, all species/forms/shiny leads, restricted maps, story/partner/HM
cutscenes, all-fainted/egg-only party gameplay and long sessions still need wider
acceptance. Item-finding differences are tracked separately. This is an
experimental milestone; the complete enhancement goal remains unfinished.
See [exact evidence](../enhancements/milestone-20-verification.json).
