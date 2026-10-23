# Field moves without learning the move

Milestone 12 begins this feature. On page 2 of the SELECT enhancement menu,
Field HMs defaults On. The contextual script command and native Surf/Waterfall
input checks can choose a party member without requiring a learned HM move.
An actual learned user takes priority; otherwise a compatible non-egg species is
preferred, falling back to the first non-egg party member. Native field use can
select fainted members. No moves, HP, badges or story flags are edited.

Native scripts retain their badge/story gates, prompts and animations. Cut,
Surf, Strength, Whirlpool, Rock Smash, Waterfall and Rock Climb use contextual
checks. Fly needs its own Bag/menu entry; Flash is a TM in HGSS and also needs
menu integration. Dive is absent. This is not complete field-HM acceptance.

The installer checks exact original function fingerprints in both USA ROMs,
changes one script-command pointer and two overlay calls, and rejects unexpected
bytes. Tests execute both original command paths and compatibility instructions
against each ROM's unchanged personal data, checking all eight HM indices,
learned-user priority, variable operands, eggs, empty/fainted parties and Off.
Compatibility caching uses only immutable species/form data; live party choice
and learned moves are rechecked. Mac runs execute the live fallback with cache
hits and display/load the setting. Full native use, badge rejection, animations,
cancellation and transitions still require emulator verification.

See [milestone-12-verification.json](../enhancements/milestone-12-verification.json).
