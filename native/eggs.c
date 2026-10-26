#include "settings.h"
extern int NativeDaycareStep(void *daycare, void *party, void *field);
extern u32 Party_GetCount(void *party);
extern void *Party_GetMonByIndex(void *party, u32 slot);
extern u32 GetMonData(void *mon, u32 attr, void *out);
extern void SetMonData(void *mon, u32 attr, const void *value);
struct FastEggState {
    void *save;
    u32 owner, steps, calls, forced, native_ready, empty, denied;
};
struct FastEggState gFastEggState;
_Static_assert(sizeof(struct FastEggState) == 32, "Fast egg diagnostic ABI");
int EnhancedDaycareStep(void *daycare, void *party, void *field) {
    /* Always retain parent EXP, breeding rolls, phone notifications, native
     * calendar/ability cycles and already-ready hatch results. The caller
     * counts the egg and starts the original standard hatch script. */
    int ready = NativeDaycareStep(daycare, party, field);
    struct FastEggState *s = &gFastEggState;
    ++s->calls;
    if (ready) ++s->native_ready;
    u32 owner;
    void *save = *(void **)((u8 *)field + 12);
    if (gEnhancedExtraOptions.fast_eggs != 1 ||
        EnhancedSettingsSaveData() != save || !EnhancedSettingsOwner(&owner)) {
        s->steps = 0;
        ++s->denied;
        return ready;
    }
    if (s->save != save || s->owner != owner) {
        s->save = save;
        s->owner = owner;
        s->steps = 0;
    }
    u32 count = Party_GetCount(party);
    void *egg = 0;
    if (count <= 6) {
        for (u32 i = 0; i < count; ++i) {
            void *mon = Party_GetMonByIndex(party, i);
            if (!GetMonData(mon, 3, 0) && GetMonData(mon, 76, 0)) {
                egg = mon;
                break;
            }
        }
    }
    if (!egg) {
        s->steps = 0;
        ++s->empty;
        return ready;
    }
    /* As in Emerald's optional five-step mode, progress belongs to walking
     * with any valid egg, not a PID. Menus, blocked movement and turning do
     * not call this hook. Party reordering does not erase walking progress. */
    if (++s->steps < 5) return ready;
    s->steps = 0;
    u32 cycles = 0;
    SetMonData(egg, 9, &cycles);
    ++s->forced;
    return 1;
}
