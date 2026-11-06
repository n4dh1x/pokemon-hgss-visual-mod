#ifndef HGSS_ENHANCED_QUICK_BALL_H
#define HGSS_ENHANCED_QUICK_BALL_H
#include "settings.h"
void EnhancedQuickRestore(const struct EnhancedJournal *record, u32 owner);
void EnhancedQuickSnapshot(struct EnhancedJournal *record);
void EnhancedQuickBegin(void *battle, void *ctx);
int EnhancedQuickNeedsSave(void *save);
void EnhancedQuickSaving(void *save);
void EnhancedQuickSaved(int success);
#endif
