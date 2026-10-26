#include "config.h"
#include "settings.h"

/* USA ABI offsets are checked against both pinned Visual+ images. Use native
 * Pokemon APIs and copy the whole encrypted 236-byte Pokemon, never rebuild it. */
struct ObjectEvent {
    u16 id, sprite, movement, type, flag, script;
    s16 facing;
    u16 parameter[3];
    s16 range_x, range_z;
    u16 x, z;
    s32 y;
};
_Static_assert(sizeof(struct ObjectEvent) == 32, "Object event ABI");

extern void EnhancedFollowerUpdate(void *field);
extern void EnhancedClockHudBefore(void *field);
extern void EnhancedClockHudShow(void *field);
extern void EnhancedClockHudForget(void *manager);
extern int OriginalFieldInput(void *input, void *field);
extern void OriginalFieldControl(void *field);
extern int FieldMovementAllowed(void *field);
extern int OriginalStepEncounter(void *field);
extern int OriginalEncounterRoll(void *field, u8 rate, u8 tile);
extern int OriginalRoamerCheck(void *field, void **roamer);
extern void OriginalStartEncounter(void *field, void *setup);
extern void OriginalStartScript(void *field, u16 script, void *object);
extern u32 NativeMapObjectId(void *object);
extern void *NativeFieldSparkle(void *object);
extern int PlaySE(int sequence);
extern int OriginalObjectIterator(void *manager, void **object, int *index, u32 mask);
extern void Heap_FreeExplicit(int heap, void *memory);
extern void *SaveArray_Party_Get(void *save);
extern int Party_GetCount(void *party);
extern void *Party_GetMonByIndex(void *party, int index);
extern void *Save_Roamers_Get(void *save);
extern int RoamerSave_RepelNotInUse(void *roamers);
extern u32 GetMonData(void *mon, int field, void *destination);
extern int MonIsShiny(void *mon);
extern int MapHeader_HasWildEncounters(u32 map);
extern void *Save_VarsFlags_Get(void *save);
extern int CheckPartner(void *flags);
extern int CheckSafari(void *flags);
extern int CheckContest(void *flags);
extern int CheckPalPark(void *flags);
extern int NativeEncounterTile(u8 tile);
extern int NativeSurfableTile(u8 tile);
extern u8 GetMetatileBehavior(void *field, int x, int z);
extern int TerrainBlocked(void *field, int x, int z);
extern int ObjectCollision(void *object, int x, int y, int z);
extern int MovementBlocked(void *field, void *position, int x, int z, void *flags);
extern int MovementFinished(void *object);
extern int ClearMovementIfFinished(void *object);
extern void SetHeldMovement(void *object, u32 command);
extern u32 LCRandom(void);
extern void *CreateObject(void *manager, struct ObjectEvent *event, u32 map);
extern void MapObject_Remove(void *object);
extern u32 FollowMon_GetSpriteID(int species, u16 form, int gender);
extern void FollowMon_SetObjectParams(void *object, int species, u8 form, int shiny);
extern void SetPokemonHidden(void *object, int hidden);
extern void *BattleSetup_New(int heap, u32 type);
extern void BattleSetup_InitFromFieldSystem(void *setup, void *field);
extern void BattleSetup_Delete(void *setup);
extern void BattleSetup_AddMonToParty(void *setup, void *mon, int battler);

static u32 word(void *pointer, unsigned offset) {
    return *(u32 *)((u8 *)pointer + offset);
}
static void *ptr(void *pointer, unsigned offset) {
    return *(void **)((u8 *)pointer + offset);
}
static void put(void *pointer, unsigned offset, u32 value) {
    *(u32 *)((u8 *)pointer + offset) = value;
}
static int distance(int a, int b) { int d = a - b; return d < 0 ? -d : d; }
static int grass(u8 tile) { return tile == 2 || tile == 3; }

struct VisibleSlot {
    void *object;
    u32 id, map;
    u32 mon[59];
    u32 species, level, personality;
};
struct VisibleState {
    void *manager;
    u32 capture;
    void *captured;
    u32 tick, generated, launched, save_filtered, failures;
    struct VisibleSlot slots[6];
    u32 roam_delay[6], walk_commands, paused_mask;
    u32 suppress_ordinary, discarded_ordinary;
    u32 repelled_contacts, map_releases;
    u32 blocked_grass_steps;
};
/* Counters aid emulator verification. They are session-only, not save data. */
struct VisibleState gVisibleState;
_Static_assert(sizeof(struct VisibleSlot) == 260, "Visible slot diagnostic ABI");
_Static_assert(sizeof(struct VisibleState) == 1644, "Visible state diagnostic ABI");

static int owned(void *object) {
    if (!object || !gVisibleState.manager || !(word(object, 0) & 1) ||
        ptr(object, 0xB4) != gVisibleState.manager)
        return -1;
    for (int i = 0; i < 6; ++i)
        if (gVisibleState.slots[i].object == object &&
            word(object, 8) == gVisibleState.slots[i].id &&
            word(object, 0x0C) == gVisibleState.slots[i].map)
            return i;
    return -1;
}

struct VisibleRoamerSlot {
    u32 identity, record[5], battle_type;
};
struct VisibleRoamerState {
    u32 capture_slot;
    void *candidate;
    u32 selected, duplicates, stale, launched;
    struct VisibleRoamerSlot slots[6];
};
struct VisibleRoamerState gVisibleRoamerState;
_Static_assert(sizeof(struct VisibleRoamerState) == 192, "Visible roamer diagnostic ABI");

/* Roamer save records are four native 20-byte entries following a 16-byte
 * header. Validate pointer membership before any candidate dereference. */
static u32 roamer_identity(void *field, void *candidate) {
    u8 *base = Save_Roamers_Get(ptr(field, 0x0C));
    for (u32 i = 0; i < 4; ++i)
        if (candidate == base + 16 + i * 20)
            return i + 1;
    return 0;
}
static int roamer_current(void *field, int index) {
    struct VisibleRoamerSlot *slot = &gVisibleRoamerState.slots[index];
    if (!slot->identity) return 1;
    if (slot->identity > 4) return 0;
    u8 *base = Save_Roamers_Get(ptr(field, 0x0C));
    u32 *record = (u32 *)(base + 16 + (slot->identity - 1) * 20);
    if (!(record[4] & 0xFF0000) || record[0] != word(ptr(field, 0x20), 0)) return 0;
    for (int i = 0; i < 5; ++i)
        if (record[i] != slot->record[i]) return 0;
    return 1;
}

/* Session-only surface identity prevents a surf spawn crossing onto land.
 * The original tile flags, encounter tables and generator remain authoritative. */
struct VisibleHabitatState {
    u32 slots[6], spawned[4], surface_releases;
};
struct VisibleHabitatState gVisibleHabitatState;
_Static_assert(sizeof(struct VisibleHabitatState) == 44, "Visible habitat diagnostic ABI");

u32 EnhancedTileHabitat(u8 tile) {
    if (!NativeEncounterTile(tile)) return 0;
    if (NativeSurfableTile(tile)) return 3;
    return grass(tile) ? 1 : 2;
}
static u32 player_habitat(void *field, void *player) {
    u32 habitat = EnhancedTileHabitat(GetMetatileBehavior(field,
        word(player, 0x64), word(player, 0x6C)));
    int surfing = word(ptr(field, 0x40), 0x18) == 2;
    if ((habitat == 3) != surfing) return 0;
    return habitat;
}
static int compatible_surface(void *field, int index) {
    void *object = gVisibleState.slots[index].object;
    u32 habitat = gVisibleHabitatState.slots[index];
    int surfing = word(ptr(field, 0x40), 0x18) == 2;
    return habitat && ((habitat == 3) == surfing) &&
        EnhancedTileHabitat(GetMetatileBehavior(field,
            word(object, 0x64), word(object, 0x6C))) == habitat;
}

struct VisibleVisualState {
    u32 pending_slot, pending_sprite, owned_lookups, construction_lookups, native_lookups;
    u32 sparkles, sparkle_failures, sparkle_ticks[6], chimes;
};
struct VisibleVisualState gVisibleVisualState;
_Static_assert(sizeof(struct VisibleVisualState) == 56, "Visible visuals diagnostic ABI");

/* Only two palette-local identity queries call this. The real object ID is
 * never changed, and other NPC/follower queries retain the native getter. */
u32 EnhancedPaletteObjectId(void *object) {
    if (owned(object) >= 0) {
        ++gVisibleVisualState.owned_lookups;
        return 0xFD;
    }
    u32 pending = gVisibleVisualState.pending_slot;
    if (object && pending >= 1 && pending <= 6) {
        struct VisibleSlot *slot = &gVisibleState.slots[pending - 1];
        if ((word(object, 0) & 1) && ptr(object, 0xB4) == gVisibleState.manager &&
            word(object, 8) == slot->id && word(object, 0x0C) == slot->map &&
            word(object, 0x10) == gVisibleVisualState.pending_sprite &&
            word(object, 0x38) == slot->species) {
            ++gVisibleVisualState.construction_lookups;
            return 0xFD;
        }
    }
    ++gVisibleVisualState.native_lookups;
    return NativeMapObjectId(object);
}

/* Native seed_kira field glints use a short, self-deleting task with reference-
 * counted renderer resources. They retain a world position, never a Pokemon or
 * map-object pointer. Each new burst samples the moving object's current pose. */
static void shiny_sparkle(void *field, int index, int appearance) {
    void *object = gVisibleState.slots[index].object;
    if (owned(object) != index || !(word(object, 0x40) & 1))
        return;
    if (ptr(field, 0x44) && NativeFieldSparkle(object))
        ++gVisibleVisualState.sparkles;
    else
        ++gVisibleVisualState.sparkle_failures;
    if (appearance) {
        PlaySE(2340); /* SEQ_SE_GS_KIRAKIRA: brief native glint sound. */
        ++gVisibleVisualState.chimes;
    }
    gVisibleVisualState.sparkle_ticks[index] = 120;
}

static void forget(void) {
    gVisibleVisualState.pending_slot = 0;
    gVisibleRoamerState.capture_slot = 0;
    gVisibleRoamerState.candidate = 0;
    for (int i = 0; i < 6; ++i)
        gVisibleState.slots[i].object = 0;
    gVisibleState.manager = 0;
    gVisibleState.tick = 0;
    gVisibleState.paused_mask = 0;
    for (int i = 0; i < 6; ++i) {
        gVisibleState.roam_delay[i] = 0;
        gVisibleVisualState.sparkle_ticks[i] = 0;
        gVisibleHabitatState.slots[i] = 0;
        gVisibleRoamerState.slots[i].identity = 0;
    }
}

static void pause_wilds(int paused) {
    for (int i = 0; i < 6; ++i) {
        void *object = gVisibleState.slots[i].object;
        if (owned(object) != i)
            continue;
        u32 flags = word(object, 0);
        if (paused && !(flags & 2)) {
            /* Native held movements run even when the normal NPC pause flag
             * is set. SINGLE_MOVEMENT blocks their update at its entry. */
            put(object, 0, flags | 2);
            gVisibleState.paused_mask |= 1u << i;
        } else if (!paused && (gVisibleState.paused_mask & (1u << i))) {
            put(object, 0, flags & ~2u);
            gVisibleState.paused_mask &= ~(1u << i);
        }
    }
}

void EnhancedFieldControl(void *field) {
    EnhancedClockHudBefore(field);
    EnhancedSettingsEnsure(field);
    pause_wilds(!FieldMovementAllowed(field));
    OriginalFieldControl(field);
    pause_wilds(!FieldMovementAllowed(field));
    EnhancedClockHudShow(field);
}

void EnhancedManagerDelete(void *manager) {
    EnhancedClockHudForget(manager);
    if (manager == gVisibleState.manager)
        forget();
    /* Exact original destructor; no graphics calls after the field unload. */
    Heap_FreeExplicit(11, ptr(manager, 0x124));
    Heap_FreeExplicit(11, manager);
}

int EnhancedSaveIterator(void *manager, void **object, int *index, u32 mask) {
    while (OriginalObjectIterator(manager, object, index, mask)) {
        if (owned(*object) < 0)
            return 1;
        ++gVisibleState.save_filtered;
    }
    return 0;
}

static int regular(void *field) {
    if (!MapHeader_HasWildEncounters(word(ptr(field, 0x20), 0)))
        return 0;
    void *flags = Save_VarsFlags_Get(ptr(field, 0x0C));
    return !CheckPartner(flags) && !CheckSafari(flags) &&
           !CheckContest(flags) && !CheckPalPark(flags);
}

static int alive(void *field) {
    void *party = SaveArray_Party_Get(ptr(field, 0x0C));
    int count = Party_GetCount(party);
    if (count < 1 || count > 6)
        return 0;
    for (int i = 0; i < count; ++i) {
        void *mon = Party_GetMonByIndex(party, i);
        if (GetMonData(mon, 5, 0) && !GetMonData(mon, 76, 0) && GetMonData(mon, 163, 0))
            return 1;
    }
    return 0;
}

static int repel_allows_contact(void *field, u32 wild_level) {
    void *save = ptr(field, 0x0C);
    if (RoamerSave_RepelNotInUse(Save_Roamers_Get(save)))
        return 1;
    /* Match HGSS's current first alive, non-egg party member. A Repel used or
     * a party reordered after spawning must affect unsolicited contact now. */
    void *party = SaveArray_Party_Get(save);
    int count = Party_GetCount(party);
    if (count < 1 || count > 6)
        return 0;
    for (int i = 0; i < count; ++i) {
        void *mon = Party_GetMonByIndex(party, i);
        if (GetMonData(mon, 5, 0) && !GetMonData(mon, 76, 0) && GetMonData(mon, 163, 0))
            return GetMonData(mon, 161, 0) <= wild_level;
    }
    return 0;
}

/* The native legendary check follows the ordinary rate roll. Preserve its
 * normal-rate decision before independently scaling ordinary encounters. The
 * cached result is consumed once by that same synchronous native call chain. */
struct EncounterRateState {
    void *field, *roamer;
    u32 cached, native_rolls, scaled_rolls, roamer_preserved, off_blocks;
};
struct EncounterRateState gEncounterRateState;
_Static_assert(sizeof(struct EncounterRateState) == 28, "Encounter-rate diagnostic ABI");
u32 EnhancedEncounterPercent(void) {
    static const u8 percent[5] = {100, 0, 25, 50, 200};
    u32 setting = gEnhancedExtraOptions.encounter_rate;
    return setting < 5 ? percent[setting] : 100;
}
u32 EnhancedSpawnInterval(void) {
    static const u16 interval[5] = {60, 0, 240, 120, 30};
    u32 setting = gEnhancedExtraOptions.encounter_rate;
    return setting < 5 ? interval[setting] : 60;
}
int EnhancedEncounterRoll(void *field, u8 rate, u8 tile) {
    gEncounterRateState.cached = 0;
    if (gVisibleState.capture) return 1;
    u32 percent = EnhancedEncounterPercent();
    if (percent == 100 || !regular(field))
        return OriginalEncounterRoll(field, rate, tile);
    ++gEncounterRateState.native_rolls;
    int native = OriginalEncounterRoll(field, rate, tile);
    void *roamer = 0;
    if (native && OriginalRoamerCheck(field, &roamer)) {
        gEncounterRateState.field = field;
        gEncounterRateState.roamer = roamer;
        gEncounterRateState.cached = 1;
        ++gEncounterRateState.roamer_preserved;
        return 1;
    }
    int result = 0;
    if (percent) {
        u32 scaled = (u32)rate * percent / 100;
        if (scaled > 100) scaled = 100; /* Clamp before narrowing to u8. */
        ++gEncounterRateState.scaled_rolls;
        result = OriginalEncounterRoll(field, (u8)scaled, tile);
    } else ++gEncounterRateState.off_blocks;
    if (result) {
        gEncounterRateState.field = field;
        gEncounterRateState.roamer = 0;
        gEncounterRateState.cached = 1;
    }
    return result;
}
int EnhancedRoamerCheck(void *field, void **roamer) {
    if (gVisibleState.capture) {
        if (!gVisibleRoamerState.capture_slot || !roamer) return 0;
        if (!OriginalRoamerCheck(field, roamer)) return 0;
        u32 identity = roamer_identity(field, *roamer);
        if (!identity) return 0;
        static const u16 species[4] = {243, 244, 380, 381};
        u32 *record = *roamer;
        if (!(record[4] & 0xFF0000) || record[0] != word(ptr(field, 0x20), 0) ||
            (record[3] & 0xFFFF) != species[identity - 1]) return 0;
        for (int i = 0; i < 6; ++i)
            if (owned(gVisibleState.slots[i].object) == i &&
                gVisibleRoamerState.slots[i].identity == identity) {
                ++gVisibleRoamerState.duplicates;
                return 0;
            }
        gVisibleRoamerState.candidate = *roamer;
        return 1;
    }
    if (gEncounterRateState.cached && gEncounterRateState.field == field) {
        gEncounterRateState.cached = 0;
        *roamer = gEncounterRateState.roamer;
        return *roamer != 0;
    }
    return OriginalRoamerCheck(field, roamer);
}
void EnhancedCaptureEncounter(void *field, void *setup) {
    if (gVisibleState.capture)
        gVisibleState.captured = setup;
    else
        OriginalStartEncounter(field, setup);
}
int EnhancedStepEncounter(void *field) {
    void *player = ptr(ptr(field, 0x40), 0x30);
    u32 mode = gEnhancedOptions.visible_encounters;
    if (gEnhancedExtraOptions.roaming_only_grass && mode >= 1 && mode <= 3 &&
        regular(field) && alive(field) &&
        grass(GetMetatileBehavior(field, word(player, 0x64), word(player, 0x6C)))) {
        /* Explicit contact-only mode must not start ANY hidden grass battle,
         * including the native rare-roamer branch. Sprite generation calls
         * OriginalStepEncounter directly and remains enabled. */
        ++gVisibleState.blocked_grass_steps;
        return 0;
    }
    return OriginalStepEncounter(field);
}

static void release_slot(int index) {
    void *object = gVisibleState.slots[index].object;
    if (owned(object) == index)
        MapObject_Remove(object);
    gVisibleState.slots[index].object = 0;
    gVisibleState.roam_delay[index] = 0;
    gVisibleVisualState.sparkle_ticks[index] = 0;
    gVisibleHabitatState.slots[index] = 0;
    gVisibleRoamerState.slots[index].identity = 0;
    gVisibleState.paused_mask &= ~(1u << index);
}

static int launch(void *field, int index) {
    if (owned(gVisibleState.slots[index].object) != index)
        return 0;
    u32 mode = gEnhancedOptions.visible_encounters;
    /* Native A interaction dispatches before our ordinary free-input loop.
     * Validate here too, including immediately after an option/map/context
     * change, before constructing any battle or consuming the stored Pokemon. */
    if (!mode || mode > 3 || !EnhancedEncounterPercent() || (u32)index >= mode * 2 ||
        gVisibleState.slots[index].map != word(ptr(field, 0x20), 0) || !regular(field) ||
        !compatible_surface(field, index) || !roamer_current(field, index)) {
        if (gVisibleState.slots[index].map != word(ptr(field, 0x20), 0))
            ++gVisibleState.map_releases;
        release_slot(index);
        return 0;
    }
    if (!alive(field))
        return 0;
    u32 battle_type = gVisibleRoamerState.slots[index].identity ? 0x100 : 0;
    void *setup = BattleSetup_New(11, battle_type);
    if (!setup) {
        gVisibleRoamerState.candidate = 0;
        return 0;
    }
    BattleSetup_InitFromFieldSystem(setup, field);
    BattleSetup_AddMonToParty(setup, gVisibleState.slots[index].mon, 1);
    if (battle_type) ++gVisibleRoamerState.launched;
    release_slot(index);
    ++gVisibleState.launched;
    OriginalStartEncounter(field, setup);
    return 1;
}

void EnhancedStartScript(void *field, u16 script, void *object) {
    int index = owned(object);
    if (index >= 0) {
        launch(field, index);
        return;
    }
    OriginalStartScript(field, script, object);
}

static int generate(void *field, struct VisibleSlot *slot, int index) {
    /* The native generator uses current HGSS tables/abilities/Repel and rolls
     * PID/IVs/form once. Capture its successful battle setup, copy its Pokemon,
     * then free all setup allocations; player data is refreshed at contact. */
    u32 counters = word(field, 0x7C);
    u16 facing = *(u16 *)((u8 *)field + 0x7A);
    *(u16 *)((u8 *)field + 0x7E) = 4;
    gVisibleState.captured = 0;
    gVisibleRoamerState.capture_slot = (u32)index + 1;
    gVisibleRoamerState.candidate = 0;
    gVisibleRoamerState.slots[index].identity = 0;
    gVisibleState.capture = 1;
    OriginalStepEncounter(field);
    gVisibleState.capture = 0;
    gVisibleRoamerState.capture_slot = 0;
    put(field, 0x7C, counters);
    *(u16 *)((u8 *)field + 0x7A) = facing;
    void *setup = gVisibleState.captured;
    gVisibleState.captured = 0;
    if (!setup) {
        gVisibleRoamerState.candidate = 0;
        return 0;
    }
    void *party = ptr(setup, 8);
    int valid = Party_GetCount(party) == 1;
    if (valid) {
        u32 *mon = Party_GetMonByIndex(party, 0);
        for (int i = 0; i < 59; ++i)
            slot->mon[i] = mon[i];
        slot->species = GetMonData(slot->mon, 5, 0);
        slot->level = GetMonData(slot->mon, 161, 0);
        slot->personality = GetMonData(slot->mon, 0, 0);
        valid = slot->species >= 1 && slot->species <= 493;
    }
    u32 battle_type = word(setup, 0);
    if (valid && battle_type == 0x100) {
        u32 identity = roamer_identity(field, gVisibleRoamerState.candidate);
        valid = identity != 0;
        if (valid) {
            struct VisibleRoamerSlot *rs = &gVisibleRoamerState.slots[index];
            u32 *record = gVisibleRoamerState.candidate;
            rs->identity = identity;
            for (int i = 0; i < 5; ++i) rs->record[i] = record[i];
            rs->battle_type = battle_type;
            valid = roamer_current(field, index) && slot->personality == record[2] &&
                slot->species == (record[3] & 0xFFFF) && slot->level == (record[4] & 0xFF);
            if (valid) ++gVisibleRoamerState.selected;
        }
    } else if (battle_type) valid = 0;
    if (!valid) gVisibleRoamerState.slots[index].identity = 0;
    gVisibleRoamerState.candidate = 0;
    BattleSetup_Delete(setup);
    return valid;
}

static void spawn(void *field, void *player, int index, u32 habitat) {
    int px = word(player, 0x64), pz = word(player, 0x6C);
    int x = px, z = pz, found = 0;
    for (int attempt = 0; attempt < 24; ++attempt) {
        u32 random = LCRandom();
        x = px + (int)(random & 7) - 3;
        z = pz + (int)((random >> 3) & 7) - 3;
        if (distance(x, px) + distance(z, pz) < 2 || x < 0 || z < 0)
            continue;
        if (EnhancedTileHabitat(GetMetatileBehavior(field, x, z)) != habitat || TerrainBlocked(field, x, z) ||
            MovementBlocked(field, (u8 *)player + 0x70, x, z, 0) ||
            ObjectCollision(player, x, word(player, 0x68), z))
            continue;
        found = 1;
        break;
    }
    if (!found)
        return;
    struct VisibleSlot *slot = &gVisibleState.slots[index];
    void *manager = ptr(field, 0x3C);
    /* Avoid both the helper's ID-zero reuse and collisions with authored IDs. */
    u32 id = 0xE0 + (u32)index;
    u32 count = word(manager, 4);
    u8 *objects = ptr(manager, 0x124);
    if (count > 64)
        return;
    for (u32 i = 0; i < count; ++i)
        if ((word(objects + i * 0x12C, 0) & 1) && word(objects + i * 0x12C, 8) == id)
            return;
    if (!generate(field, slot, index))
        return;
    u16 form = (u16)GetMonData(slot->mon, 112, 0);
    struct ObjectEvent event;
    event.id = (u16)id;
    event.sprite = (u16)FollowMon_GetSpriteID(slot->species, form, GetMonData(slot->mon, 111, 0));
    event.movement = 0;
    event.type = 0;
    event.flag = 0;
    event.script = 0;
    event.facing = 1;
    /* Native graphics initialize synchronously inside CreateObject. Prepare
     * their parameters first using the original parameter-only helper on a
     * bounded scratch prefix; it accesses only param[0..2] at offsets38..40. */
    u32 parameters[17];
    parameters[14] = parameters[15] = parameters[16] = 0;
    FollowMon_SetObjectParams(parameters, slot->species, (u8)form, MonIsShiny(slot->mon));
    event.parameter[0] = (u16)parameters[14];
    event.parameter[1] = (u16)parameters[15];
    event.parameter[2] = (u16)parameters[16];
    event.range_x = event.range_z = 0;
    event.x = (u16)x;
    event.z = (u16)z;
    event.y = (s32)word(player, 0x74);
    slot->map = word(ptr(field, 0x20), 0);
    slot->id = id;
    gVisibleVisualState.pending_slot = (u32)index + 1;
    gVisibleVisualState.pending_sprite = event.sprite;
    void *object = CreateObject(manager, &event, slot->map);
    gVisibleVisualState.pending_slot = 0;
    if (!object) {
        ++gVisibleState.failures;
        return;
    }
    put(object, 0, (word(object, 0) | (1u << 13) | (1u << 10) | (1u << 29)) & ~0x180u);
    SetPokemonHidden(object, 0);
    slot->object = object;
    slot->id = id;
    gVisibleHabitatState.slots[index] = habitat;
    ++gVisibleHabitatState.spawned[habitat];
    ++gVisibleState.generated;
    gVisibleState.roam_delay[index] = 45 + (LCRandom() & 63);
    shiny_sparkle(field, index, 1);
}

static int roam(void *field, int index) {
    void *object = gVisibleState.slots[index].object;
    if ((word(object, 0) & (2u | (1u << 6) | (1u << 9))) || !MovementFinished(object))
        return 0;
    ClearMovementIfFinished(object);
    if (gVisibleState.roam_delay[index]) {
        --gVisibleState.roam_delay[index];
        return 0;
    }
    u32 random = LCRandom();
    gVisibleState.roam_delay[index] = 45 + ((random >> 3) & 63);
    int direction = random & 3;
    int x = word(object, 0x64), z = word(object, 0x6C);
    x += direction == 2 ? -1 : direction == 3 ? 1 : 0;
    z += direction == 0 ? -1 : direction == 1 ? 1 : 0;
    if (x < 0 || z < 0 || distance(x, word(object, 0x4C)) > 3 ||
        distance(z, word(object, 0x54)) > 3 ||
        EnhancedTileHabitat(GetMetatileBehavior(field, x, z)) != gVisibleHabitatState.slots[index] ||
        MovementBlocked(field, (u8 *)object + 0x70, x, z, 0))
        return 0;
    void *player = ptr(ptr(field, 0x40), 0x30);
    if (x == (int)word(player, 0x64) && z == (int)word(player, 0x6C) &&
        distance(word(object, 0x68), word(player, 0x68)) < 2) {
        if (repel_allows_contact(field, gVisibleState.slots[index].level))
            return launch(field, index);
        ++gVisibleState.repelled_contacts;
        return 0;
    }
    if (ObjectCollision(object, x, word(object, 0x68), z))
        return 0;
    /* Native normal-walk commands update facing, interpolation and the same
     * species model animation used by the party follower. */
    SetHeldMovement(object, 12 + direction);
    ++gVisibleState.walk_commands;
    return 0;
}

int EnhancedFieldInput(void *input, void *field) {
    void *manager = ptr(field, 0x3C);
    if (manager != gVisibleState.manager) {
        forget();
        gVisibleState.manager = manager;
    }
    EnhancedFollowerUpdate(field);
    int result = OriginalFieldInput(input, field);
    if (result)
        return result;
    if ((*(u16 *)((u8 *)input + 6) & 4) && EnhancedMenuOpen(field))
        return 1;
    void *player = ptr(ptr(field, 0x40), 0x30);
    int px = word(player, 0x64), pz = word(player, 0x6C);
    u32 mode = gEnhancedOptions.visible_encounters;
    unsigned limit = mode > 3 || !EnhancedEncounterPercent() ? 0 : mode * 2;
    if (!limit) gVisibleState.tick = 0;
    int context = regular(field);
    for (int i = 0; i < 6; ++i) {
        void *object = gVisibleState.slots[i].object;
        if (owned(object) != i) {
            gVisibleState.slots[i].object = 0;
            continue;
        }
        int x = word(object, 0x64), z = word(object, 0x6C);
        int same_map = gVisibleState.slots[i].map == word(ptr(field, 0x20), 0);
        int surface_ok = !same_map || !context || compatible_surface(field, i);
        int roamer_ok = !same_map || !context || roamer_current(field, i);
        if ((unsigned)i >= limit || !context || gVisibleState.slots[i].map != word(ptr(field, 0x20), 0) ||
            distance(x, px) > 12 || distance(z, pz) > 12 || !surface_ok || !roamer_ok) {
            if (gVisibleState.slots[i].map != word(ptr(field, 0x20), 0))
                ++gVisibleState.map_releases;
            if (!surface_ok) ++gVisibleHabitatState.surface_releases;
            if (!roamer_ok) ++gVisibleRoamerState.stale;
            release_slot(i);
            continue;
        }
        int facing = word(player, 0x28);
        int dx = facing == 2 ? -1 : facing == 3 ? 1 : 0;
        int dz = facing == 0 ? -1 : facing == 1 ? 1 : 0;
        u16 held = *(u16 *)((u8 *)input + 8);
        u16 direction_key = facing == 0 ? 0x40 : facing == 1 ? 0x80 : facing == 2 ? 0x20 : 0x10;
        if ((held & direction_key) && x == px + dx && z == pz + dz &&
            distance(word(object, 0x68), word(player, 0x68)) < 2 && launch(field, i))
            return 1;
        if (gVisibleVisualState.sparkle_ticks[i])
            --gVisibleVisualState.sparkle_ticks[i];
        else
            shiny_sparkle(field, i, 0);
        if (roam(field, i))
            return 1;
    }
    u32 habitat = player_habitat(field, player);
    if (!limit || !context || !alive(field) || !habitat)
        return 0;
    if (++gVisibleState.tick < EnhancedSpawnInterval())
        return 0;
    gVisibleState.tick = 0;
    for (unsigned i = 0; i < limit; ++i)
        if (!gVisibleState.slots[i].object) {
            spawn(field, player, (int)i, habitat);
            break;
        }
    return 0;
}
