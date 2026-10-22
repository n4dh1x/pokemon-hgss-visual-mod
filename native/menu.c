#include "settings.h"

struct Window {
    void *bg;
    u8 layer, x, y, width, height, palette;
    u16 base_tile;
    void *pixels;
};
_Static_assert(sizeof(struct Window) == 16, "Window ABI");
extern void *FieldSystem_CreateTask(void *field, int (*callback)(void *), void *environment);
extern void *String_New(u32 maxsize, int heap);
extern void String_Delete(void *string);
extern void CopyU16ArrayToString(void *string, const u16 *text);
extern void AddWindowParameterized(void *bg, struct Window *window, u8 layer,
    u8 x, u8 y, u8 width, u8 height, u8 palette, u16 base_tile);
extern void FillWindowPixelBuffer(struct Window *window, u8 color);
extern void CopyWindowToVram(struct Window *window);
extern void RemoveWindow(struct Window *window);
extern void LoadUserFrameGfx1(void *bg, int layer, u16 base_tile, u8 palette, u8 frame, int heap);
extern void DrawFrameAndWindow1(struct Window *window, int deferred, u16 base_tile, u8 palette);
extern void ClearFrameAndWindow1(struct Window *window, int deferred);
extern u8 AddTextPrinterParameterizedWithColor(struct Window *window, int font,
    void *string, u32 x, u32 y, u32 speed, u32 color, void *callback);
extern void FieldDrawMapName_Reset(void *info);

struct MenuState {
    void *field;
    struct Window window;
    void *string;
    u32 active, phase, row, trade, tms, visible, error;
    u32 paused_before[2];
};
struct MenuState gEnhancedMenu;
_Static_assert(sizeof(struct MenuState) == 60, "Menu diagnostic ABI");

static u32 word(void *p, unsigned offset) { return *(u32 *)((u8 *)p + offset); }
static void *ptr(void *p, unsigned offset) { return *(void **)((u8 *)p + offset); }

static u16 character(char c) {
    if (c >= 'A' && c <= 'Z') return 299 + c - 'A';
    if (c >= 'a' && c <= 'z') return 325 + c - 'a';
    if (c >= '0' && c <= '9') return 289 + c - '0';
    if (c == '/') return 433;
    if (c == ':') return 452;
    if (c == '-') return 446;
    return 478;
}
static void print(const char *text, u32 x, u32 y) {
    u16 encoded[64];
    unsigned n = 0;
    while (*text && n < 63)
        encoded[n++] = character(*text++);
    encoded[n] = 0xFFFF;
    CopyU16ArrayToString(gEnhancedMenu.string, encoded);
    AddTextPrinterParameterizedWithColor(&gEnhancedMenu.window, 0, gEnhancedMenu.string,
        x, y, 0xFF, 0x01020F, 0);
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
    print("Save and close", 16, 82);
    print("Cancel", 16, 100);
    print("-", 2, 28 + 18 * gEnhancedMenu.row);
    if (gEnhancedMenu.phase == 2)
        print("Saving settings", 8, 120);
    else if (gEnhancedMenu.error)
        print("Settings storage unavailable", 8, 120);
    else
        print("Left/Right change  A choose", 8, 120);
    CopyWindowToVram(&gEnhancedMenu.window);
}

static void set_npc_pause(int pause) {
    void *manager = ptr(gEnhancedMenu.field, 0x3C);
    u8 *objects = ptr(manager, 0x124);
    u32 count = word(manager, 4);
    if (count > 64) count = 64;
    if (pause) gEnhancedMenu.paused_before[0] = gEnhancedMenu.paused_before[1] = 0;
    for (u32 i = 0; i < count; ++i) {
        u32 *flags = (u32 *)(objects + 0x12C * i);
        if (pause) {
            if (*flags & (1u << 6))
                gEnhancedMenu.paused_before[i >> 5] |= 1u << (i & 31);
            *flags |= 1u << 6;
        } else if (!(gEnhancedMenu.paused_before[i >> 5] & (1u << (i & 31))))
            *flags &= ~(1u << 6);
    }
}
static int close_menu(void) {
    ClearFrameAndWindow1(&gEnhancedMenu.window, 0);
    RemoveWindow(&gEnhancedMenu.window);
    String_Delete(gEnhancedMenu.string);
    set_npc_pause(0);
    gEnhancedMenu.active = 0;
    return 1;
}

int EnhancedMenuTask(void *task) {
    (void)task;
    if (gEnhancedMenu.phase == 0) {
        void *field = gEnhancedMenu.field;
        FieldDrawMapName_Reset(ptr(ptr(field, 4), 8));
        void *bg = ptr(field, 8);
        AddWindowParameterized(bg, &gEnhancedMenu.window, 3, 2, 2, 28, 17, 13, 1);
        LoadUserFrameGfx1(bg, 3, 0x3D9, 11, 0, 4);
        DrawFrameAndWindow1(&gEnhancedMenu.window, 1, 0x3D9, 11);
        gEnhancedMenu.string = String_New(64, 4);
        gEnhancedMenu.phase = 1;
        render();
        return 0;
    }
    if (gEnhancedMenu.phase == 2) {
        if (EnhancedSettingsStore(gEnhancedMenu.trade, gEnhancedMenu.tms, gEnhancedMenu.visible))
            return close_menu();
        gEnhancedMenu.phase = 1;
        gEnhancedMenu.error = 1;
        render();
        return 0;
    }
    u32 keys = *(volatile u32 *)0x021D1154; /* gSystem.newKeys, +0x48 */
    if (keys & 2) return close_menu();
    int redraw = 0;
    if (keys & 0x40) { gEnhancedMenu.row = gEnhancedMenu.row ? gEnhancedMenu.row - 1 : 4; redraw = 1; }
    if (keys & 0x80) { gEnhancedMenu.row = gEnhancedMenu.row == 4 ? 0 : gEnhancedMenu.row + 1; redraw = 1; }
    if (keys & (0x10 | 0x20 | 1)) {
        if (gEnhancedMenu.row < 3) {
            if (gEnhancedMenu.row == 0)
                gEnhancedMenu.visible = (gEnhancedMenu.visible + ((keys & 0x20) ? 3 : 1)) & 3;
            else if (gEnhancedMenu.row == 1)
                gEnhancedMenu.trade ^= 1;
            else
                gEnhancedMenu.tms ^= 1;
            redraw = 1;
        } else if ((keys & 1) && gEnhancedMenu.row == 3) {
            gEnhancedMenu.phase = 2;
            redraw = 1;
        } else if ((keys & 1) && gEnhancedMenu.row == 4)
            return close_menu();
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
    set_npc_pause(1);
    FieldSystem_CreateTask(field, EnhancedMenuTask, 0);
    return 1;
}
