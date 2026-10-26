#ifndef HGSS_ENHANCED_CLOCK_H
#define HGSS_ENHANCED_CLOCK_H
#include "settings.h"
void EnhancedClockRestore(const struct EnhancedJournal *record, u32 owner);
void EnhancedClockSnapshot(struct EnhancedJournal *record);
u32 EnhancedClockSeconds(void);
u32 EnhancedClockRate(void);
u32 EnhancedClockText(char *text);
#endif
