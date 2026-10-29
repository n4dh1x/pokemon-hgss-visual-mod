#include "settings.h"
#include "dex.h"
extern void *Save_PlayerData_GetProfile(void *save);
extern void *NativeSavePokedex(void *save);
extern void NativeDexNational(void *dex);
extern void NativeProfileNational(void *profile);
extern void NativeDexCaught(void *dex, void *mon);
extern u16 *NativeJohtoList(void);
extern void NativeCreateMon(void *, int, int, int, int, u32, int, u32);
extern void *Heap_Alloc(int heap, u32 size);
extern void Heap_Free(void *allocation);
extern void PlaySE(u16 sequence);

struct DexAction {
    void *field, *save, *dex, *profile;
    u32 owner, action, status, species, registered;
    void *mon;
    u16 *johto;
};
struct DexAction gDexAction;
_Static_assert(sizeof(struct DexAction) == 44, "Dex action diagnostic ABI");
static void release(void) {
    if (gDexAction.mon) Heap_Free(gDexAction.mon);
    if (gDexAction.johto) Heap_Free(gDexAction.johto);
    gDexAction.mon = 0;
    gDexAction.johto = 0;
}
static int owned(void *field, u32 *owner) {
    return field && EnhancedSettingsOwner(owner) &&
        *(void **)((u8 *)field + 12) == EnhancedSettingsSaveData();
}
int EnhancedDexBegin(void *field, u32 action) {
    struct DexAction *s = &gDexAction;
    u32 owner;
    if (s->status == 1 || action > 2 || !owned(field, &owner)) return 0;
    void *save = EnhancedSettingsSaveData();
    void *dex = NativeSavePokedex(save);
    if (!dex || *(u32 *)dex != 0xBEEFCAFEu) return 0;
    s->field = field; s->save = save; s->dex = dex;
    s->profile = Save_PlayerData_GetProfile(save);
    s->owner = owner; s->action = action;
    s->status = 0; s->species = 1; s->registered = 0;
    s->mon = 0; s->johto = 0;
    if (action != 1) {
        s->mon = Heap_Alloc(4, 236);
        if (!action) s->johto = NativeJohtoList();
        if (!s->mon || (!action && !s->johto)) {
            release(); s->status = 3; return 0;
        }
    }
    /* Mirror the original HGSS upgrade command, without story/game-clear flags.
     * Owning the Pokedex itself is still earned through the normal story. */
    if (action) {
        NativeDexNational(dex);
        NativeProfileNational(s->profile);
    }
    s->status = 1;
    return 1;
}
int EnhancedDexStep(void) {
    struct DexAction *s = &gDexAction;
    if (s->status != 1) return s->status == 2 ? 1 : -1;
    u32 owner;
    if (!owned(s->field, &owner) || owner != s->owner ||
        EnhancedSettingsSaveData() != s->save ||
        NativeSavePokedex(s->save) != s->dex || *(u32 *)s->dex != 0xBEEFCAFEu) {
        release(); s->status = 3; return -1;
    }
    if (s->action != 1) {
        while (s->species <= 493 && !s->action && !s->johto[s->species]) ++s->species;
        if (s->species <= 493) {
            /* A private, deterministic native-created Pokemon supplies valid
             * gender/form/language metadata. It never enters party or storage.
             * Fixed PID/IV/OT avoid advancing gameplay RNG. */
            NativeCreateMon(s->mon, s->species, 1, 0, 1, 1, 1, s->owner);
            NativeDexCaught(s->dex, s->mon); /* Native API sets seen too. */
            ++s->species; ++s->registered;
            return 0;
        }
    }
    release(); s->status = 2;
    PlaySE(0x5E1);
    return 1;
}
