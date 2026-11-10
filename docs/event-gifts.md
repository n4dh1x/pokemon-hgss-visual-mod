# Event gifts and save overview

In the field, hold **SELECT + L** and release both buttons. Press **Y** in
Enhancements to see the trainer, badges and the names and levels of the current
party. Press **B** to return. Use the game's Save button to save your progress.

To enable gifts, go to **Cheats, page 4 → Dex / event gifts → Unlock event gifts**
and choose Yes. Talk to the delivery person in a Poké Mart with an open party
slot. The original delivery queue holds eight entries and refills as slots
become free. Save in-game to keep activation and delivery progress.

The 28-entry catalogue includes Mew, Celebi, Jirachi, Deoxys, Phione, a Manaphy
Egg, Darkrai, Shaymin and Arceus. Other entries include shiny Pichu, the shiny
legendary beasts, shiny Eevee and Milotic, three Pikachu variants, Scizor,
Crobat, Regigigas, the Enigma Stone and six Pokéwalker courses. Pokémon are
created in HGSS's native format for the current trainer. The existing event
scripts still govern what happens when you bring a gift to its story location.
The catalogue preserves an existing Enigma Stone delivery or story progress.

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
- OpenHome 1.17.1 opened a milestone-30 HeartGold save with a populated box and
  a separately started milestone-31 SoulSilver save with the correct title,
  trainer and Box 1. These were copied raw 512 KiB saves. The fresh SoulSilver
  box was empty at that checkpoint. Populated SoulSilver and event-gift
  transfer and write-back checks remain release work.
- Clean builds of both ROMs and their xdelta patches match the tested candidates
  byte for byte. See `enhancements/milestone-31-verification.json` for hashes
  and evidence references.

This milestone documents bounded Mac melonDS verification. Claim/refill across
the full native catalogue, original event story triggers, wider compatibility
and longer playthroughs are tracked in the release checklist.
