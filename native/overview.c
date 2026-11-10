#include "settings.h"
#include "ui.h"

extern void *Save_PlayerData_GetProfile(void *save);
extern void *SaveArray_Party_Get(void *save);
extern int Party_GetCount(void *party);
extern void *Party_GetMonByIndex(void *party, int slot);
extern u32 GetMonData(void *mon, int attribute, void *destination);
extern u32 NativeBadgeCount(void *profile);
extern void CopyU16ArrayToString(void *string, const u16 *characters);
extern u8 AddTextPrinterParameterizedWithColor(struct Window *, int, void *, u32, u32, u32, u32, void *);

#define LABEL(name, value) static const char name[] __attribute__((section(".overview_ui"))) = value
LABEL(title, "SAVE OVERVIEW");
LABEL(badges, "Badges");
LABEL(back, "B back / Save in field menu");

static void print_native(struct Window *window, void *string, u32 x, u32 y) {
    AddTextPrinterParameterizedWithColor(window, 0, string, x, y, 0xFF, 0x01020F, 0);
}

static void print_number(struct Window *window, void *string, u32 number, u32 y) {
    char buffer[4];
    u32 length = 0;
    if (number >= 100) buffer[length++] = '0' + number / 100;
    if (number >= 10) buffer[length++] = '0' + number / 10 % 10;
    buffer[length++] = '0' + number % 10;
    buffer[length] = 0;
    EnhancedDrawText(window, string, buffer, 184, y);
}

void EnhancedOverview(struct Window *window, void *string) {
    void *save = EnhancedSettingsSaveData();
    if (!save) return;
    void *profile = Save_PlayerData_GetProfile(save);
    FillWindowPixelBuffer(window, 15);
    EnhancedDrawText(window, string, title, 8, 2);
    CopyU16ArrayToString(string, profile);
    print_native(window, string, 16, 24);
    EnhancedDrawText(window, string, badges, 128, 24);
    print_number(window, string, NativeBadgeCount(profile), 24);
    void *party = SaveArray_Party_Get(save);
    int count = Party_GetCount(party);
    for (int slot = 0; slot < count && slot < 6; ++slot) {
        void *mon = Party_GetMonByIndex(party, slot);
        u32 y = 48 + slot * 16;
        GetMonData(mon, 119, string);
        print_native(window, string, 16, y);
        print_number(window, string, GetMonData(mon, 161, 0), y);
    }
    EnhancedDrawText(window, string, back, 8, 158);
    CopyWindowToVram(window);
}
