#include "settings.h"
#include "ui.h"

struct MenuState {
    void *field;
    struct Window window;
    void *string;
    u32 active, phase, row, trade, tms, visible, repel, capture, party;
    struct EnhancedExtraOptions extra;
    u32 page, error;
    u32 paused_before[2];
};
struct MenuState gEnhancedMenu;
_Static_assert(sizeof(struct MenuState) == 96, "Menu diagnostic ABI");
static void *ptr(void *p, unsigned offset) { return *(void **)((u8 *)p + offset); }
static void print(const char *text, u32 x, u32 y) {
    EnhancedDrawText(&gEnhancedMenu.window, gEnhancedMenu.string, text, x, y);
}
static void render(void) {
    static const char *odds[6] = {"1/8192", "1/4096", "1/1024", "1/256", "1/64", "Always"};
    static const char *rates[5] = {"Normal", "Off", "1/4", "1/2", "2x"};
    static const char *modes[4] = {"Off", "Few", "Some", "Many"};
    FillWindowPixelBuffer(&gEnhancedMenu.window, 15);
    print(gEnhancedMenu.page ? "ENHANCEMENTS 2/2" : "ENHANCEMENTS 1/2", 8, 2);
    if (!gEnhancedMenu.page) {
        print("Visible wilds", 16, 28);
        print(modes[gEnhancedMenu.visible], 172, 28);
        print("Trade evolution", 16, 44);
        print(gEnhancedMenu.trade ? "On" : "Off", 172, 44);
        print("Reusable TMs", 16, 60);
        print(gEnhancedMenu.tms ? "On" : "Off", 172, 60);
        print("Repel prompt", 16, 76);
        print(gEnhancedMenu.repel ? "On" : "Off", 172, 76);
        print("EXP for catching", 16, 92);
        print(gEnhancedMenu.capture ? "On" : "Off", 172, 92);
        print("Party EXP Share", 16, 108);
        print(gEnhancedMenu.party ? "On" : "Off", 172, 108);
    } else {
        print("Field HMs", 16, 28);
        print(gEnhancedMenu.extra.field_hms ? "On" : "Off", 172, 28);
        print("Grass battles", 16, 44);
        print(gEnhancedMenu.extra.roaming_only_grass ? "Roaming only" : "Normal", 144, 44);
        print("IV / EV viewer", 16, 60);
        print(gEnhancedMenu.extra.iv_ev_viewer ? "On" : "Off", 172, 60);
        print("Encounter rate", 16, 76);
        print(rates[gEnhancedMenu.extra.encounter_rate], 172, 76);
        print("Shiny odds", 16, 92);
        print(odds[gEnhancedMenu.extra.shiny_odds], 160, 92);
    }
    print("Save and close", 16, 124);
    print("Cancel", 16, 140);
    print("-", 2, 28 + 16 * gEnhancedMenu.row);
    if (gEnhancedMenu.phase == 2) print("Saving settings", 8, 158);
    else if (gEnhancedMenu.error) print("Settings storage unavailable", 8, 158);
    else if (gEnhancedMenu.page && gEnhancedMenu.row == 2)
        print("Summary: Y cycle / L/R", 8, 158);
    else print("Left/Right value  X page", 8, 158);
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
        if (EnhancedSettingsStoreAll(gEnhancedMenu.trade, gEnhancedMenu.tms, gEnhancedMenu.visible, gEnhancedMenu.repel, gEnhancedMenu.capture, gEnhancedMenu.party, &gEnhancedMenu.extra))
            return close_menu();
        gEnhancedMenu.phase = 1;
        gEnhancedMenu.error = 1;
        render();
        return 0;
    }
    u32 keys = *(volatile u32 *)0x021D1154;
    if (keys & 2) return close_menu();
    int redraw = 0;
    if (keys & 0x700) { gEnhancedMenu.page ^= 1; gEnhancedMenu.row = 0; redraw = 1; }
    u32 count = gEnhancedMenu.page ? 5 : 6;
    if (keys & 0x40) {
        gEnhancedMenu.row = gEnhancedMenu.row == 0 ? 7 :
            gEnhancedMenu.row == 6 ? count - 1 : gEnhancedMenu.row - 1;
        redraw = 1;
    }
    if (keys & 0x80) {
        gEnhancedMenu.row = gEnhancedMenu.row == 7 ? 0 :
            gEnhancedMenu.row == count - 1 ? 6 : gEnhancedMenu.row + 1;
        redraw = 1;
    }
    if (keys & (0x10 | 0x20 | 1)) {
        if (gEnhancedMenu.row < count) {
            if (gEnhancedMenu.page) {
                if (gEnhancedMenu.row == 0) gEnhancedMenu.extra.field_hms ^= 1;
                else if (gEnhancedMenu.row == 1) gEnhancedMenu.extra.roaming_only_grass ^= 1;
                else if (gEnhancedMenu.row == 2) gEnhancedMenu.extra.iv_ev_viewer ^= 1;
                else if (gEnhancedMenu.row == 3) {
                    u32 rate = gEnhancedMenu.extra.encounter_rate + ((keys & 0x20) ? 4 : 1);
                    gEnhancedMenu.extra.encounter_rate = rate >= 5 ? rate - 5 : rate;
                } else {
                    u32 odds = gEnhancedMenu.extra.shiny_odds + ((keys & 0x20) ? 5 : 1);
                    gEnhancedMenu.extra.shiny_odds = odds >= 6 ? odds - 6 : odds;
                }
            }
            else if (gEnhancedMenu.row == 0)
                gEnhancedMenu.visible = (gEnhancedMenu.visible + ((keys & 0x20) ? 3 : 1)) & 3;
            else if (gEnhancedMenu.row == 1) gEnhancedMenu.trade ^= 1;
            else if (gEnhancedMenu.row == 2) gEnhancedMenu.tms ^= 1;
            else if (gEnhancedMenu.row == 3) gEnhancedMenu.repel ^= 1;
            else if (gEnhancedMenu.row == 4) gEnhancedMenu.capture ^= 1;
            else gEnhancedMenu.party ^= 1;
            redraw = 1;
        } else if ((keys & 1) && gEnhancedMenu.row == 6) {
            gEnhancedMenu.phase = 2;
            redraw = 1;
        } else if ((keys & 1) && gEnhancedMenu.row == 7) return close_menu();
    }
    if (redraw) render();
    return 0;
}
int EnhancedMenuOpen(void *field) {
    if (gEnhancedMenu.active || ptr(field, 0x10)) return 0;
    EnhancedSettingsEnsure(field);
    gEnhancedMenu.field = field;
    gEnhancedMenu.active = 1;
    gEnhancedMenu.phase = gEnhancedMenu.row = gEnhancedMenu.page = gEnhancedMenu.error = 0;
    gEnhancedMenu.trade = gEnhancedOptions.trade_evolutions;
    gEnhancedMenu.tms = gEnhancedOptions.reusable_tms;
    gEnhancedMenu.visible = gEnhancedOptions.visible_encounters;
    gEnhancedMenu.repel = gEnhancedOptions.repel_prompt;
    gEnhancedMenu.capture = gEnhancedOptions.capture_exp;
    gEnhancedMenu.party = gEnhancedOptions.party_exp;
    gEnhancedMenu.extra.field_hms = gEnhancedExtraOptions.field_hms;
    gEnhancedMenu.extra.roaming_only_grass = gEnhancedExtraOptions.roaming_only_grass;
    gEnhancedMenu.extra.iv_ev_viewer = gEnhancedExtraOptions.iv_ev_viewer;
    gEnhancedMenu.extra.encounter_rate = gEnhancedExtraOptions.encounter_rate;
    gEnhancedMenu.extra.shiny_odds = gEnhancedExtraOptions.shiny_odds;
    EnhancedNpcPause(field, gEnhancedMenu.paused_before, 1);
    FieldSystem_CreateTask(field, EnhancedMenuTask, 0);
    return 1;
}
