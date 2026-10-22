#ifndef HGSS_ENHANCED_SETTINGS_H
#define HGSS_ENHANCED_SETTINGS_H
#include "config.h"

#define ENHANCED_SETTINGS_COUNT 48
#define ENHANCED_JOURNAL_MAGIC 0x53454748u
#define ENHANCED_JOURNAL_VERSION 1

struct EnhancedJournal {
    u32 magic, version, sequence, owner, count;
    u32 values[ENHANCED_SETTINGS_COUNT];
    u32 reserved[10];
    u32 checksum;
};
_Static_assert(sizeof(struct EnhancedJournal) == 256, "Settings flash page ABI");

void EnhancedSettingsEnsure(void *field);
int EnhancedSettingsStore(u32 trade, u32 tms, u32 visible, u32 repel, u32 capture);
void *EnhancedSettingsSaveData(void);
int EnhancedMenuOpen(void *field);
u32 EnhancedSettingsCRC(const void *data, u32 size);
int EnhancedSettingsValid(const struct EnhancedJournal *record, u32 owner);
#endif
