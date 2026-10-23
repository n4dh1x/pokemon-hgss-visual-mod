#include "settings.h"

extern int FlashLoadChunk(u32 offset, void *data, u32 size);
extern int FlashWriteChunk(u32 offset, void *data, u32 size);
extern void *Save_PlayerData_GetProfile(void *save);
extern u32 PlayerProfile_GetTrainerID(void *profile);
extern void Sys_SetSleepDisableFlag(u32 flag);
extern void Sys_ClearSleepDisableFlag(u32 flag);

/* Both USA save-layout tables and all six extra-chunk size routines are
 * checked by the builder. Native main/extra data ends before these pages. */
static const u32 journal_offsets[2] = {0x3F000, 0x7F000};
struct SettingsState {
    void *save;
    u32 owner, loaded, sequence;
    s32 last_slot;
    u32 writable[2], saves, status;
    struct EnhancedJournal pages[2];
    struct EnhancedJournal pending, verify;
};
struct SettingsState gSettingsState;
volatile struct EnhancedExtraOptions gEnhancedExtraOptions;
_Static_assert(sizeof(struct SettingsState) == 1060, "Settings diagnostic ABI");

u32 EnhancedSettingsCRC(const void *data, u32 size) {
    const u8 *bytes = data;
    u32 crc = ~0u;
    for (u32 i = 0; i < size; ++i) {
        crc ^= bytes[i];
        for (int bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

static int valid_format(const struct EnhancedJournal *r) {
    return r->magic == ENHANCED_JOURNAL_MAGIC && r->version == ENHANCED_JOURNAL_VERSION &&
        r->count == ENHANCED_SETTINGS_COUNT && r->values[0] <= 1 &&
        r->values[1] <= 1 && r->values[2] <= 3 &&
        (!(r->reserved[0] & 1) || r->values[3] <= 1) &&
        (!(r->reserved[0] & 2) || r->values[4] <= 1) &&
        (!(r->reserved[0] & 4) || r->values[5] <= 1) &&
        (!(r->reserved[0] & 8) || r->values[6] <= 1) &&
        (!(r->reserved[0] & 16) || r->values[7] <= 1) &&
        (!(r->reserved[0] & 32) || r->values[8] <= 1) &&
        (!(r->reserved[0] & 64) || r->values[9] <= 4) &&
        (!(r->reserved[0] & 128) || r->values[10] <= 5) &&
        r->checksum == EnhancedSettingsCRC(r, 252);
}
int EnhancedSettingsValid(const struct EnhancedJournal *r, u32 owner) {
    return r->owner == owner && valid_format(r);
}
static int erased(const struct EnhancedJournal *r) {
    const u32 *words = (const u32 *)r;
    /* Backup devices use erased FF; some emulator saves initialize unused
     * space to zero. Only a uniform page is considered unoccupied. */
    u32 fill = words[0];
    if (fill != 0 && fill != ~0u) return 0;
    for (int i = 0; i < 64; ++i)
        if (words[i] != fill)
            return 0;
    return 1;
}

void EnhancedSettingsEnsure(void *field) {
    void *save = *(void **)((u8 *)field + 12);
    u32 owner = PlayerProfile_GetTrainerID(Save_PlayerData_GetProfile(save));
    if (gSettingsState.loaded && gSettingsState.save == save && gSettingsState.owner == owner)
        return;
    gSettingsState.save = save;
    gSettingsState.owner = owner;
    gSettingsState.loaded = 1;
    gSettingsState.sequence = 0;
    gSettingsState.last_slot = -1;
    gSettingsState.status = 0;
    gEnhancedOptions.trade_evolutions = 1;
    gEnhancedOptions.reusable_tms = 1;
    gEnhancedOptions.visible_encounters = 1;
    gEnhancedOptions.repel_prompt = 1;
    gEnhancedOptions.capture_exp = 1;
    gEnhancedOptions.party_exp = 1;
    gEnhancedExtraOptions.field_hms = 1;
    gEnhancedExtraOptions.roaming_only_grass = 0;
    gEnhancedExtraOptions.iv_ev_viewer = 1;
    gEnhancedExtraOptions.encounter_rate = 0;
    gEnhancedExtraOptions.shiny_odds = 0;
    for (int i = 0; i < 2; ++i) {
        struct EnhancedJournal *r = &gSettingsState.pages[i];
        int read = FlashLoadChunk(journal_offsets[i], r, sizeof(*r));
        /* Unknown occupied pages, including future format versions, are never
         * overwritten. A damaged current-format page can be repaired. */
        gSettingsState.writable[i] = read && (erased(r) ||
            (r->magic == ENHANCED_JOURNAL_MAGIC && r->version == ENHANCED_JOURNAL_VERSION));
        if (read && EnhancedSettingsValid(r, owner) &&
            (gSettingsState.last_slot < 0 || (s32)(r->sequence - gSettingsState.sequence) > 0)) {
            gSettingsState.last_slot = i;
            gSettingsState.sequence = r->sequence;
            gEnhancedOptions.trade_evolutions = r->values[0];
            gEnhancedOptions.reusable_tms = r->values[1];
            gEnhancedOptions.visible_encounters = r->values[2];
            /* The presence bit distinguishes legacy padding from explicit Off. */
            gEnhancedOptions.repel_prompt = (r->reserved[0] & 1) ? r->values[3] : 1;
            gEnhancedOptions.capture_exp = (r->reserved[0] & 2) ? r->values[4] : 1;
            gEnhancedOptions.party_exp = (r->reserved[0] & 4) ? r->values[5] : 1;
            gEnhancedExtraOptions.field_hms = (r->reserved[0] & 8) ? r->values[6] : 1;
            gEnhancedExtraOptions.roaming_only_grass = (r->reserved[0] & 16) ? r->values[7] : 0;
            gEnhancedExtraOptions.iv_ev_viewer = (r->reserved[0] & 32) ? r->values[8] : 1;
            gEnhancedExtraOptions.encounter_rate = (r->reserved[0] & 64) ? r->values[9] : 0;
            gEnhancedExtraOptions.shiny_odds = (r->reserved[0] & 128) ? r->values[10] : 0;
        }
    }
}

void *EnhancedSettingsSaveData(void) {
    return gSettingsState.loaded ? gSettingsState.save : 0;
}

int EnhancedSettingsOwner(u32 *owner) {
    if (!gSettingsState.loaded || !gSettingsState.save) return 0;
    u32 current = PlayerProfile_GetTrainerID(Save_PlayerData_GetProfile(gSettingsState.save));
    if (current != gSettingsState.owner) return 0;
    *owner = current;
    return 1;
}

int EnhancedSettingsStore(u32 trade, u32 tms, u32 visible, u32 repel, u32 capture, u32 party) {
    /* Old callers preserve auxiliary and unknown journal fields. */
    return EnhancedSettingsStoreAll(trade, tms, visible, repel, capture, party, 0);
}

int EnhancedSettingsStoreAll(u32 trade, u32 tms, u32 visible, u32 repel,
        u32 capture, u32 party, const struct EnhancedExtraOptions *extra) {
    if (!gSettingsState.loaded || trade > 1 || tms > 1 || visible > 3 || repel > 1 || capture > 1 || party > 1)
        return 0;
    if (extra && (extra->field_hms > 1 || extra->roaming_only_grass > 1 || extra->iv_ev_viewer > 1 || extra->encounter_rate > 4 || extra->shiny_odds > 5)) return 0;
    int target = gSettingsState.last_slot < 0 ? 0 : 1 - gSettingsState.last_slot;
    if (gSettingsState.last_slot < 0 && !gSettingsState.writable[target])
        target = 1;
    if (!gSettingsState.writable[target]) {
        gSettingsState.status = 2;
        return 0;
    }
    struct EnhancedJournal *r = &gSettingsState.pending;
    u32 *words = (u32 *)r;
    for (int i = 0; i < 64; ++i)
        words[i] = 0;
    r->magic = ENHANCED_JOURNAL_MAGIC;
    r->version = ENHANCED_JOURNAL_VERSION;
    r->sequence = gSettingsState.sequence + 1;
    r->owner = gSettingsState.owner;
    r->count = ENHANCED_SETTINGS_COUNT;
    if (gSettingsState.last_slot >= 0) {
        for (int i = 0; i < ENHANCED_SETTINGS_COUNT; ++i)
            r->values[i] = gSettingsState.pages[gSettingsState.last_slot].values[i];
        for (int i = 0; i < 10; ++i)
            r->reserved[i] = gSettingsState.pages[gSettingsState.last_slot].reserved[i];
    }
    r->values[0] = trade;
    r->values[1] = tms;
    r->values[2] = visible;
    r->values[3] = repel;
    r->values[4] = capture;
    r->values[5] = party;
    r->reserved[0] |= 7;
    if (extra) {
        r->values[6] = extra->field_hms;
        r->values[7] = extra->roaming_only_grass;
        r->values[8] = extra->iv_ev_viewer;
        r->values[9] = extra->encounter_rate;
        r->values[10] = extra->shiny_odds;
        r->reserved[0] |= 248;
    }
    r->checksum = EnhancedSettingsCRC(r, 252);
    Sys_SetSleepDisableFlag(1);
    int result = FlashWriteChunk(journal_offsets[target], r, sizeof(*r));
    if (result)
        result = FlashLoadChunk(journal_offsets[target], &gSettingsState.verify, sizeof(*r));
    Sys_ClearSleepDisableFlag(1);
    if (result) {
        const u32 *a = (const u32 *)r;
        const u32 *b = (const u32 *)&gSettingsState.verify;
        for (int i = 0; i < 64; ++i)
            if (a[i] != b[i])
                result = 0;
    }
    if (!result) {
        gSettingsState.status = 3;
        return 0;
    }
    u32 *dst = (u32 *)&gSettingsState.pages[target];
    for (int i = 0; i < 64; ++i)
        dst[i] = words[i];
    gSettingsState.last_slot = target;
    gSettingsState.sequence = r->sequence;
    ++gSettingsState.saves;
    gSettingsState.status = 1;
    gEnhancedOptions.trade_evolutions = trade;
    gEnhancedOptions.reusable_tms = tms;
    gEnhancedOptions.visible_encounters = visible;
    gEnhancedOptions.repel_prompt = repel;
    gEnhancedOptions.capture_exp = capture;
    gEnhancedOptions.party_exp = party;
    if (extra) {
        gEnhancedExtraOptions.field_hms = extra->field_hms;
        gEnhancedExtraOptions.roaming_only_grass = extra->roaming_only_grass;
        gEnhancedExtraOptions.iv_ev_viewer = extra->iv_ev_viewer;
        gEnhancedExtraOptions.encounter_rate = extra->encounter_rate;
        gEnhancedExtraOptions.shiny_odds = extra->shiny_odds;
    }
    return 1;
}
