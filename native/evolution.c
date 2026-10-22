#include "config.h"

/* These declarations use the original USA HGSS ABI. No Pokemon/save layouts
 * are redefined or replaced. Addresses are checked by the injector. */
struct Evolution {
    u16 method;
    u16 parameter;
    u16 target;
};

extern u16 OriginalEvolution(void *party, void *mon, u8 context, u16 used_item,
                             int *method_out);
extern u32 GetMonData(void *mon, int field, void *destination);
extern u32 GetItemAttr(u16 item, int attribute, int heap);
extern void LoadMonEvolutionTable(u16 species, struct Evolution *table);

__attribute__((section(".enhanced_config"), used))
volatile struct EnhancedOptions gEnhancedOptions = {
    0x48534745u, 1, 1, 1, 1, {0, 0, 0}
};

enum {
    MON_SPECIES = 5, MON_HELD_ITEM = 6, MON_IS_EGG = 76, MON_LEVEL = 161,
    EVO_LEVEL_CONTEXT = 0, EVO_TRADE = 5, EVO_TRADE_ITEM = 6,
    ITEM_HOLD_EFFECT = 1, HOLD_NO_EVOLVE = 0x40, KADABRA = 64
};

u16 EnhancedEvolution(void *party, void *mon, u8 context, u16 used_item,
                      int *method_out)
{
    /* Existing behavior runs first and remains the fallback. A matching held
     * trade item at level 40 takes precedence: Slowpoke can then choose
     * Slowking instead of its otherwise eligible Slowbro level evolution. */
    u16 original = OriginalEvolution(party, mon, context, used_item, method_out);
    if (context != EVO_LEVEL_CONTEXT || !gEnhancedOptions.trade_evolutions)
        return original;

    if (GetMonData(mon, MON_IS_EGG, 0) || GetMonData(mon, MON_LEVEL, 0) < 40)
        return original;

    u16 species = (u16)GetMonData(mon, MON_SPECIES, 0);
    u16 held_item = (u16)GetMonData(mon, MON_HELD_ITEM, 0);
    if (species != KADABRA && GetItemAttr(held_item, ITEM_HOLD_EFFECT, 0) == HOLD_NO_EVOLVE)
        return original;

    struct Evolution table[7];
    LoadMonEvolutionTable(species, table);
    for (unsigned i = 0; i < 7; ++i) {
        const struct Evolution *entry = &table[i];
        if (entry->target &&
            (entry->method == EVO_TRADE ||
             (entry->method == EVO_TRADE_ITEM && held_item && held_item == entry->parameter))) {
            if (method_out)
                *method_out = entry->method;
            /* Native evolution completion consumes held items for method 6;
             * cancellation never reaches that completion path. */
            return entry->target;
        }
    }
    return original;
}
