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
    u32 encounter_rate; /* Normal, Off, quarter, half, double. */
    u32 shiny_odds; /* Native, 2/8/32/128 rolls, always. */
    u32 hide_follower; /* Default zero preserves the native party follower. */
    u32 clock_speed; /* 1x, 6x, 12x, 24x, 60x, 120x; calendar stays native. */
    u32 clock_hud; /* Optional field clock, default Off. */
    u32 camera_pitch; /* Visual+ default, then 34/37/40/43/46 degrees. */
    u32 camera_zoom; /* 90/100/110/120 percent; default index 1. */
    u32 always_catch; /* Optional native wild-catch guarantee, default Off. */
    u32 instant_victory; /* Optional native opponent fainting, default Off. */
    u32 fast_eggs; /* One valid egg every five actual steps; default Off. */
    u32 infinite_money; /* Refill owned wallet reads, default Off. */
};
extern volatile struct EnhancedExtraOptions gEnhancedExtraOptions;

#endif
