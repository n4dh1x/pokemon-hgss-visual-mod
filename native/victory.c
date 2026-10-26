#include "settings.h"
extern void NativeSelectionInput(void *battle, void *ctx);
extern void NativeGetBattleMon(void *battle, void *ctx);
extern u32 BattleSystem_GetBattleType(void *battle);
extern u32 NativeBattleSpecial(void *battle);
extern u32 NativeMaxBattlers(void *battle);
extern u32 NativeFieldSide(void *battle, u32 battler);
extern u32 NativeBattleOutcome(void *battle);
extern void NativeBattleOverlayMode(void *battle, u32 menu);
extern void NativeReadBattleScript(void *ctx, u32 narc, u32 script);
extern int NativeTryFaint(void *ctx, u32 next, u32 command, u32 flag);
extern int NativeGrantExperience(void *ctx, u32 next, u32 command);
extern int NativeCheckBattleOutcome(void *battle, void *ctx);
extern int NativeReplaceFainted(void *battle, void *ctx);
extern void NativeBattleContextInit(void *ctx);
extern void NativeResetTurn(void *battle, void *ctx);
struct InstantVictoryState {
    void *battle, *ctx;
    u32 pending, target, started, faints, grants, replacements;
    u32 completed, denied, deferred, abandoned;
};
struct InstantVictoryState gInstantVictoryState;
_Static_assert(sizeof(struct InstantVictoryState) == 48, "Instant victory diagnostic ABI");
static u32 word(void *p, u32 n) { return *(u32 *)((u8 *)p + n); }
static void put(void *p, u32 n, u32 value) { *(u32 *)((u8 *)p + n) = value; }
static int alive(void *ctx, u32 battler) {
    u32 hp = word(ctx, 0x2D8C + 192 * battler);
    return hp && hp <= word(ctx, 0x2D90 + 192 * battler);
}
void EnhancedVictoryGetBattleMon(void *battle, void *ctx) {
    /* A fresh native battle always starts at controller command zero. Clear
     * an interrupted handoff even if the native allocator reuses both pointers. */
    if (gInstantVictoryState.pending) ++gInstantVictoryState.abandoned;
    gInstantVictoryState.pending = 0;
    gInstantVictoryState.battle = battle;
    gInstantVictoryState.ctx = ctx;
    NativeGetBattleMon(battle, ctx);
}
void EnhancedVictorySelection(void *battle, void *ctx) {
    if (gInstantVictoryState.pending && gInstantVictoryState.battle == battle &&
        gInstantVictoryState.ctx == ctx) {
        /* Finish native HP/faint/EXP/replacement work before considering another
         * opponent. Native scripts return to command five after every wait. */
        if (NativeTryFaint(ctx, 5, 5, 1)) { ++gInstantVictoryState.faints; return; }
        if (NativeGrantExperience(ctx, 5, 5)) { ++gInstantVictoryState.grants; return; }
        if (NativeCheckBattleOutcome(battle, ctx)) {
            gInstantVictoryState.pending = 0;
            ++gInstantVictoryState.completed;
            return;
        }
        if (NativeReplaceFainted(battle, ctx)) { ++gInstantVictoryState.replacements; return; }
        /* Native turn-end cleanup, without incrementing real turn counters or
         * ticking field/status timers: no move or ordinary turn was taken. */
        NativeBattleContextInit(ctx);
        NativeResetTurn(battle, ctx);
        put(ctx, 8, 2); /* Native trainer message, entry abilities, then selection. */
        gInstantVictoryState.pending = 0;
        ++gInstantVictoryState.completed;
        return;
    }
    if (gInstantVictoryState.pending) {
        gInstantVictoryState.pending = 0;
        ++gInstantVictoryState.abandoned;
    }
    u32 owner;
    if (gEnhancedExtraOptions.instant_victory != 1) goto native;
    /* Keep trainer, ordinary/partner wild, roamer and contest formats. Exclude
     * link, facilities, Safari, tutorial, Pal Park, recordings and unknown flags. */
    if ((BattleSystem_GetBattleType(battle) & ~0x115Bu) ||
        (NativeBattleSpecial(battle) & 0x30) || !EnhancedSettingsOwner(&owner)) {
        ++gInstantVictoryState.denied;
        goto native;
    }
    u32 count = NativeMaxBattlers(battle);
    if ((count != 2 && count != 4) || NativeBattleOutcome(battle) ||
        word(ctx, 8) != 5 || ((u8 *)battle)[0x2445] != 1 || !alive(ctx, 0) || NativeFieldSide(battle, 0) != 0)
        goto defer;
    if ((word(ctx, 0x213C) & 0x0F000000u) || (word(ctx, 0x2140) & 0xF0000000u) ||
        word(ctx, 0x178)) goto defer;
    for (u32 i = 0; i < count; ++i) if (((u8 *)ctx)[i]) goto defer;
    u32 absent = ((u8 *)ctx)[0x3108];
    if (absent & 1) goto defer;
    for (u32 i = 0; i < count; ++i) {
        if ((absent & (1u << i)) || !alive(ctx, i) || NativeFieldSide(battle, i) != 1) continue;
        /* Selection uses overlay 10. HP/faint/ball scripts need overlay 7,
         * exactly as the native completed-selection path restores it. */
        NativeBattleOverlayMode(battle, 0);
        gInstantVictoryState.battle = battle;
        gInstantVictoryState.ctx = ctx;
        gInstantVictoryState.pending = 1;
        gInstantVictoryState.target = i;
        ++gInstantVictoryState.started;
        put(ctx, 0x64, 0); /* Native player attacker. */
        put(ctx, 0x6C, i);
        put(ctx, 0x118, i); /* MSG_BATTLER_TEMP used by native UpdateHP. */
        put(ctx, 0x215C, 0u - word(ctx, 0x2D8C + 192 * i));
        put(ctx, 0x213C, word(ctx, 0x213C) | 64); /* NO_BLINK skips type berries. */
        NativeReadBattleScript(ctx, 1, 2); /* Original UpdateHP, including TryFaint. */
        put(ctx, 8, 22);
        put(ctx, 12, 5);
        return;
    }
 defer:
    ++gInstantVictoryState.deferred;
 native:
    NativeSelectionInput(battle, ctx);
}
