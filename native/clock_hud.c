#include "clock.h"
#include "ui.h"
extern void *String_New(u32 length, int heap);
extern void String_Delete(void *string);
extern void AddWindowParameterized(void *bg, struct Window *window, u8 layer,
    u8 x, u8 y, u8 width, u8 height, u8 palette, u16 base_tile);
extern void RemoveWindow(struct Window *window);
extern void NativeHudClear(struct Window *window);
extern int FieldMovementAllowed(void *field);
extern u32 NativeNormalMenuInhibitFlags(void *field);
extern void NativeClockAssert(void);
extern void *NativeClockTaskNew(void *field, int (*callback)(void *), void *environment);

struct ClockHudState {
    void *field;
    struct Window window;
    void *string;
    u32 active, opens, closes, draws, seconds, rate;
};
struct ClockHudState gClockHudState;
_Static_assert(sizeof(struct ClockHudState) == 48, "Clock HUD diagnostic ABI");
static void *ptr(void *p, unsigned n) { return *(void **)((u8 *)p + n); }

void EnhancedClockHudClose(void) {
    if (!gClockHudState.active) return;
    NativeHudClear(&gClockHudState.window);
    RemoveWindow(&gClockHudState.window);
    String_Delete(gClockHudState.string);
    gClockHudState.string = gClockHudState.field = 0;
    gClockHudState.active = 0;
    ++gClockHudState.closes;
}
static int available(void *field) {
    if (gEnhancedExtraOptions.clock_hud != 1 || !ptr(field, 4) ||
        !ptr(field, 8) || !ptr(field, 0x3C) || !ptr(field, 0x44) || ptr(field, 0x10) ||
        !FieldMovementAllowed(field) || (NativeNormalMenuInhibitFlags(field) & 4)) return 0;
    void *banner = ptr(ptr(field, 4), 8);
    /* The area-name animation scrolls the whole shared BG3. Wait for it. */
    return !banner || !*(u32 *)banner;
}
void EnhancedClockHudBefore(void *field) {
    if (gClockHudState.active && (gClockHudState.field != field ||
        gClockHudState.window.bg != ptr(field, 8) || !available(field)))
        EnhancedClockHudClose();
}
void EnhancedClockHudForget(void *manager) {
    if (gClockHudState.active && ptr(gClockHudState.field, 0x3C) == manager)
        EnhancedClockHudClose();
}
/* Preserve the original constructor's assertion, arguments, field assignment
 * and return value. Release our window before any native task can open UI or
 * unload graphics; nested tasks already run with the HUD unavailable. */
void *EnhancedClockCreateTask(void *field, int (*callback)(void *), void *environment) {
    if (ptr(field, 0x10)) NativeClockAssert();
    if (gClockHudState.active && gClockHudState.field == field) EnhancedClockHudClose();
    void *task = NativeClockTaskNew(field, callback, environment);
    *(void **)((u8 *)field + 0x10) = task;
    return task;
}
void EnhancedClockHudShow(void *field) {
    if (!available(field)) {
        if (gClockHudState.active && gClockHudState.field == field) EnhancedClockHudClose();
        return;
    }
    if (gClockHudState.active && gClockHudState.field != field) EnhancedClockHudClose();
    u32 seconds = EnhancedClockSeconds();
    u32 choice = gEnhancedExtraOptions.clock_speed;
    if (choice >= 6) choice = 0;
    if (gClockHudState.active && gClockHudState.seconds == seconds && gClockHudState.rate == choice) return;
    if (!gClockHudState.active) {
        void *string = String_New(64, 4);
        if (!string) return;
        gClockHudState.field = field;
        gClockHudState.string = string;
        /* Main BG3: area-name window and icon tiles end below 0x360;
         * normal message/menu tiles end below it, frame tiles start 0x3D9. */
        AddWindowParameterized(ptr(field, 8), &gClockHudState.window, 3, 18, 21, 12, 2, 13, 0x360);
        gClockHudState.active = 1;
        ++gClockHudState.opens;
    }
    char text[16];
    static const char *rates[6] = {"1x", "6x", "12x", "24x", "60x", "120x"};
    gClockHudState.seconds = EnhancedClockText(text);
    gClockHudState.rate = choice;
    text[8] = ' ';
    const char *rate = rates[choice];
    unsigned n = 9;
    while (*rate) text[n++] = *rate++;
    text[n] = 0;
    FillWindowPixelBuffer(&gClockHudState.window, 15);
    EnhancedDrawText(&gClockHudState.window, gClockHudState.string, text, 0, 0);
    CopyWindowToVram(&gClockHudState.window);
    ++gClockHudState.draws;
}
