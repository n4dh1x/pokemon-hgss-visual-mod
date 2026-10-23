#include "ui.h"

struct CheckData { u32 map; void *field, *object; u16 flags, padding; };
struct UseData { void *task; u16 slot, index; };
struct ItemUse { void *task; u16 item; u8 slot, padding; };
struct FieldBagState {
    void *field, *save;
    u32 item, active, slot, offered, accepted, cancelled, blocked, launched, response;
};
struct FieldBagState gFieldBagState;
_Static_assert(sizeof(struct FieldBagState) == 44, "Bag HM diagnostic ABI");
extern void NativeBagDrawContext(void *, u8 *, int);
extern void NativeBagSetCancel(void *, int);
extern void NativeBagHideCursor(void *);
extern int NativeBagCancelContext(void *);
extern u8 NativeBagPrintMessage(void *, int);
extern void NativeBagCreateYesNo(void *);
extern void NativeBagDestroyYesNo(void *);
extern int NativeYesNoInput(void *);
extern int NativeTextPrinterActive(u8);
extern void NativeAppFade(int, int);
extern void *String_New(u32, int);
extern void String_Delete(void *);
extern void *SaveArray_Party_Get(void *);
extern void *Save_Bag_Get(void *);
extern int Bag_HasItem(void *, u16, u16, int);
extern int EnhancedBagFieldUser(void *, u16);
extern void *NativeFieldMoveFunction(u32, u16);
extern void *NativeTaskField(void *);
extern void *NativeTaskEnvironment(void *);
extern void NativeItemUseTMHM(struct ItemUse *, const void *);
extern void *NativeReopenBag(void *, void *);
extern void NativeStartMenuExit(void *, void *);
extern int NativeBagReturn(void *);
extern int NativeFlyReturn(void *);
extern void Heap_FreeExplicit(int, void *);

static void *ptr(void *p, u32 offset) { return *(void **)((u8 *)p + offset); }
static u16 half(void *p, u32 offset) { return *(u16 *)((u8 *)p + offset); }
static int index_for(u16 item) { return item == 421 ? 1 : item == 397 ? 7 : -1; }
static u16 move_for(u16 item) { return item == 421 ? 19 : 148; }
static void *bag_field(void *view) {
    void *check = ptr(view, 0x70);
    return check ? ptr(check, 20) : 0;
}
static u32 check_use(void *field, u16 item, struct CheckData *check, int *slot) {
    int index = index_for(item);
    /* Bag uses the native start-menu snapshot: the field overlay may be
     * unloaded while the Bag overlay is active, so never query its terrain. */
    if (!field || index < 0 || !gEnhancedExtraOptions.field_hms) return 1;
    void *save = ptr(field, 12);
    if (!Bag_HasItem(Save_Bag_Get(save), item, 1, 11)) return 1;
    *slot = EnhancedBagFieldUser(SaveArray_Party_Get(save), move_for(item));
    if (*slot >= 6) return 6;
    if (check->field != field) return 1;
    u32 result = ((u32 (*)(const struct CheckData *))NativeFieldMoveFunction(1, index))(check);
    return result;
}
static int error(void *app, u32 response) {
    gFieldBagState.active = 0;
    ++gFieldBagState.blocked;
    gFieldBagState.response = response;
    const char *message = response == 2 ? "You need the proper Badge." :
        response == 3 ? "You cannot use this with a companion." :
        response == 5 ? "You cannot use this right now." :
        response == 6 ? "You need a Pokemon in your party." : "You cannot use this here.";
    EnhancedCopyText(ptr(app, 0x5E4), message);
    *((u8 *)app + 0x616) = NativeBagPrintMessage(app, 0);
    return 12; /* Native error-message wait and Bag cleanup. */
}
int EnhancedBagFieldPrompt(void *app) {
    u8 *state = (u8 *)app + 0x67B;
    void *view = ptr(app, 0x234);
    u16 item = half(view, 0x66);
    if (*state == 0) {
        EnhancedCopyText(ptr(app, 0x5E4), item == 421 ? "Use FLY now?" : "Use FLASH now?");
        *((u8 *)app + 0x616) = NativeBagPrintMessage(app, 0);
        *state = 1;
    } else if (*state == 1) {
        if (!NativeTextPrinterActive(*((u8 *)app + 0x616))) {
            NativeBagCreateYesNo(app);
            *state = 2;
        }
    } else if (*state == 2) {
        int response = NativeYesNoInput(ptr(app, 0x804));
        if (response != 1 && response != 2) return 13;
        NativeBagDestroyYesNo(app);
        if (response == 2) {
            ++gFieldBagState.cancelled;
            gFieldBagState.active = 0;
            int next = NativeBagCancelContext(app);
            NativeBagSetCancel(app, 1);
            return next;
        }
        struct CheckData check = *(struct CheckData *)((u8 *)ptr(view, 0x70) + 24);
        int slot = 255;
        void *field = bag_field(view);
        u32 result = check_use(field, item, &check, &slot);
        if (result) return error(app, result);
        /* One-shot intent bridges only the native Bag -> start-menu callback.
         * The real native task environment owns the subsequent Fly/Flash use. */
        gFieldBagState.field = field;
        gFieldBagState.save = ptr(field, 12);
        gFieldBagState.item = item;
        gFieldBagState.slot = slot;
        gFieldBagState.active = 1;
        ++gFieldBagState.accepted;
        *(u16 *)((u8 *)view + 0x68) = 0; /* USE_ON_PARTYMON */
        NativeAppFade(1, 6);
        return 37; /* Native fade completion and Bag teardown. */
    }
    return 13;
}
int EnhancedBagFieldSelect(void *app) {
    NativeBagSetCancel(app, 0);
    NativeBagHideCursor(app);
    gFieldBagState.active = 0;
    void *view = ptr(app, 0x234);
    struct CheckData check = *(struct CheckData *)((u8 *)ptr(view, 0x70) + 24);
    int slot = 255;
    u32 response = check_use(bag_field(view), half(view, 0x66), &check, &slot);
    if (response) return error(app, response);
    ++gFieldBagState.offered;
    *((u8 *)app + 0x67B) = 0;
    *(int (**)(void *))((u8 *)app + 0x67C) = EnhancedBagFieldPrompt;
    return 13;
}
void EnhancedBagDrawContext(void *app, u8 *indices, int count) {
    void *view = ptr(app, 0x234);
    /* The original USA menu never assigns the Japan-only action 9. Reuse its
     * existing string/callback slot; retain all five native button bounds. */
    if (gEnhancedExtraOptions.field_hms && count == 5 && indices[1] == 255 &&
        *((u8 *)view + 0x65) == 0 && index_for(half(view, 0x66)) >= 0 &&
        (half(view, 0x76) >> 1) != 2 && (half(view, 0x76) >> 1) != 3) {
        void *label = String_New(32, 6);
        if (label) {
            EnhancedCopyText(label, "USE NOW");
            String_Delete(ptr(app, 0x300 + 9 * 4));
            *(void **)((u8 *)app + 0x300 + 9 * 4) = label;
            indices[1] = 9;
            *(int (**)(void *))((u8 *)app + 0x7F4) = EnhancedBagFieldSelect;
        }
    }
    NativeBagDrawContext(app, indices, count);
}
int EnhancedBagFlyReturn(void *task) {
    void *menu = NativeTaskEnvironment(task);
    void *map = ptr(menu, 0x380);
    if (*(u32 *)((u8 *)map + 0x14)) return NativeFlyReturn(task);
    /* Native party-launched Fly returns to the party screen on cancel. This
     * Bag-launched flow returns to its Bag instead, freeing the same owners. */
    Heap_FreeExplicit(11, ptr(menu, 0x384));
    Heap_FreeExplicit(11, map);
    *(void **)((u8 *)menu + 0x384) = 0;
    ++gFieldBagState.cancelled;
    void *field = NativeTaskField(task);
    *(void **)((u8 *)menu + 0x380) = NativeReopenBag(field, (u8 *)menu + 0x358);
    NativeStartMenuExit(menu, NativeBagReturn);
    return 0;
}
void EnhancedItemUseTMHM(struct ItemUse *data, const void *checkData) {
    if (!gFieldBagState.active || data->item != gFieldBagState.item) {
        gFieldBagState.active = 0;
        NativeItemUseTMHM(data, checkData);
        return;
    }
    gFieldBagState.active = 0;
    void *field = NativeTaskField(data->task);
    void *menu = NativeTaskEnvironment(data->task);
    struct CheckData *check = (struct CheckData *)((u8 *)menu + 0x370);
    int slot = 255;
    u32 result = field == gFieldBagState.field && ptr(field, 12) == gFieldBagState.save ?
        check_use(field, data->item, check, &slot) : 1;
    gFieldBagState.response = result;
    if (result) {
        ++gFieldBagState.blocked;
        *(void **)((u8 *)menu + 0x380) = NativeReopenBag(field, (u8 *)menu + 0x358);
        NativeStartMenuExit(menu, NativeBagReturn);
        return;
    }
    struct UseData use = {data->task, (u16)slot, (u16)index_for(data->item)};
    gFieldBagState.slot = slot;
    ++gFieldBagState.launched;
    ((void (*)(struct UseData *, const struct CheckData *))NativeFieldMoveFunction(0, use.index))(&use, check);
    if (use.index == 1)
        NativeStartMenuExit(menu, EnhancedBagFlyReturn);
}
