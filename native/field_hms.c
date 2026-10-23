#include "config.h"

extern int NativePartySlotWithMove(void *ctx);
extern int NativeFirstPartyMove(void *party, u16 move);
extern u16 ScriptReadHalfword(void *ctx);
extern u16 *GetVarPointer(void *field, u16 variable);
extern u16 FieldSystem_VarGet(void *field, u16 variable);
extern void *SaveArray_Party_Get(void *save);
extern int Party_GetCount(void *party);
extern void *Party_GetMonByIndex(void *party, int slot);
extern u32 GetMonData(void *mon, int field, void *destination);
extern int GetMonTMHMCompat(void *mon, u8 tmhm);

struct FieldHmState {
    u32 scripts, checks, fallbacks, no_user, last_move, last_slot, compatible, disabled, cache_hits;
};
struct FieldHmState gFieldHmState;
_Static_assert(sizeof(struct FieldHmState) == 36, "Field HM diagnostic ABI");

static int hm_index(u16 move) {
    /* TM01..92 precede the eight HGSS HMs. No Dive; Flash remains a TM. */
    switch (move) {
    case 15: return 92;   /* Cut */
    case 19: return 93;   /* Fly */
    case 57: return 94;   /* Surf */
    case 70: return 95;   /* Strength */
    case 250: return 96;  /* Whirlpool */
    case 249: return 97;  /* Rock Smash */
    case 127: return 98;  /* Waterfall */
    case 431: return 99;  /* Rock Climb */
    default: return -1;
    }
}

/* Field input tests Waterfall every tick. Cache only immutable species/form
 * learnability, never the selected user, learned moves, HP, eggs or badges. */
struct HmCompatCache { u16 species, form; u32 known, compatible; };
static struct HmCompatCache compatibility[8];
static u32 next_compatibility;
static int compatible(void *mon, u16 species, int index) {
    u16 form = (u16)GetMonData(mon, 112, 0);
    u32 bit = index == 69 ? 1u << 8 : 1u << (index - 92);
    struct HmCompatCache *entry = 0;
    for (int i = 0; i < 8; ++i)
        if (compatibility[i].species == species && compatibility[i].form == form) {
            entry = &compatibility[i];
            break;
        }
    if (entry && (entry->known & bit)) {
        ++gFieldHmState.cache_hits;
        return !!(entry->compatible & bit);
    }
    int result = GetMonTMHMCompat(mon, (u8)index);
    if (!entry) {
        entry = &compatibility[next_compatibility++ & 7];
        entry->species = species;
        entry->form = form;
        entry->known = entry->compatible = 0;
    }
    entry->known |= bit;
    if (result) entry->compatible |= bit;
    return result;
}

static int first_user(void *party, u16 move, int tmhm) {
    ++gFieldHmState.checks;
    gFieldHmState.last_move = move;
    int original = NativeFirstPartyMove(party, move);
    if (!gEnhancedExtraOptions.field_hms || original != 255 || tmhm < 0) {
        if (!gEnhancedExtraOptions.field_hms) ++gFieldHmState.disabled;
        gFieldHmState.last_slot = original;
        return original;
    }
    int count = Party_GetCount(party), first = 255;
    if (count < 0 || count > 6) count = 0;
    for (int slot = 0; slot < count; ++slot) {
        void *mon = Party_GetMonByIndex(party, slot);
        u16 species = (u16)GetMonData(mon, 5, 0);
        if (!species || GetMonData(mon, 76, 0)) continue;
        if (first == 255) first = slot;
        if (compatible(mon, species, tmhm)) {
            first = slot;
            ++gFieldHmState.compatible;
            break;
        }
    }
    if (first == 255) ++gFieldHmState.no_user;
    else ++gFieldHmState.fallbacks;
    gFieldHmState.last_slot = first;
    return first;
}

int EnhancedFirstPartyMove(void *party, u16 move) {
    return first_user(party, move, hm_index(move));
}

int EnhancedBagFieldUser(void *party, u16 move) {
    return first_user(party, move, move == 148 ? 69 : hm_index(move));
}

int EnhancedPartySlotWithMove(void *ctx) {
    ++gFieldHmState.scripts;
    if (!gEnhancedExtraOptions.field_hms) {
        ++gFieldHmState.disabled;
        return NativePartySlotWithMove(ctx);
    }
    /* The original command reads exactly two u16 operands through these native
     * helpers. The surrounding field scripts retain badge/story gates, prompts,
     * animation and cancellation; Pokemon moves are never changed. */
    void *field = *(void **)((u8 *)ctx + 0x80);
    u16 *result = GetVarPointer(field, ScriptReadHalfword(ctx));
    u16 move = FieldSystem_VarGet(field, ScriptReadHalfword(ctx));
    int slot = EnhancedFirstPartyMove(SaveArray_Party_Get(*(void **)((u8 *)field + 12)), move);
    *result = slot < 6 ? slot : 6;
    return 0;
}
