# Event gifts and save overview

In the field, hold **SELECT + L** and release both buttons. Press **Y** in
Enhancements to see the trainer, badges and the names and levels of the current
party. Press **B** to return. Use the game's Save button to save your progress.

Go to **Cheats, page 4 → Dex / event gifts → Choose event gifts**. Browse
with Left/Right or L/R and press **A** to queue the displayed gift. Press
**B** to go back. Claim it from the delivery person in a Poké Mart, then use
the normal Save button to keep your progress. Pokémon and eggs need a free
party slot. The queue can hold eight gifts at a time.

Each catalogue gift can be queued once. Saves from the earlier bulk mode
retain the gifts already queued and the catalogue entries already marked.
Choose any remaining entries individually in the picker.

The 28-entry catalogue includes Mew, Celebi, Jirachi, Deoxys, Phione, a Manaphy
Egg, Darkrai, Shaymin and Arceus. Other entries include shiny Pichu, the shiny
legendary beasts, shiny Eevee and Milotic, three Pikachu variants, Scizor,
Crobat, Regigigas, the Enigma Stone and six Pokéwalker courses. Pokémon are
created in HGSS's native format for the current trainer. The existing event
scripts still govern what happens when you bring a gift to its story location.
The catalogue preserves an existing Enigma Stone delivery or story progress.

## Milestone 33 picker verification

Both games showed the original names in the picker. HeartGold queued Amity
Meadow and SoulSilver queued Celebi. Each save contained exactly the selected
entry after a normal Save and cold restart. The menu refused to queue a second
copy. HeartGold also redeemed Amity Meadow through the original delivery
NPC. The course survived a normal Save and cold restart, and the picker
refused to queue it again. All 28 catalogue entries passed the compiled queue tests, including
duplicate courses and a full queue. See [milestone 33 verification](../enhancements/milestone-33-verification.json).

The full milestone 33 suite passed 319 tests. On a separately started
SoulSilver save, the Poké Mart delivered the selected Lv. 50 Celebi.
The same Pokémon remained in the party after a normal Save and cold restart.

In SoulSilver, the Ilex Shrine showed its normal text before the Radio Tower
gate. A declared test fixture supplied that one story flag and transported
the trainer to the shrine. The original cutscene travelled through Route 22
to Tohjo Falls and started Giovanni's battle. Battle victory and the return
scene still need verification.

On a separate branch, the original NPC delivered the Enigma Stone, and
Pewter Museum exchanged it for Soul Dew. The original Pewter scripts then
started the Lv. 40 Latias encounter. The museum and exterior fixtures
used the original Warp command for travel.

The picker currently rotates the labels for the three Pikachu variants.
The saved queue contains the expected Fly, Surf and Volt Tackle moves.
The labels need correction before release.

The English Wonder Card archive also identifies four distinct gifts missing
from the current catalogue. Those are Kyle Riolu, Pokétopia Electivire,
Pokétopia Magmortar, and Oblivia Heatran. The gift catalogue audit remains open.
[Archived English Generation IV cards](https://github.com/projectpokemon/EventsGallery/tree/master/Released/Gen%204/Wondercards/ENG)

## Milestone 31 verification

- 317 automated tests pass. The new event tests exercise catalogue refill,
  repeat protection, incompatible save flags, retry after insertion failure,
  Wonder Card preservation and an existing Enigma Stone story.
- In both games, the save overview renders the trainer, badge count and six
  party entries. The first eight gifts queue through the normal field menu,
  and the queue persists through the original Save and a cold restart.
  Original Pokémon getters confirm valid checksums, distinct IDs and Jirachi's
  move PP. The Wonder Card data matches before and after activation.
- In HeartGold, the original Poké Mart NPC rejects a full party and leaves the
  queue intact. A test-only native warp brought the trainer to the shop. The
  fixture edits the script pointer and unused script stack, while delivery uses
  the game's actual NPC and existing party and save data.
  After a normal PC deposit and return to the mart, the NPC delivered Mew
  at Lv. 5 and the queue added Arceus. The original Save and cold restart
  kept Mew, the other five party members, Togepi in the PC and the refilled
  queue. Wonder Cards and the other seven queued gifts matched exactly.
- In a separately started SoulSilver game, the original delivery NPC gave the
  trainer a Lv. 5 Mew and the queue refilled with Arceus. The other seven gifts
  and Wonder Cards matched exactly. After a normal PC deposit, Save and cold
  restart, Chikorita remained in the party and the delivered Mew was in Box 1.
  The test used the same kind of native warp fixture to reach the Poké Mart.
- In SoulSilver, the native delivery NPC then gave Arceus and shiny Pichu,
  and the queue refilled through Raikou while preserving the other seven
  gifts and Wonder Cards. Arceus as the lead activated the Ruins of Alph
  researcher scene, which reached the Mystri Stage and Sinjoh exterior.
  Shiny Pichu as the lead activated the Ilex Shrine scene, which awarded
  Lv. 30 Spiky-eared Pichu. The reward and completed scene survived the
  original Save and a cold restart. Travel fixtures used the original Warp
  command to reach the event entrances. The player used the original party
  menu, trigger tile and shrine interaction.
- OpenHome 1.17.1 opened a populated milestone-30 HeartGold save and the
  milestone-31 SoulSilver save with the delivered Mew in Box 1. The app
  recognized both titles from copied raw 512 KiB cartridge saves. The
  SoulSilver copy was byte-identical after import. A headless test of the
  OpenHome v1.18.1 storage writer moved Mew in SoulSilver and Togepi in
  HeartGold from slot 1 to slot 2 of Box 1. Both games cold-booted the edited
  saves with the same party, queued gifts and Wonder Cards. The writer
  changed only the two PC records and the storage checksum. The harness
  kept each Pokémon's PK4 payload intact. GUI write-back and moving Pokémon
  between saves remain release work.
- Clean builds of both ROMs and their xdelta patches match the tested candidates
  byte for byte. See `enhancements/milestone-31-verification.json` for hashes
  and evidence references.

This milestone documents bounded Mac melonDS verification. Claim/refill across
the full native catalogue, original event story triggers, wider compatibility
and longer playthroughs are tracked in the release checklist.
