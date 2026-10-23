# Credits

| Who | What |
|---|---|
| **민트초크 (MinT ChoK)** | Original Pokémon Visual+ mod (Korean HG & Platinum) |
| **Young** | Battle background artwork (from the fan game *Pokémon Another Red*), used with permission in the original mod |
| **Josh MacDonald** | xdelta / VCDIFF |
| **KaioShin** | xdeltaUI front-end |
| **RoadrunnerWMC & contributors** | [ndspy](https://github.com/RoadrunnerWMC/ndspy) NDS library |
| **melonDS team** | melonDS emulator |
| **This repository** | English port analysis, tooling, variants, documentation |

Pokémon © Nintendo / Creatures Inc. / GAME FREAK inc. — this is an
unofficial fan project. See [Legal](legal.md).


The enhancement work uses the pinned [pret/pokeheartgold](https://github.com/pret/pokeheartgold)
decompilation as a native interface reference. The summary-viewer approach was
informed by [hg-engine](https://github.com/BluRosie/hg-engine), whose summary work
credits LheaRachel and Bubble. Exact audited revisions are in
[sources.lock.json](../enhancements/sources.lock.json).

Shiny odds follow Emerald 3DS patches 0022/0028's nominal roll choices. The HGSS
adaptation targets new native creation calls and retains the native shiny rule;
it does not transplant hg-engine's global compile-time shiny threshold.
