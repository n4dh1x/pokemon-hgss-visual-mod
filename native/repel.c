#include "settings.h"
#include "ui.h"

extern void *Save_Roamers_Get(void *save);
extern void *Save_Bag_Get(void *save);
extern int Bag_HasItem(void *bag, u16 item, u16 count, int heap);
extern int Bag_TakeItem(void *bag, u16 item, u16 count, int heap);
extern u32 GetItemAttr(u16 item, int attribute, int heap);
extern void OriginalStartScript(void *field, u16 script, void *object);
extern void PlaySE(u16 sequence);

struct RepelDialog {
    void *field;
    struct Window window;
    void *string;
    u32 active, phase, choice, item;
    u32 paused_before[2];
    u32 offered, accepted, declined, failures, remembered;
};
struct RepelDialog gEnhancedRepelDialog;
_Static_assert(sizeof(struct RepelDialog) == 68, "Repel dialog diagnostic ABI");
static void *ptr(void *p, unsigned offset) { return *(void **)((u8 *)p + offset); }
static int valid_item(u32 item) { return item == 76 || item == 77 || item == 79; }

u32 EnhancedRepelGetSteps(u16 item, int attribute, int heap) {
    u32 steps = GetItemAttr(item, attribute, heap);
    void *save = EnhancedSettingsSaveData();
    if (save && valid_item(item) && attribute == 2) {
        u8 *roamers = Save_Roamers_Get(save);
        /* Audited USA byte 0x66 is initialized to zero and has no native user.
         * Store with the normal game save, not the independently saved options.
         * Preserve unexpected data rather than reinterpret another mod's byte. */
        if (roamers[0x66] == 0 || valid_item(roamers[0x66])) {
            roamers[0x66] = (u8)item;
            ++gEnhancedRepelDialog.remembered;
        }
    }
    return steps;
}

static void print(const char *text, u32 x, u32 y) {
    EnhancedDrawText(&gEnhancedRepelDialog.window, gEnhancedRepelDialog.string, text, x, y);
}
static void render(void) {
    FillWindowPixelBuffer(&gEnhancedRepelDialog.window, 15);
    print("REPEL", 8, 2);
    if (gEnhancedRepelDialog.phase == 1) {
        print("Repel wore off.", 8, 24);
        print(gEnhancedRepelDialog.item == 76 ? "Use another Super Repel?" :
              gEnhancedRepelDialog.item == 77 ? "Use another Max Repel?" : "Use another Repel?", 8, 46);
        print("Yes", 32, 76);
        print("No", 128, 76);
        print("-", gEnhancedRepelDialog.choice ? 112 : 16, 76);
        print("A choose  B cancel", 8, 100);
    } else {
        if (gEnhancedRepelDialog.phase == 2)
            print(gEnhancedRepelDialog.item == 76 ? "You used Super Repel." :
                  gEnhancedRepelDialog.item == 77 ? "You used Max Repel." : "You used Repel.", 8, 46);
        else print("No matching Repel left.", 8, 46);
        print("A/B close", 8, 100);
    }
    CopyWindowToVram(&gEnhancedRepelDialog.window);
}
static int close_dialog(void) {
    EnhancedWindowClose(&gEnhancedRepelDialog.window, gEnhancedRepelDialog.string);
    EnhancedNpcPause(gEnhancedRepelDialog.field, gEnhancedRepelDialog.paused_before, 0);
    gEnhancedRepelDialog.active = 0;
    return 1;
}
int EnhancedRepelPromptTask(void *task) {
    (void)task;
    if (!gEnhancedRepelDialog.phase) {
        gEnhancedRepelDialog.string = EnhancedWindowOpen(gEnhancedRepelDialog.field,
            &gEnhancedRepelDialog.window, 2, 15);
        gEnhancedRepelDialog.phase = 1;
        render();
        return 0;
    }
    u32 keys = *(volatile u32 *)0x021D1154;
    if (gEnhancedRepelDialog.phase != 1) return (keys & 3) ? close_dialog() : 0;
    if ((keys & 2) || ((keys & 1) && gEnhancedRepelDialog.choice)) {
        ++gEnhancedRepelDialog.declined;
        return close_dialog();
    }
    if (keys & 1) {
        void *save = ptr(gEnhancedRepelDialog.field, 12);
        u32 item = gEnhancedRepelDialog.item;
        void *bag = Save_Bag_Get(save);
        /* Check again at acceptance. Never substitute a different Repel type. */
        if (Bag_HasItem(bag, (u16)item, 1, 11) && Bag_TakeItem(bag, (u16)item, 1, 11)) {
            u8 *roamers = Save_Roamers_Get(save);
            roamers[0x65] = (u8)GetItemAttr((u16)item, 2, 11);
            ++gEnhancedRepelDialog.accepted;
            gEnhancedRepelDialog.phase = 2;
            PlaySE(1535);
        } else {
            ++gEnhancedRepelDialog.failures;
            gEnhancedRepelDialog.phase = 3;
        }
        render();
    } else if (keys & 0xF0) {
        gEnhancedRepelDialog.choice ^= 1;
        render();
    }
    return 0;
}
void EnhancedRepelWoreOff(void *field, u16 script, void *object) {
    void *save = ptr(field, 12);
    u8 *roamers = Save_Roamers_Get(save);
    u16 item = roamers[0x66];
    if (script != 2022 || !gEnhancedOptions.repel_prompt || !valid_item(item) ||
        !Bag_HasItem(Save_Bag_Get(save), item, 1, 11) ||
        gEnhancedRepelDialog.active || ptr(field, 0x10)) {
        OriginalStartScript(field, script, object);
        return;
    }
    gEnhancedRepelDialog.field = field;
    gEnhancedRepelDialog.item = item;
    gEnhancedRepelDialog.active = 1;
    gEnhancedRepelDialog.phase = gEnhancedRepelDialog.choice = 0;
    ++gEnhancedRepelDialog.offered;
    EnhancedNpcPause(field, gEnhancedRepelDialog.paused_before, 1);
    FieldSystem_CreateTask(field, EnhancedRepelPromptTask, 0);
}
