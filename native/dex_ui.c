#include "dex.h"
struct DexUi { u32 phase, row, action, yes; };
struct DexUi gDexUi;
_Static_assert(sizeof(struct DexUi) == 16, "Dex UI diagnostic ABI");
static const char *const actions[3] = {"Complete Johto Dex", "Unlock National Dex", "Complete National Dex"};
void EnhancedDexUiReset(void) {
    gDexUi.phase = gDexUi.row = gDexUi.action = gDexUi.yes = 0;
}
static void text(struct Window *w, void *str, const char *s, u32 x, u32 y) {
    EnhancedDrawText(w, str, s, x, y);
}
static void draw(struct Window *w, void *str) {
    struct DexUi *s = &gDexUi;
    FillWindowPixelBuffer(w, 15);
    text(w, str, "POKEDEX ACTIONS", 8, 2);
    if (!s->phase) {
        for (u32 i = 0; i < 3; ++i) text(w, str, actions[i], 16, 28 + 24 * i);
        text(w, str, "Back", 16, 100);
        text(w, str, "-", 2, 28 + 24 * s->row);
        text(w, str, "A choose   B back", 8, 158);
    } else {
        text(w, str, actions[s->action], 8, 28);
        if (s->phase == 1) {
            text(w, str, "Apply to game progress?", 8, 52);
            text(w, str, s->yes ? "- Yes" : "  Yes", 16, 84);
            text(w, str, s->yes ? "  No" : "- No", 16, 108);
            text(w, str, "Native Save keeps changes", 8, 158);
        } else if (s->phase == 2) {
            text(w, str, "Working...", 8, 60);
        } else {
            text(w, str, s->phase == 3 ? "Done. Save game to keep." : "Action unavailable.", 8, 60);
            text(w, str, "A or B to return", 8, 158);
        }
    }
    CopyWindowToVram(w);
}
int EnhancedDexUi(void *field, struct Window *w, void *str, u32 keys) {
    struct DexUi *s = &gDexUi;
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
        if (keys & 0x40) s->row = (s->row + 3) & 3;
        if (keys & 0x80) s->row = (s->row + 1) & 3;
        if (keys & 1) {
            if (s->row == 3) return 1;
            s->action = s->row; s->yes = 0; s->phase = 1;
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
