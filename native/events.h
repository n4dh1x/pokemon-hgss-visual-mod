#ifndef HGSS_ENHANCED_EVENTS_H
#define HGSS_ENHANCED_EVENTS_H
#include "ui.h"
#define EVENT_GIFT_COUNT 32
int EnhancedQueueEvent(void *field, u32 index);
void EnhancedEventName(struct Window *window, void *string, u32 index);
#endif
