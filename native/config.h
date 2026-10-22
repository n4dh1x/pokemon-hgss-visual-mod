#ifndef HGSS_ENHANCED_CONFIG_H
#define HGSS_ENHANCED_CONFIG_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed short s16;
typedef signed int s32;

struct EnhancedOptions {
    u32 magic;
    u32 version;
    u32 trade_evolutions;
    u32 reusable_tms;
    u32 visible_encounters; /* 0 Off, 1 Few, 2 Some, 3 Many */
    u32 repel_prompt;
    u32 capture_exp;
    u32 reserved[1];
};

extern volatile struct EnhancedOptions gEnhancedOptions;

#endif
