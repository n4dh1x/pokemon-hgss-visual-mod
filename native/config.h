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
    u32 party_exp;
};

extern volatile struct EnhancedOptions gEnhancedOptions;

/* Keep the fixed loader header/trampoline ABI while extending runtime options. */
struct EnhancedExtraOptions {
    u32 field_hms;
    u32 roaming_only_grass; /* Optional sprite-contact-only grass; default Off. */
    u32 iv_ev_viewer;
};
extern volatile struct EnhancedExtraOptions gEnhancedExtraOptions;

#endif
