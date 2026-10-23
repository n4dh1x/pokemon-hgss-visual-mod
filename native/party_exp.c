#include "config.h"

extern int NativeCalcExperience(void *battle, void *ctx);
extern void NativeExperienceTask(void *task, void *data);
extern u32 BattleSystem_GetBattleType(void *battle);
extern void *BattleSystem_GetOpponentData(void *battle, int battler);
extern void *BattleSystem_GetParty(void *battle, int battler);
extern int Party_GetCount(void *party);
extern void *Party_GetMonByIndex(void *party, int slot);
extern u32 GetMonData(void *mon, int field, void *destination);
extern u32 GetMonBaseStat(u16 species, int attribute);
extern u32 EnhancedUnsignedDivide(u32 numerator, u32 denominator);
extern int NativeScriptReadWord(void *ctx);
extern void NativeScriptIncrement(void *ctx, int distance);
extern u32 NativePrintBattleMessage(void *battle, void *loader, void *msg, u8 delay);

struct PartyExperienceState {
    void *work, *ctx;
    u32 active, participants, full, half, side, slot, bench, shown, printer;
    u32 started, completed, groups, suppressed, recipients, calculations;
};
struct PartyExperienceState gPartyExperience;
_Static_assert(sizeof(struct PartyExperienceState) == 68, "Party EXP diagnostic ABI");
static u32 word(void *p, unsigned n) { return *(u32 *)((u8 *)p + n); }
static void *ptr(void *p, unsigned n) { return *(void **)((u8 *)p + n); }
static void put(void *p, unsigned n, u32 v) { *(u32 *)((u8 *)p + n) = v; }
static int eligible(void *mon) {
    return GetMonData(mon, 5, 0) && !GetMonData(mon, 76, 0) && GetMonData(mon, 163, 0);
}

int EnhancedCalcExperience(void *battle, void *ctx) {
    if (!gEnhancedOptions.party_exp) return NativeCalcExperience(battle, ctx);
    u32 type = BattleSystem_GetBattleType(battle), enemy = word(ctx, 0x74);
    void *opponent = enemy < 4 ? BattleSystem_GetOpponentData(battle, enemy) : 0;
    NativeScriptIncrement(ctx, 1);
    int jump = NativeScriptReadWord(ctx);
    if (opponent && (((u8 *)opponent)[0x195] & 1) && !(type & 0x2A4)) {
        u8 *mon = (u8 *)ctx + enemy * 192;
        u32 total = EnhancedUnsignedDivide(GetMonBaseStat(*(u16 *)(mon + 0x2D40), 9) * mon[0x2D74], 7);
        put(ctx, 0x9C, total ? total : 1);
        put(ctx, 0xA0, total / 2 ? total / 2 : 1);
        ++gPartyExperience.calculations;
    } else NativeScriptIncrement(ctx, jump);
    return 0;
}

void EnhancedPartyExperienceTask(void *task, void *data) {
    if (!gEnhancedOptions.party_exp) {
        NativeExperienceTask(task, data);
        return;
    }
    void *ctx = ptr(data, 4), *battle = ptr(data, 0);
    u32 side = (word(ctx, 0x74) >> 1) & 1;
    if (!gPartyExperience.active || gPartyExperience.work != data || gPartyExperience.ctx != ctx) {
        gPartyExperience.work = data;
        gPartyExperience.ctx = ctx;
        gPartyExperience.active = 1;
        gPartyExperience.participants = word(ctx, 0xA4 + side * 4);
        gPartyExperience.full = word(ctx, 0x9C);
        gPartyExperience.half = word(ctx, 0xA0);
        gPartyExperience.side = side;
        gPartyExperience.shown = gPartyExperience.bench = 0;
        ++gPartyExperience.started;
    }
    void *party = BattleSystem_GetParty(battle, 0);
    int count = Party_GetCount(party);
    if (count < 0 || count > 6) count = 0;
    u32 slot = word(data, 0x48);
    while (slot < (u32)count && !eligible(Party_GetMonByIndex(party, slot))) ++slot;
    put(data, 0x48, slot);
    u32 saved_mask = word(ctx, 0xA4 + side * 4);
    u32 saved_full = word(ctx, 0x9C), saved_half = word(ctx, 0xA0);
    gPartyExperience.slot = slot;
    gPartyExperience.bench = slot < (u32)count && !(gPartyExperience.participants & (1u << slot));
    /* Let the native task select this recipient. A held EXP Share adds zero;
     * Lucky Egg/trade/trainer modifiers, EVs, levels and moves remain native. */
    put(ctx, 0xA4 + side * 4, slot < (u32)count ? (1u << slot) : 0);
    put(ctx, 0x9C, gPartyExperience.bench ? gPartyExperience.half : gPartyExperience.full);
    put(ctx, 0xA0, 0);
    NativeExperienceTask(task, data);
    if (!ptr(ctx, 0x178)) {
        /* Native completion freed data and task. Never inspect data here. */
        put(ctx, 0xA4 + side * 4, 0);
        gPartyExperience.active = gPartyExperience.bench = 0;
        ++gPartyExperience.completed;
    } else {
        if (word(data, 0x48) > slot) {
            saved_mask &= ~(1u << slot);
            ++gPartyExperience.recipients;
        }
        put(ctx, 0xA4 + side * 4, saved_mask);
    }
    put(ctx, 0x9C, saved_full);
    put(ctx, 0xA0, saved_half);
}

u32 EnhancedExperienceMessage(void *battle, void *loader, void *message, u8 delay) {
    if (gPartyExperience.active && gPartyExperience.bench) {
        if (gPartyExperience.shown) {
            ++gPartyExperience.suppressed;
            return gPartyExperience.printer;
        }
        /* Appended English battle-bank string, guarded by the builder. */
        volatile u32 group[9];
        for (int i = 0; i < 9; ++i) group[i] = 0;
        ((volatile u16 *)group)[1] = 1276;
        gPartyExperience.printer = NativePrintBattleMessage(battle, loader, (void *)group, delay);
        gPartyExperience.shown = 1;
        ++gPartyExperience.groups;
        return gPartyExperience.printer;
    }
    return NativePrintBattleMessage(battle, loader, message, delay);
}
