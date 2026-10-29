#include "settings.h"
extern u32 OriginalMoneyRead(void *profile);
extern u32 OriginalMoneySet(void *profile, u32 amount);
extern void *Save_PlayerData_GetProfile(void *save);
struct MoneyState {
    u32 calls, refills, full, denied, bookkeeping;
    void *profile;
    u32 before, after, caller;
};
struct MoneyState gMoneyState;
_Static_assert(sizeof(struct MoneyState) == 36, "Money diagnostic ABI");
u32 EnhancedMoneyRead(void *profile) {
    u32 value = OriginalMoneyRead(profile);
    u32 caller = (u32)__builtin_return_address(0) & ~1u;
    struct MoneyState *s = &gMoneyState;
    ++s->calls;
    s->profile = profile;
    s->before = value;
    s->caller = caller;
    if (gEnhancedExtraOptions.infinite_money == 1) {
        /* HGSS compares its pre-battle save profile with a copied post-battle
         * profile before depositing Mom's share. These are ledger reads, not
         * wallet access: refilling here would corrupt the native reward delta. */
        if (caller == 0x02052336u || caller == 0x0205233Eu) {
            ++s->bookkeeping;
        } else {
            void *save = EnhancedSettingsSaveData();
            u32 owner;
            if (save && profile == Save_PlayerData_GetProfile(save) &&
                EnhancedSettingsOwner(&owner)) {
                if (value != 999999u) {
                    value = OriginalMoneySet(profile, 999999u);
                    ++s->refills;
                } else ++s->full;
            } else ++s->denied;
        }
    }
    s->after = value;
    return value;
}
