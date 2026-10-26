#include "settings.h"
extern u32 NativeBattleRandom(void *battle);
extern u32 BattleSystem_GetBattleType(void *battle);
struct AlwaysCatchState { u32 calls, forced, native_roll, battle_type, denied; };
struct AlwaysCatchState gAlwaysCatchState;
_Static_assert(sizeof(struct AlwaysCatchState) == 20, "Always catch diagnostic ABI");
u32 EnhancedCatchRoll(void *battle) {
    /* This wrapper is installed only at the native ball-shake RNG call. All
     * eligibility checks, ball rules and successful-catch side effects remain
     * in the original code. Advance the original RNG once for each call. */
    u32 roll = NativeBattleRandom(battle);
    u32 type = BattleSystem_GetBattleType(battle), owner;
    ++gAlwaysCatchState.calls;
    gAlwaysCatchState.native_roll = roll;
    gAlwaysCatchState.battle_type = type;
    if (gEnhancedExtraOptions.always_catch == 1) {
        /* Singles, doubles/partner wilds, Safari, roamers and Bug Contest.
         * Trainer/link/Frontier/tutorial/Pal Park and unknown formats retain
         * native behavior. Tutorial/Pal Park return before this RNG call. */
        if (!(type & ~0x117Au) && EnhancedSettingsOwner(&owner)) {
            ++gAlwaysCatchState.forced;
            return 0;
        }
        ++gAlwaysCatchState.denied;
    }
    return roll;
}
