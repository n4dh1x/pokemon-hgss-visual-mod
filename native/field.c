#include "config.h"

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

extern int OriginalFieldInput(void *input, void *field);
extern void OriginalFieldControl(void *field);
extern int FieldMovementAllowed(void *field);
extern int OriginalStepEncounter(void *field);
extern int OriginalEncounterRoll(void *field, u8 rate, u8 tile);
extern int OriginalRoamerCheck(void *field, void **roamer);
extern void OriginalStartEncounter(void *field, void *setup);
extern void OriginalStartScript(void *field, u16 script, void *object);
extern int OriginalObjectIterator(void *manager, void **object, int *index, u32 mask);
extern void Heap_FreeExplicit(int heap, void *memory);
extern void *SaveArray_Party_Get(void *save);
extern int Party_GetCount(void *party);
extern void *Party_GetMonByIndex(void *party, int index);
extern u32 GetMonData(void *mon, int field, void *destination);
extern int MonIsShiny(void *mon);
extern int MapHeader_HasWildEncounters(u32 map);
extern void *Save_VarsFlags_Get(void *save);
extern int CheckPartner(void *flags);
extern int CheckSafari(void *flags);
extern int CheckContest(void *flags);
extern int CheckPalPark(void *flags);
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
};
/* Counters aid emulator verification. They are session-only, not save data. */
struct VisibleState gVisibleState;
_Static_assert(sizeof(struct VisibleSlot) == 260, "Visible slot diagnostic ABI");
_Static_assert(sizeof(struct VisibleState) == 1632, "Visible state diagnostic ABI");

static int owned(void *object) {
    if (!object || !gVisibleState.manager || !(word(object, 0) & 1) ||
        ptr(object, 0xB4) != gVisibleState.manager)
        return -1;
    for (int i = 0; i < 6; ++i)
        if (gVisibleState.slots[i].object == object &&
            word(object, 8) == gVisibleState.slots[i].id)
            return i;
    return -1;
}

static void forget(void) {
    for (int i = 0; i < 6; ++i)
        gVisibleState.slots[i].object = 0;
    gVisibleState.manager = 0;
    gVisibleState.tick = 0;
    gVisibleState.paused_mask = 0;
    for (int i = 0; i < 6; ++i)
        gVisibleState.roam_delay[i] = 0;
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
    pause_wilds(!FieldMovementAllowed(field));
    OriginalFieldControl(field);
    pause_wilds(!FieldMovementAllowed(field));
}

void EnhancedManagerDelete(void *manager) {
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

int EnhancedEncounterRoll(void *field, u8 rate, u8 tile) {
    return gVisibleState.capture ? 1 : OriginalEncounterRoll(field, rate, tile);
}
int EnhancedRoamerCheck(void *field, void **roamer) {
    return gVisibleState.capture ? 0 : OriginalRoamerCheck(field, roamer);
}
void EnhancedCaptureEncounter(void *field, void *setup) {
    if (gVisibleState.capture)
        gVisibleState.captured = setup;
    else if (gVisibleState.suppress_ordinary) {
        /* The roamer branch calls the original battle launcher separately.
         * Discard only an ordinary step-generated enemy in Many mode. */
        BattleSetup_Delete(setup);
        gVisibleState.discarded_ordinary = 1;
    }
    else
        OriginalStartEncounter(field, setup);
}
int EnhancedStepEncounter(void *field) {
    void *player = ptr(ptr(field, 0x40), 0x30);
    if (gEnhancedOptions.visible_encounters == 3 && regular(field) && alive(field) &&
        grass(GetMetatileBehavior(field, word(player, 0x64), word(player, 0x6C))))
    {
        gVisibleState.suppress_ordinary = 1;
        gVisibleState.discarded_ordinary = 0;
        int result = OriginalStepEncounter(field);
        gVisibleState.suppress_ordinary = 0;
        return gVisibleState.discarded_ordinary ? 0 : result;
    }
    return OriginalStepEncounter(field);
}

static void release_slot(int index) {
    void *object = gVisibleState.slots[index].object;
    if (owned(object) == index)
        MapObject_Remove(object);
    gVisibleState.slots[index].object = 0;
    gVisibleState.roam_delay[index] = 0;
    gVisibleState.paused_mask &= ~(1u << index);
}

static int launch(void *field, int index) {
    if (!alive(field) || owned(gVisibleState.slots[index].object) != index)
        return 0;
    void *setup = BattleSetup_New(11, 0);
    if (!setup)
        return 0;
    BattleSetup_InitFromFieldSystem(setup, field);
    BattleSetup_AddMonToParty(setup, gVisibleState.slots[index].mon, 1);
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

static int generate(void *field, struct VisibleSlot *slot) {
    /* The native generator uses current HGSS tables/abilities/Repel and rolls
     * PID/IVs/form once. Capture its successful battle setup, copy its Pokemon,
     * then free all setup allocations; player data is refreshed at contact. */
    u32 counters = word(field, 0x7C);
    u16 facing = *(u16 *)((u8 *)field + 0x7A);
    *(u16 *)((u8 *)field + 0x7E) = 4;
    gVisibleState.captured = 0;
    gVisibleState.capture = 1;
    OriginalStepEncounter(field);
    gVisibleState.capture = 0;
    put(field, 0x7C, counters);
    *(u16 *)((u8 *)field + 0x7A) = facing;
    void *setup = gVisibleState.captured;
    gVisibleState.captured = 0;
    if (!setup)
        return 0;
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
    BattleSetup_Delete(setup);
    return valid;
}

static void spawn(void *field, void *player, int index) {
    int px = word(player, 0x64), pz = word(player, 0x6C);
    int x = px, z = pz, found = 0;
    for (int attempt = 0; attempt < 24; ++attempt) {
        u32 random = LCRandom();
        x = px + (int)(random & 7) - 3;
        z = pz + (int)((random >> 3) & 7) - 3;
        if (distance(x, px) + distance(z, pz) < 2 || x < 0 || z < 0)
            continue;
        if (!grass(GetMetatileBehavior(field, x, z)) || TerrainBlocked(field, x, z) ||
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
    if (!generate(field, slot))
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
    event.parameter[0] = event.parameter[1] = event.parameter[2] = 0;
    event.range_x = event.range_z = 0;
    event.x = (u16)x;
    event.z = (u16)z;
    event.y = 0;
    slot->map = word(ptr(field, 0x20), 0);
    void *object = CreateObject(manager, &event, slot->map);
    if (!object) {
        ++gVisibleState.failures;
        return;
    }
    FollowMon_SetObjectParams(object, slot->species, (u8)form, MonIsShiny(slot->mon));
    put(object, 0, (word(object, 0) | (1u << 13) | (1u << 10) | (1u << 29)) & ~0x180u);
    SetPokemonHidden(object, 0);
    slot->object = object;
    slot->id = id;
    ++gVisibleState.generated;
    gVisibleState.roam_delay[index] = 45 + (LCRandom() & 63);
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
        distance(z, word(object, 0x54)) > 3 || !grass(GetMetatileBehavior(field, x, z)) ||
        MovementBlocked(field, (u8 *)object + 0x70, x, z, 0))
        return 0;
    void *player = ptr(ptr(field, 0x40), 0x30);
    if (x == (int)word(player, 0x64) && z == (int)word(player, 0x6C) &&
        distance(word(object, 0x68), word(player, 0x68)) < 2)
        return launch(field, index);
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
    int result = OriginalFieldInput(input, field);
    if (result)
        return result;
    void *player = ptr(ptr(field, 0x40), 0x30);
    int px = word(player, 0x64), pz = word(player, 0x6C);
    u32 mode = gEnhancedOptions.visible_encounters;
    unsigned limit = mode > 3 ? 0 : mode * 2;
    for (int i = 0; i < 6; ++i) {
        void *object = gVisibleState.slots[i].object;
        if (owned(object) != i) {
            gVisibleState.slots[i].object = 0;
            continue;
        }
        int x = word(object, 0x64), z = word(object, 0x6C);
        if ((unsigned)i >= limit || distance(x, px) > 12 || distance(z, pz) > 12) {
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
        if (roam(field, i))
            return 1;
    }
    if (!limit || !regular(field) || !alive(field) ||
        !grass(GetMetatileBehavior(field, px, pz)))
        return 0;
    if (++gVisibleState.tick < 60)
        return 0;
    gVisibleState.tick = 0;
    for (unsigned i = 0; i < limit; ++i)
        if (!gVisibleState.slots[i].object) {
            spawn(field, player, (int)i);
            break;
        }
    return 0;
}
