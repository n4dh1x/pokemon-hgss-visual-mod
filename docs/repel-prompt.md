# Same-type repeat Repel — milestone 06

The SELECT menu now includes Repel prompt, default On. When the native effect
expires, it offers another of the last successfully used type: Repel, Super Repel
or Max Repel. Yes consumes exactly one matching item and restores its native
100/200/250 steps. No or B consumes nothing. Other types are never substituted;
disabled, unknown-type or exhausted-inventory cases use the original wear-off
message. The inventory is checked again before consumption. Native encounter
weights, level filtering and normal step countdown retain their behavior.

Successful normal bag use records the type in native SAVE_ROAMER byte `0x66`, next
to the step counter at `0x65`. The pinned native source and USA instructions audit
the 0x68-byte chunk, initialization and accessors: the byte is otherwise unused.
Normal saving couples this byte to the game's progress and checksum. Unknown
values are preserved; a legacy save with zero cannot infer a past type, so uses
the original message until another successful native Repel use. No journal or
save chunk is enlarged. A stale independent options record cannot change the
remembered consumable associated with an older game save.

The existing options journal adds value 3 plus reserved word 0 bit 0 as its presence
marker. Legacy records default the new option On; new records can save explicit
Off. Unknown values/formats remain guarded. Shared native window/font helpers
pause NPCs during either menu, then restore their prior pause flags.

## Verification

All 75 project tests pass, with no skips. Compiled ARM tests execute the hooked
native bag-use and step-expiry instructions for both USA baselines, validate
fingerprints before mutation, check all three durations, Yes/No/B, inventory loss,
unknown bytes, saved option migration and rejection of invalid settings. Four
field regressions also guard early A interaction after map/mode/context changes.

Mac melonDS DS 1.3.1 software runs with isolated project-created save copies show:

- Both games render the fourth setting and the same-type Super Repel prompt.
  Yes restores 200 steps and consumes only Super Repel; B consumes nothing.
  Paused roaming wilds resume when the dialog closes.
- Normal native Save and a cold boot restore 200 steps and the remembered Super
  Repel. Walking all 200 steps, without a countdown fixture, reaches the matching
  prompt in both games. The session's successful-use diagnostic is zero, proving
  this uses the saved type rather than a current-session bag-use event.
- Saved Off survives a cold boot in both games and expiry shows the native
  wear-off message. HeartGold accepts Max Repel for 250 steps; SoulSilver accepts
  normal Repel for 100. HeartGold with no Super Repel and two Max Repels falls back
  to the native message rather than substituting Max Repel.

Declared isolated RAM fixtures seed two of each item in an empty bag and shorten
the counter to one for branching checks. The separate full-duration runs use no
counter fixture. Original input saves/states are never edited; all ROM, save,
RAM, state and screenshot artifacts remain ignored and local. Bounded evidence
and hashes are in [milestone-06-verification.json](../enhancements/milestone-06-verification.json).

## Remaining acceptance

Milestone 07 implements the audited native bag restrictions. Safari permits the
bag; Bug-Catching Contest, Pal Park and Tower partner selection suppress the
prompt. Normal bag unlock/map restrictions also apply. Acceptance rechecks access.
All 78 tests pass, including native USA normal-menu and Tower instructions. Both
games pass natural saved expiry again and matched isolated bag-locked expiry
falls back to the native message. HeartGold also refuses without consumption
when bag permission is revoked during the prompt. Full story visits to every
special area remain pending; these controlled branches do not replace them. See
[milestone-07-verification.json](../enhancements/milestone-07-verification.json).

Broad older-save compatibility,
hardware, fresh SoulSilver story progression and every map/script context are not
established. The inventory therefore remains `integrated_untested` for complete
acceptance. This is an experimental milestone within the full enhancement goal.
