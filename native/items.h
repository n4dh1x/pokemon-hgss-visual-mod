#ifndef HGSS_ENHANCED_ITEMS_H
#define HGSS_ENHANCED_ITEMS_H
#include "ui.h"
int EnhancedItemValid(u32 item, u32 pocket, void *string);
void EnhancedItemStep(struct EnhancedExtraOptions *extra, int direction, void *string);
int EnhancedGiveItem(void *field, const struct EnhancedExtraOptions *extra, void *string);
void EnhancedItemUiReset(void);
int EnhancedItemUi(void *field, struct Window *window, void *string,
    struct EnhancedExtraOptions *extra, u32 keys);
#endif
