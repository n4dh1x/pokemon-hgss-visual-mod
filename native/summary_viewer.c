#include "ui.h"

extern int NativeSummaryInput(void *summary);
extern void NativeSummaryDrawStats(void *summary);
extern void *NativeSummaryMon(void *summary);
extern void NativeSummaryNumber(void *, u32 message, u32 number, u8 digits, u8 pad);
extern void NativeSummaryPrint(void *, struct Window *, u32 color, u32 justify);
extern u32 GetMonData(void *, int, void *);
extern u32 GetBoxMonData(void *, int, void *);
extern void PlaySE(u32);

struct SummaryViewState {
    void *summary, *pokemon;
    u32 mode, draws, switches, data_type, reads, values[6];
};
struct SummaryViewState gSummaryViewState;
_Static_assert(sizeof(struct SummaryViewState) == 52, "Summary diagnostic ABI");
static void *ptr(void *p, u32 offset) { return *(void **)((u8 *)p + offset); }
static u32 word(void *p, u32 offset) { return *(u32 *)((u8 *)p + offset); }
static struct Window *label(void *summary) { return (struct Window *)((u8 *)summary + 4 + 15 * 16); }
static void text(void *summary, struct Window *window, const char *value, u32 color, u32 justify) {
    FillWindowPixelBuffer(window, 0);
    EnhancedCopyText(ptr(summary, 0x7AC), value);
    NativeSummaryPrint(summary, window, color, justify);
    CopyWindowToVram(window);
}
static void identity(void *summary) {
    gSummaryViewState.summary = summary;
    gSummaryViewState.pokemon = NativeSummaryMon(summary);
    gSummaryViewState.data_type = *((u8 *)ptr(summary, 0x22C) + 0x11);
}
void EnhancedSummaryDraw(void *summary) {
    NativeSummaryDrawStats(summary);
    identity(summary);
    gSummaryViewState.mode = 0;
    ++gSummaryViewState.draws;
    /* The native page refresh does not redraw its fixed HP-label window. */
    text(summary, label(summary), "HP", 0x0E0F00, 0);
}
int EnhancedSummaryReadValues(void *summary, u32 mode, u32 *values) {
    u8 type = *((u8 *)ptr(summary, 0x22C) + 0x11);
    if (mode < 1 || mode > 2 || type > 2) return 0;
    void *mon = NativeSummaryMon(summary);
    if (!mon) return 0;
    /* Display order is HP/Attack/Defense/Sp.Atk/Sp.Def/Speed. Native saved
     * parameter order puts Speed before the special stats. Never edit cached
     * battle stats, Pokemon data, moves, HP or the encryption state ourselves. */
    static const u8 order[6] = {0, 1, 2, 4, 5, 3};
    int first = mode == 1 ? 13 : 70;
    for (int i = 0; i < 6; ++i)
        values[i] = type == 2 ? GetBoxMonData(mon, first + order[i], 0) :
                               GetMonData(mon, first + order[i], 0);
    return 1;
}
static void render(void *summary, u32 mode) {
    if (!mode) {
        EnhancedSummaryDraw(summary);
        return;
    }
    if (!EnhancedSummaryReadValues(summary, mode, gSummaryViewState.values)) return;
    identity(summary);
    gSummaryViewState.mode = mode;
    ++gSummaryViewState.reads;
    struct Window *windows = ptr(summary, 0x224);
    for (int i = 0; i < 6; ++i) {
        FillWindowPixelBuffer(windows + i, 0);
        NativeSummaryNumber(summary, 119, gSummaryViewState.values[i], 3, 1);
        NativeSummaryPrint(summary, windows + i, 0x010200, i ? 1 : 2);
        CopyWindowToVram(windows + i);
    }
    /* The fixed HP-label window is only two tiles wide; two letters fit. */
    text(summary, label(summary), mode == 1 ? "EV" : "IV", 0x0E0F00, 0);
    text(summary, windows + 7, mode == 1 ?
        "EVs: 0-255. Y cycle\nL EVs  R IVs  Select stats" :
        "IVs: 0-31. Y cycle\nL EVs  R IVs  Select stats", 0x010200, 0);
}
int EnhancedSummaryInput(void *summary) {
    u32 keys = *(volatile u32 *)0x021D1154;
    u32 repeat = *(volatile u32 *)0x021D1158;
    int page = *(signed char *)((u8 *)summary + 0x7BC);
    int closing = *((u8 *)summary + 0x7BF) >> 4;
    if (!gEnhancedExtraOptions.iv_ev_viewer || page != 1 || closing == 1 ||
        word(summary, 0x228) < 8 || word(summary, 0x228) > 32) {
        if (page == 1 && gSummaryViewState.summary == summary && gSummaryViewState.mode &&
            word(summary, 0x228) >= 8 && word(summary, 0x228) <= 32)
            EnhancedSummaryDraw(summary);
        gSummaryViewState.mode = 0;
        return NativeSummaryInput(summary);
    }
    if (gSummaryViewState.summary != summary ||
        gSummaryViewState.pokemon != NativeSummaryMon(summary)) {
        identity(summary);
        gSummaryViewState.mode = 0;
    }
    /* Preserve native page/party navigation and modal controls first. Only
     * previously unused Y/L/R/SELECT on the settled skills page select a view. */
    if ((repeat & 0xF0) || (keys & 3) || *(volatile u16 *)0x021D1170) {
        if (gSummaryViewState.mode) EnhancedSummaryDraw(summary);
        return NativeSummaryInput(summary);
    }
    if (keys & (0x800 | 0x200 | 0x100 | 4)) {
        u32 mode = (keys & 4) ? 0 : (keys & 0x800) ?
            (gSummaryViewState.mode == 0 ? 2 : gSummaryViewState.mode == 2 ? 1 : 0) :
            (keys & 0x200) ? 1 : 2;
        render(summary, mode);
        ++gSummaryViewState.switches;
        PlaySE(0x5E1);
        return 2; /* Native summary input state. */
    }
    int next = NativeSummaryInput(summary);
    if (next != 2) gSummaryViewState.mode = 0;
    return next;
}
