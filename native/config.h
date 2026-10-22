#ifndef HGSS_ENHANCED_CONFIG_H
#define HGSS_ENHANCED_CONFIG_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

struct EnhancedOptions {
    u32 magic;
    u32 version;
    u32 trade_evolutions;
    u32 reusable_tms;
    u32 reserved[4];
};

extern volatile struct EnhancedOptions gEnhancedOptions;

#endif
