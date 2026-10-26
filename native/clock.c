#include "clock.h"

typedef unsigned long long u64;
extern u64 NativeRtcWall(void);
extern u32 NativeRtcSeconds(void);
extern u32 NativeRtcDayByHour(u32 hour);
extern u32 NativeRtcWildByHour(u32 hour);
extern void NativeRtcCopyTime(u32 *time);
extern u32 EnhancedUnsignedDivide(u32 numerator, u32 denominator);
extern void *NativeSysRtc(void *save);
extern int NativeSaveGame(void *save);
extern void NativeBerryUpdate(void *data, int redraw);
extern void NativeBerryAdvance(void *pots, void *properties, u32 minutes);
extern void NativeBerryPlant(void *pots, u32 index, void *properties, u32 berry);
extern void NativeBerryStatus(void *data);
extern void NativeBerryRedraw(void *data);

struct ClockState {
    u32 owner, ready, restored, shifted, seconds, wall, bonus_minutes, bonus_seconds;
    u32 updates, backwards, saves, save_failures, berry_minutes, light_reads, encounter_reads;
};
struct ClockState gClockState;
_Static_assert(sizeof(struct ClockState) == 60, "World clock diagnostic ABI");
static u32 mod(u32 n, u32 d) { return n - EnhancedUnsignedDivide(n, d) * d; }
static int photo(void) { return *(volatile u32 *)0x021D1090 == 3; }
u32 EnhancedClockRate(void) {
    static const u32 rates[6] = {1, 6, 12, 24, 60, 120};
    u32 setting = gEnhancedExtraOptions.clock_speed;
    return setting < 6 ? rates[setting] : 1;
}
void EnhancedClockRestore(const struct EnhancedJournal *record, u32 owner) {
    u32 *words = (u32 *)&gClockState;
    for (int i = 0; i < 15; ++i) words[i] = 0;
    gClockState.owner = owner;
    if (record && (record->reserved[0] & 1024)) {
        gClockState.restored = 1;
        gClockState.seconds = record->values[13];
        gClockState.wall = record->values[14];
        gClockState.shifted = record->values[15];
        gClockState.bonus_minutes = record->values[16];
        gClockState.bonus_seconds = record->values[17];
    }
}
static void bonus(u32 elapsed, u32 extra) {
    if (!extra) return;
    u32 minutes = EnhancedUnsignedDivide(elapsed, 60);
    u32 seconds = mod(elapsed, 60) * extra + gClockState.bonus_seconds;
    u32 carry = EnhancedUnsignedDivide(seconds, 60);
    gClockState.bonus_seconds = mod(seconds, 60);
    u32 room = 2147483647u - gClockState.bonus_minutes;
    if (minutes > EnhancedUnsignedDivide(room, extra) || carry > room - minutes * extra) {
        gClockState.bonus_minutes = 2147483647u;
        gClockState.bonus_seconds = 0;
    } else gClockState.bonus_minutes += minutes * extra + carry;
}
static int advance(int force) {
    u32 owner;
    if ((!force && !gEnhancedExtraOptions.clock_speed && !gClockState.shifted) ||
        !EnhancedSettingsOwner(&owner) || owner != gClockState.owner || photo()) return 0;
    u64 native_wall = NativeRtcWall();
    if (native_wall > 3155759999ULL) return 0;
    u32 now = (u32)native_wall;
    u32 rate = EnhancedClockRate();
    if (!gClockState.ready) {
        if (gClockState.restored && gClockState.shifted) {
            /* Off-session time resumes at 1x; no accelerated Berry debt. */
            if (now >= gClockState.wall)
                gClockState.seconds = mod(gClockState.seconds + mod(now - gClockState.wall, 86400), 86400);
        } else gClockState.seconds = NativeRtcSeconds();
        gClockState.ready = 1;
    } else if (now >= gClockState.wall) {
        u32 elapsed = now - gClockState.wall;
        if (rate == 1 && !gClockState.shifted) gClockState.seconds = NativeRtcSeconds();
        else gClockState.seconds = mod(gClockState.seconds + mod(elapsed, 86400) * rate, 86400);
        bonus(elapsed, rate - 1);
    } else ++gClockState.backwards; /* Rebase after a native RTC rollback. */
    gClockState.wall = now;
    if (rate > 1) gClockState.shifted = 1;
    ++gClockState.updates;
    return 1;
}
u32 EnhancedClockSeconds(void) {
    ++gClockState.light_reads;
    return advance(0) ? gClockState.seconds : NativeRtcSeconds();
}
u32 EnhancedClockDayByHour(u32 hour) {
    if (advance(0)) hour = EnhancedUnsignedDivide(gClockState.seconds, 3600);
    return NativeRtcDayByHour(hour);
}
u32 EnhancedClockWildByHour(u32 hour) {
    if (advance(0)) hour = EnhancedUnsignedDivide(gClockState.seconds, 3600);
    return NativeRtcWildByHour(hour);
}
u32 EnhancedClockDay(void) {
    ++gClockState.encounter_reads;
    u32 time[3]; NativeRtcCopyTime(time);
    return EnhancedClockDayByHour(time[0]);
}
u32 EnhancedClockNight(void) {
    u32 day = EnhancedClockDay();
    return day == 3 || day == 4;
}
u32 EnhancedClockWild(void) {
    ++gClockState.encounter_reads;
    u32 time[3]; NativeRtcCopyTime(time);
    return EnhancedClockWildByHour(time[0]);
}
void EnhancedClockCopyTime(u32 *time) {
    NativeRtcCopyTime(time);
    if (advance(0)) {
        u32 seconds = gClockState.seconds;
        time[0] = EnhancedUnsignedDivide(seconds, 3600);
        time[1] = EnhancedUnsignedDivide(mod(seconds, 3600), 60);
        time[2] = mod(seconds, 60);
    }
}
u32 EnhancedClockFieldHour(void *field) {
    if (advance(0)) return EnhancedUnsignedDivide(gClockState.seconds, 3600);
    return *(u32 *)((u8 *)NativeSysRtc(*(void **)((u8 *)field + 12)) + 0x14);
}
void EnhancedClockSnapshot(struct EnhancedJournal *record) {
    u32 requested = (record->reserved[0] & 512) ? record->values[12] : 0;
    if (!requested && !gEnhancedExtraOptions.clock_speed && !gClockState.shifted) return;
    if (!advance(1)) return;
    record->reserved[0] |= 1024;
    record->values[13] = gClockState.seconds;
    record->values[14] = gClockState.wall;
    record->values[15] = gClockState.shifted;
    record->values[16] = gClockState.bonus_minutes;
    record->values[17] = gClockState.bonus_seconds;
}
int EnhancedClockSave(void *save) {
    int result = NativeSaveGame(save);
    if (result == 2 && save == EnhancedSettingsSaveData() &&
        (gEnhancedExtraOptions.clock_speed || gClockState.shifted)) {
        if (EnhancedSettingsStore(gEnhancedOptions.trade_evolutions, gEnhancedOptions.reusable_tms,
                gEnhancedOptions.visible_encounters, gEnhancedOptions.repel_prompt,
                gEnhancedOptions.capture_exp, gEnhancedOptions.party_exp)) ++gClockState.saves;
        else ++gClockState.save_failures;
    }
    return result;
}
static int grow(void *pots, void *properties) {
    if (!advance(0) || !gClockState.bonus_minutes) return 0;
    u32 minutes = gClockState.bonus_minutes;
    gClockState.bonus_minutes = 0;
    NativeBerryAdvance(pots, properties, minutes);
    gClockState.berry_minutes += minutes;
    return 1;
}
void EnhancedClockPlant(void *pots, u32 index, void *properties, u32 berry) {
    /* The native app plants on return from the Bag, before its normal update.
     * Settle elapsed bonus for existing plants before creating the new seed. */
    grow(pots, properties);
    NativeBerryPlant(pots, index, properties, berry);
}
void EnhancedClockBerry(void *data, int redraw) {
    NativeBerryUpdate(data, redraw);
    if (!grow(*(void **)((u8 *)data + 0x14), *(void **)((u8 *)data + 0x1C))) return;
    NativeBerryStatus(data);
    if (redraw) NativeBerryRedraw(data);
}
u32 EnhancedClockText(char *text) {
    u32 seconds = EnhancedClockSeconds();
    u32 hour = EnhancedUnsignedDivide(seconds, 3600);
    u32 minute = EnhancedUnsignedDivide(mod(seconds, 3600), 60);
    u32 second = mod(seconds, 60);
    text[0] = '0' + EnhancedUnsignedDivide(hour, 10); text[1] = '0' + mod(hour, 10); text[2] = ':';
    text[3] = '0' + EnhancedUnsignedDivide(minute, 10); text[4] = '0' + mod(minute, 10); text[5] = ':';
    text[6] = '0' + EnhancedUnsignedDivide(second, 10); text[7] = '0' + mod(second, 10); text[8] = 0;
    return seconds;
}
