#ifndef HGSS_ENHANCED_DEX_H
#define HGSS_ENHANCED_DEX_H
#include "ui.h"
/* Actions are immediate game progress, not staged/persistent settings. */
int EnhancedDexBegin(void *field, u32 action);
int EnhancedDexStep(void);
void EnhancedDexUiReset(void);
int EnhancedDexUi(void *field, struct Window *window, void *string, u32 keys);
#endif
