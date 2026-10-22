#include "settings.h"
#include "ui.h"

struct MenuState {
    void *field;
    struct Window window;
    void *string;
    u32 active, phase, row, trade, tms, visible, repel, capture, error;
    u32 paused_before[2];
};
struct MenuState gEnhancedMenu;
_Static_assert(sizeof(struct MenuState) == 68, "Menu diagnostic ABI");
static void *ptr(void *p, unsigned offset) { return *(void **)((u8 *)p + offset); }
static void print(const char *text, u32 x, u32 y) {
    EnhancedDrawText(&gEnhancedMenu.window, gEnhancedMenu.string, text, x, y);
}
static void render(void) {
    static const char *modes[4] = {"Off", "Few", "Some", "Many"};
    FillWindowPixelBuffer(&gEnhancedMenu.window, 15);
    print("ENHANCEMENTS", 8, 2);
    print("Visible wilds", 16, 28);
    print(modes[gEnhancedMenu.visible], 172, 28);
    print("Trade evolution", 16, 46);
    print(gEnhancedMenu.trade ? "On" : "Off", 172, 46);
    print("Reusable TMs", 16, 64);
    print(gEnhancedMenu.tms ? "On" : "Off", 172, 64);
    print("Repel prompt", 16, 82);
    print(gEnhancedMenu.repel ? "On" : "Off", 172, 82);
    print("EXP for catching", 16, 100);
    print(gEnhancedMenu.capture ? "On" : "Off", 172, 100);
    print("Save and close", 16, 118);
    print("Cancel", 16, 136);
    print("-", 2, 28 + 18 * gEnhancedMenu.row);
    if (gEnhancedMenu.phase == 2) print("Saving settings", 8, 158);
    else if (gEnhancedMenu.error) print("Settings storage unavailable", 8, 158);
    else print("Left/Right change  A choose", 8, 158);
    CopyWindowToVram(&gEnhancedMenu.window);
}
static int close_menu(void) {
    EnhancedWindowClose(&gEnhancedMenu.window, gEnhancedMenu.string);
    EnhancedNpcPause(gEnhancedMenu.field, gEnhancedMenu.paused_before, 0);
    gEnhancedMenu.active = 0;
    return 1;
}
int EnhancedMenuTask(void *task) {
    (void)task;
    if (gEnhancedMenu.phase == 0) {
        gEnhancedMenu.string = EnhancedWindowOpen(gEnhancedMenu.field, &gEnhancedMenu.window, 1, 22);
        gEnhancedMenu.phase = 1;
        render();
        return 0;
    }
    if (gEnhancedMenu.phase == 2) {
        if (EnhancedSettingsStore(gEnhancedMenu.trade, gEnhancedMenu.tms, gEnhancedMenu.visible, gEnhancedMenu.repel, gEnhancedMenu.capture))
            return close_menu();
        gEnhancedMenu.phase = 1;
        gEnhancedMenu.error = 1;
        render();
        return 0;
    }
    u32 keys = *(volatile u32 *)0x021D1154;
    if (keys & 2) return close_menu();
    int redraw = 0;
    if (keys & 0x40) { gEnhancedMenu.row = gEnhancedMenu.row ? gEnhancedMenu.row - 1 : 6; redraw = 1; }
    if (keys & 0x80) { gEnhancedMenu.row = gEnhancedMenu.row == 6 ? 0 : gEnhancedMenu.row + 1; redraw = 1; }
    if (keys & (0x10 | 0x20 | 1)) {
        if (gEnhancedMenu.row < 5) {
            if (gEnhancedMenu.row == 0)
                gEnhancedMenu.visible = (gEnhancedMenu.visible + ((keys & 0x20) ? 3 : 1)) & 3;
            else if (gEnhancedMenu.row == 1) gEnhancedMenu.trade ^= 1;
            else if (gEnhancedMenu.row == 2) gEnhancedMenu.tms ^= 1;
            else if (gEnhancedMenu.row == 3) gEnhancedMenu.repel ^= 1;
            else gEnhancedMenu.capture ^= 1;
            redraw = 1;
        } else if ((keys & 1) && gEnhancedMenu.row == 5) {
            gEnhancedMenu.phase = 2;
            redraw = 1;
        } else if ((keys & 1) && gEnhancedMenu.row == 6) return close_menu();
    }
    if (redraw) render();
    return 0;
}
int EnhancedMenuOpen(void *field) {
    if (gEnhancedMenu.active || ptr(field, 0x10)) return 0;
    EnhancedSettingsEnsure(field);
    gEnhancedMenu.field = field;
    gEnhancedMenu.active = 1;
    gEnhancedMenu.phase = gEnhancedMenu.row = gEnhancedMenu.error = 0;
    gEnhancedMenu.trade = gEnhancedOptions.trade_evolutions;
    gEnhancedMenu.tms = gEnhancedOptions.reusable_tms;
    gEnhancedMenu.visible = gEnhancedOptions.visible_encounters;
    gEnhancedMenu.repel = gEnhancedOptions.repel_prompt;
    gEnhancedMenu.capture = gEnhancedOptions.capture_exp;
    EnhancedNpcPause(field, gEnhancedMenu.paused_before, 1);
    FieldSystem_CreateTask(field, EnhancedMenuTask, 0);
    return 1;
}
