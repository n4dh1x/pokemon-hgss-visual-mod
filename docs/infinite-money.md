# Saved Infinite money

Press SELECT in free field play, then X three times to reach Cheats, page 4.
Infinite money is the fourth row and defaults Off. Save and close applies the
choice; B/Cancel discards staging. Use the game's normal Save command to retain
progress and balances.

When enabled, reading the actual player's wallet refills its stored balance to
₽999,999 through the original capped money setter. This matches Emerald's
refill-on-read behavior. Spending still deducts the real price; the next eligible
wallet read restores the maximum. For example, buying one Potion first leaves
999699, then returning to the native shop refreshes the wallet to 999999. Turning
Off stops refills and keeps the current actual balance. No earlier balance is
restored. Casino coins, Battle Points and Mom's savings are separate currencies.

HGSS compares a pre-battle profile with a copied post-battle profile to calculate
Mom's share. Those internal ledger reads remain native, as do copied/opponent
profiles. A native 64 prize therefore still gives Mom 16 and adds 48 to the
wallet. A later wallet access refills only the player's wallet.

## Integration

The original getter is only four bytes. One guarded twenty-byte ARM9 change at
`0x02029024` shares two entry veneers and literal pointers with the adjacent setter.
Both original getter and capped setter are relocated byte for byte and aligned
in resident memory. The original maximum literal, add/subtract routines, avatar
getter and all surrounding bytes remain unchanged. Stack, return address,
arguments and callee-saved registers retain their native contract.

Both clean USA baselines independently match complete money/profile/Mom helper
fingerprints. The wrapper requires the actual saved profile pointer, loaded
setting and full owner identity; matching trainer IDs in a copied profile are
insufficient. Internal Mom caller returns `0x02052336`/`0x0205233E` bypass refills.
New-game initialization, native setter caps and spending arithmetic remain native.

Twenty options use 6/6/4/4 menu rows. Journal value 24/presence bit 131072 defaults
Off in earlier journals, preserving all nineteen previous choices and unknown
later slots. Version 1, 48 values, 256-byte pages and loader configuration size
stay fixed. Auxiliary/menu/wallet diagnostics are 56/132/36 bytes. The payload is
24,556 bytes, ends at `0x01FFEFEC`, and leaves 4,116 reserved ITCM bytes.

## Verification

256 regression tests pass. Seven wallet instruction tests cover real getter,
setter, add/subtract, saturation, ownership, copied profiles, Off after On,
neighboring currency bytes, ABI and the original Mom helper with controlled
external services. Forty-five settings tests cover durable storage and menus.
Both final ROMs/patches reproduce their tested experiments exactly.

Mac melonDS DS 1.3.1 acceptance in both games covers:

- Native Potion purchase for 300 and sale for 150, each changing quantity once.
- Cancel preserving purchase/sale balances and inventory; native quantity limits
  show 99 On versus 10 Off from the same 3064 starting wallet.
- Native two-Pokemon trainer battle, 64 prize, 16 Mom deposit and 48 wallet delta
  in both modes, with normal party EXP and native level screens completing.
- Trainer Card access after cold boot: 3112 becomes 999999 On and remains 3112
  Off; Mom's bank stays 16. Coins, Battle Points and other inventory stay intact.
- Native saving/cold reload of actual balances, inventories, party and choices;
  cold counters remain zero until wallet access. No periodic refill occurs.
- Settings Cancel preserving the entire cartridge save; older journals defaulting
  Money Off while retaining earlier settings.

The isolated native-VM fixtures insert MartBuy(0), MartSell or native Mom savings
SetFlag(0x986) plus TrainerBattle(Mikey47), then jump back to the follower script.
They change 10/8/18 unused script-stack bytes respectively plus a four-byte script
pointer. No wallet, bank, coins, BP, inventory, Pokemon, battle data or coordinates
are injected. Source saves are the declared HG-derived project lineage with
earlier legendary-release/location/ball fixtures. These checks do not establish
fresh story or universal save interchange compatibility.

Full-bag/insufficient-funds UI, other shop categories, losses/blackouts, Mom
purchases and wider story/link/Frontier contexts remain pending. These candidates
are experimental, and the full enhancement goal remains unfinished. See
[exact evidence](../enhancements/milestone-26-verification.json). Recheck local
accepted runs with `.venv/bin/python -B scripts/verify_money_milestone.py`.
