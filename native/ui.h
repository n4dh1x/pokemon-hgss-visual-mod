#ifndef HGSS_ENHANCED_UI_H
#define HGSS_ENHANCED_UI_H
#include "config.h"

struct Window {
    void *bg;
    u8 layer, x, y, width, height, palette;
    u16 base_tile;
    void *pixels;
};
_Static_assert(sizeof(struct Window) == 16, "Window ABI");
extern void *FieldSystem_CreateTask(void *field, int (*callback)(void *), void *environment);
extern void FillWindowPixelBuffer(struct Window *window, u8 color);
extern void CopyWindowToVram(struct Window *window);
void *EnhancedWindowOpen(void *field, struct Window *window, u8 y, u8 height);
void EnhancedWindowClose(struct Window *window, void *string);
void EnhancedDrawText(struct Window *window, void *string, const char *text, u32 x, u32 y);
void EnhancedNpcPause(void *field, u32 previous[2], int pause);
#endif
