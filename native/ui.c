#include "ui.h"
extern void *String_New(u32 maxsize, int heap);
extern void String_Delete(void *string);
extern void CopyU16ArrayToString(void *string, const u16 *text);
extern void AddWindowParameterized(void *bg, struct Window *window, u8 layer,
    u8 x, u8 y, u8 width, u8 height, u8 palette, u16 base_tile);
extern void RemoveWindow(struct Window *window);
extern void LoadUserFrameGfx1(void *bg, int layer, u16 base_tile, u8 palette, u8 frame, int heap);
extern void DrawFrameAndWindow1(struct Window *window, int deferred, u16 base_tile, u8 palette);
extern void ClearFrameAndWindow1(struct Window *window, int deferred);
extern u8 AddTextPrinterParameterizedWithColor(struct Window *window, int font,
    void *string, u32 x, u32 y, u32 speed, u32 color, void *callback);
extern void FieldDrawMapName_Reset(void *info);

static void *ptr(void *p, unsigned offset) { return *(void **)((u8 *)p + offset); }
static u32 word(void *p, unsigned offset) { return *(u32 *)((u8 *)p + offset); }
static u16 character(char c) {
    if (c >= 'A' && c <= 'Z') return 299 + c - 'A';
    if (c >= 'a' && c <= 'z') return 325 + c - 'a';
    if (c >= '0' && c <= '9') return 289 + c - '0';
    if (c == '?') return 428;
    if (c == '.') return 430;
    if (c == '/') return 433;
    if (c == ':') return 452;
    if (c == '-') return 446;
    return 478;
}
void EnhancedCopyText(void *string, const char *text) {
    u16 encoded[64];
    unsigned n = 0;
    while (*text && n < 63) encoded[n++] = character(*text++);
    encoded[n] = 0xFFFF;
    CopyU16ArrayToString(string, encoded);
}
void EnhancedDrawText(struct Window *window, void *string, const char *text, u32 x, u32 y) {
    EnhancedCopyText(string, text);
    AddTextPrinterParameterizedWithColor(window, 0, string, x, y, 0xFF, 0x01020F, 0);
}
void *EnhancedWindowOpen(void *field, struct Window *window, u8 y, u8 height) {
    FieldDrawMapName_Reset(ptr(ptr(field, 4), 8));
    void *bg = ptr(field, 8);
    AddWindowParameterized(bg, window, 3, 2, y, 28, height, 13, 1);
    LoadUserFrameGfx1(bg, 3, 0x3D9, 11, 0, 4);
    DrawFrameAndWindow1(window, 1, 0x3D9, 11);
    return String_New(64, 4);
}
void EnhancedWindowClose(struct Window *window, void *string) {
    ClearFrameAndWindow1(window, 0);
    RemoveWindow(window);
    String_Delete(string);
}
void EnhancedNpcPause(void *field, u32 previous[2], int pause) {
    void *manager = ptr(field, 0x3C);
    u8 *objects = ptr(manager, 0x124);
    u32 count = word(manager, 4);
    if (count > 64) count = 64;
    if (pause) previous[0] = previous[1] = 0;
    for (u32 i = 0; i < count; ++i) {
        u32 *flags = (u32 *)(objects + 0x12C * i);
        if (pause) {
            if (*flags & (1u << 6)) previous[i >> 5] |= 1u << (i & 31);
            *flags |= 1u << 6;
        } else if (!(previous[i >> 5] & (1u << (i & 31))))
            *flags &= ~(1u << 6);
    }
}
