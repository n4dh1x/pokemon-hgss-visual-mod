# Capture progression and save persistence — milestone 09

These checks expand verification of the unchanged milestone 08 candidates. No
new ROM or reward patch is needed. Both games use ordinary bag inputs and the
remaining Master Balls from the declared milestone 08 isolated fixture. Pokemon
data, EXP and levels are never edited for these checks.

| Observation | HeartGold | SoulSilver |
|---|---|---|
| Chikorita EXP across captures | 135→151→167→183 | 135→159→191 |
| Resulting level / HP | 6 / 22 | 6 / 22 |
| Native stat increase screens | Passed | Passed |
| Razor Leaf learned into empty slot | Move 75, 25 PP | Move 75, 25 PP |
| Native EXP child tasks started/completed | 3/3 | 2/2 |
| Native game save and cold reload | Passed | Passed |
| Stored party members after reload | 4 | 3 |

Both native stat summary screens advance normally. The original task learns
Razor Leaf and then resumes capture registration/nickname/storage. Original
participation rules keep the previously captured, nonparticipating Pokemon at
their existing EXP. Chikorita retains Tackle/Growl and gains Razor Leaf; the new
move has its normal PP. HG gains two HP EVs and one Speed EV over these captures;
SS gains one HP EV and one Speed EV.

The normal game Save command and a complete cold restart preserve all party
members and their native EXP, EVs, level, HP, moves and PP. Both enhancement
journal pages remain byte-identical across native saving. The native party
inspector executes original getter instructions on private RAM copies and now
reports move IDs/PP. No Pokemon layout or encryption is reimplemented.

Earlier UI checkpoints include pending nickname prompts and old saved-party
copies while the battle is still active. Only the completed field checkpoints
and cold reloads establish stored-party persistence. HG's earlier milestone 08
post-capture checkpoint had already entered a second visible-wild battle; that
exact native encounter is used here for the second capture.

Full movesets/forgetting, evolution/cancellation, held EXP Share/Lucky Egg, level
100, failed throws, full party/PC storage, full double/roamer/special-area flows
and hardware remain pending. These checks do not establish complete enhancement
parity. The 85-test suite and original component/xdelta checks from milestone 08
remain applicable because the ROM code is unchanged. Bounded input sequences,
artifact hashes and native party values are recorded in
[milestone-09-verification.json](../enhancements/milestone-09-verification.json).
