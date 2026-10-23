# Party EXP progression — milestone 11

This expands verification of the unchanged milestone-10 candidate ROMs. Native
bench stat screens, multiple actual participants in HeartGold, and normal game
saving/cold reload pass in Mac melonDS DS 1.3.1. The 95-test regression baseline
and component/xdelta checks from milestone 10 remain applicable; no ROM code or
reward formula changes here.

The source is milestone 10's native HeartGold save: Chikorita has 207 EXP and
three level-2 party members each have 20 EXP, earned through the previous normal
victory. HeartGold continues its matching cold-loaded state. SoulSilver explicitly
imports a copy of that native save to exercise the same low-level fixture. This
checks the USA SS execution path, rather than an independent SS story playthrough
or general cross-title save compatibility. No RAM, Pokemon, EXP, level, badge or
item edits are used in milestone 11.

| Observation | HeartGold | SoulSilver |
|---|---|---|
| Native participants | Chikorita and switched-in Rattata | Chikorita |
| Chikorita EXP | 207→223 (+16) | 207→223 (+16) |
| Rattata EXP | 20→36 (+16, participant) | 20→28 (+8, bench) |
| Both Hoothoot EXP | 20→28 each (+8, bench) | 20→28 each (+8, bench) |
| Final party levels | 6 / 3 / 3 / 3 | 6 / 3 / 3 / 3 |
| Collective bench messages | One; one repeat suppressed | One; two repeats suppressed |
| Native game save and cold reload | Passed | Passed |

Both native reward tasks complete all four recipients. The original game presents
individual level-up messages and stat increase/total screens; the collective
message replaces only the bench gained-EXP lines. SoulSilver advances all three
bench members to level 3. HeartGold switches to Rattata through the native party
menu before victory: the actual participation mask is 3, and both participants
receive full 16 EXP. The two bench Hoothoot receive 8 each and show native stat
screens. Rattata also reaches level 3 through its full participant reward.

The native HP EVs change from 3/1/1/1 to 4/2/2/2. Rattata's HP grows from 13 to 15;
the two Hoothoot grow from 14 to 17 and 16 according to their existing stats.
All four party members' native EXP, level, HP, EVs, moves and PP survive normal
Save and a complete restart. Both settings journal pages are byte-identical before
and after native game saving. Sources remain unchanged; artifacts stay local.

Bench move learning/forgetting, evolution/cancellation, the actual multi-participant
SS case, held-item and wider battle-format emulator acceptance remain pending.
The broader enhancement inventory remains unfinished. Bounded inputs, fixture
provenance, hashes and native party values are recorded in
[milestone-11-verification.json](../enhancements/milestone-11-verification.json).
