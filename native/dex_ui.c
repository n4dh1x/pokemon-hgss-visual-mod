#include "dex.h"
#include "events.h"
struct DexUi { u32 phase, row, action, yes; };
struct DexUi gDexUi;
_Static_assert(sizeof(struct DexUi) == 16, "Dex UI diagnostic ABI");
static const char event_name[] __attribute__((section(".event_ui")))="Choose event gifts";
static const char unavailable[] __attribute__((section(".event_ui")))="Action unavailable.";
#define EVENT_TEXT(name, value) static const char name[] __attribute__((section(".event_ui"))) = value
EVENT_TEXT(event_controls, "L/R browse  A queue  B back");
EVENT_TEXT(event_queued, "Queued at Poke Mart");
EVENT_TEXT(event_duplicate, "Already available");
static const char event_full[] __attribute__((section(".event_cold"))) = "Queue full";
static const char *const event_results[] __attribute__((section(".event_ui"))) = {
    event_queued, event_duplicate, event_full, unavailable
};
static const char *const actions[4] = {"Complete Johto Dex", "Unlock National Dex", "Complete National Dex", event_name};
void EnhancedDexUiReset(void) {
    gDexUi.phase = gDexUi.row = gDexUi.action = gDexUi.yes = 0;
}
static void text(struct Window *w, void *str, const char *s, u32 x, u32 y) {
    EnhancedDrawText(w, str, s, x, y);
}
static __attribute__((noinline)) void line(struct Window *w, void *str, const char *s, u32 y) {
    EnhancedDrawText(w, str, s, 8, y);
}
static void draw(struct Window *w, void *str) {
    struct DexUi *s = &gDexUi;
    FillWindowPixelBuffer(w, 15);
    if (s->phase == 5) {
        line(w, str, event_name, 2);
        EnhancedEventName(w, str, s->action);
        if (s->yes) line(w, str, event_results[s->yes - 1], 105);
        line(w, str, event_controls, 158);
        CopyWindowToVram(w);
        return;
    }
    line(w, str, "DEX / EVENT GIFTS", 2);
    if (!s->phase) {
        for (u32 i = 0; i < 4; ++i) text(w, str, actions[i], 16, 28 + 24 * i);
        text(w, str, "Back", 16, 124);
        text(w, str, "-", 2, 28 + 24 * s->row);
        line(w, str, "A choose   B back", 158);
    } else {
        line(w, str, actions[s->action], 28);
        if (s->phase == 1) {
            line(w, str, "Apply to game progress?", 52);
            text(w, str, s->yes ? "- Yes" : "  Yes", 16, 84);
            text(w, str, s->yes ? "  No" : "- No", 16, 108);
            line(w, str, "Native Save keeps changes", 158);
        } else if (s->phase == 2) {
            line(w, str, "Working...", 60);
        } else {
            line(w, str, s->phase == 3 ? "Done. Save game to keep." : unavailable, 60);
            line(w, str, "A or B to return", 158);
        }
    }
    CopyWindowToVram(w);
}
int EnhancedDexUi(void *field, struct Window *w, void *str, u32 keys) {
    struct DexUi *s = &gDexUi;
    if (s->phase == 5) {
        if (!(keys & 0x3F3)) return 0;
        if (keys & 2) s->phase = 0;
        else if (keys & 0x3F0) {
            u32 next = s->action + ((keys & 0x260) ? EVENT_GIFT_COUNT - 1 : 1);
            s->action = next >= EVENT_GIFT_COUNT ? next - EVENT_GIFT_COUNT : next;
            s->yes = 0;
        } else s->yes = EnhancedQueueEvent(field, s->action);
        draw(w, str);
        return 0;
    }
    if (s->phase == 2) {
        int result = EnhancedDexStep();
        if (result) { s->phase = result > 0 ? 3 : 4; draw(w, str); }
        return 0;
    }
    if (s->phase >= 3) {
        if (keys & 3) { s->phase = 0; draw(w, str); }
        return 0;
    }
    if (keys & 2) {
        if (!s->phase) return 1;
        s->phase = 0; draw(w, str); return 0;
    }
    if (!s->phase) {
        if (keys & 0x40) s->row = s->row ? s->row-1 : 4;
        if (keys & 0x80) s->row = s->row == 4 ? 0 : s->row+1;
        if (keys & 1) {
            if (s->row == 4) return 1;
            s->action = s->row == 3 ? 0 : s->row;
            s->yes = 0;
            s->phase = s->row == 3 ? 5 : 1;
        }
    } else {
        if (keys & 0xF0) s->yes ^= 1;
        if (keys & 1) {
            if (!s->yes) s->phase = 0;
            else s->phase = EnhancedDexBegin(field, s->action) ? 2 : 4;
        }
    }
    draw(w, str);
    return 0;
}
