#include "events.h"
#include "settings.h"
extern void *NativeMysteryGift(void *save);
extern int NativeInsertGift(void *gifts, const void *gift, int card);
extern void NativeGiftFlagSet(void *gifts, int index);
extern void NativeCreateMon(void *, int, int, int, int, u32, int, u32);
extern void SetMonData(void *, int, const void *);
extern void NativeGiftMove(void *, u16, u8);
extern void *Heap_Alloc(int heap, u32 size);
extern void Heap_Free(void *allocation);
extern int EnhancedRepelCanUse(void *field);
extern u16 FieldSystem_VarGet(void *field, u16 var);
extern void *Save_Bag_Get(void *save);
extern const u8 *NativeSavePokewalker(void *save);
extern int Bag_HasItem(void *bag, u16 item, u16 count, int heap);
/* Mod catalogue flags: never clear or overwrite an existing received flag.
 * Existing Wonder Cards and all occupied delivery slots are preserved. */
#define FIRST_FLAG 1984
#define EVENT_SIGNATURE 0x6C35u
enum GiftKind { NORMAL, SHINY, ITEM = 3, MANAPHY_EGG = 7, COURSE = 14 };
struct Gift { u16 species_or_reward; u8 level, kind_and_moves; };
#define GIFT(species, level, kind, move_set) { species, level, ((move_set) << 4) | (kind) }
/* Move set zero keeps the original level-up moves. Other sets replace only
 * the specified slots, with PP assigned by the native move setter. */
static const u16 gift_moves[][4] = {
    {434}, {344,450,270,203}, {192,245,396,46}, {394,245,336,46},
    {329,245,403,46}, {344,231,98,85}, {57}, {19}, {404,14,334,97},
    {257,403,188,162}
};
/* Native stories retain their original progression requirements. */
static const struct Gift gifts[] = {
    GIFT(151,5,NORMAL,0), GIFT(251,50,NORMAL,0), GIFT(385,5,NORMAL,1),
    GIFT(386,50,NORMAL,0), GIFT(489,1,NORMAL,0), GIFT(490,1,MANAPHY_EGG,0),
    GIFT(491,50,NORMAL,0), GIFT(492,30,NORMAL,0), GIFT(493,100,NORMAL,0),
    GIFT(172,30,SHINY,2), GIFT(243,30,SHINY,3), GIFT(244,30,SHINY,4),
    GIFT(245,30,SHINY,5), GIFT(133,50,SHINY,0), GIFT(25,50,NORMAL,6),
    GIFT(25,10,NORMAL,7), GIFT(25,10,NORMAL,8), GIFT(212,50,NORMAL,9),
    GIFT(169,30,NORMAL,10), GIFT(486,100,NORMAL,0), GIFT(350,50,SHINY,0),
    GIFT(536,0,ITEM,0), GIFT(21,0,COURSE,0), GIFT(22,0,COURSE,0),
    GIFT(23,0,COURSE,0), GIFT(24,0,COURSE,0), GIFT(25,0,COURSE,0), GIFT(26,0,COURSE,0)
};
_Static_assert(sizeof(gifts) / sizeof(gifts[0]) == EVENT_GIFT_COUNT, "Event catalogue flags");

enum { QUEUED = 1, ALREADY_AVAILABLE, FULL, UNAVAILABLE };
extern void *NativeEventMessages(int type, int narc, int file, int heap);
extern void NativeEventMessageRead(void *data, u32 index, void *string);
extern void NativeEventMessagesFree(void *data);

void EnhancedEventName(struct Window *window, void *string, u32 index) {
    const struct Gift *gift = &gifts[index];
    u32 kind = gift->kind_and_moves & 15;
    u32 file = kind == COURSE ? 274 : kind == ITEM ? 222 : 237;
    u32 message = gift->species_or_reward + (kind == COURSE ? 91 : 0);
    void *data = NativeEventMessages(1, 27, file, 4);
    if (data) {
        NativeEventMessageRead(data, message, string);
        NativeEventMessagesFree(data);
        EnhancedDrawString(window, string, 16, 38);
    }
    const char *detail = kind == SHINY ? "Shiny" : kind == MANAPHY_EGG ? "Egg" :
        index == 14 ? "Surf" : index == 15 ? "Fly" : index == 16 ? "Volt Tackle" :
        kind == COURSE ? "PokeWalker course" : 0;
    if (detail) EnhancedDrawText(window, string, detail, 16, 60);
}

int EnhancedQueueEvent(void *field, u32 index) {
    u32 owner;
    void *save = EnhancedSettingsSaveData();
    if (!field || !save || *(void **)((u8 *)field + 12) != save ||
        !EnhancedSettingsOwner(&owner) || !EnhancedRepelCanUse(field) ||
        index >= EVENT_GIFT_COUNT) return UNAVAILABLE;
    u8 *mg = NativeMysteryGift(save);
    if (!mg) return UNAVAILABLE;
    u32 received = *(u32 *)(mg + 248) & 0x0FFFFFFFu;
    u16 signature = *(u16 *)(mg + 254) & 0x7FFFu;
    if (signature != EVENT_SIGNATURE && (signature || received)) return UNAVAILABLE;
    if (received & (1u << index)) return ALREADY_AVAILABLE;

    const struct Gift *entry = &gifts[index];
    u32 kind = entry->kind_and_moves & 15;
    u32 reward = entry->species_or_reward;
    int has_room = 0;
    for (u32 slot = 0; slot < 8; ++slot) {
        const u8 *pending = mg + 256 + 260 * slot;
        u16 tag = *(const u16 *)pending;
        if (!tag || tag >= 16) has_room = 1;
        if (tag == kind && ((kind == COURSE && pending[4] == reward) ||
            (kind == ITEM && *(const u32 *)(pending + 4) == reward))) return ALREADY_AVAILABLE;
    }
    if (kind == ITEM && (FieldSystem_VarGet(field, 0x4083) ||
        Bag_HasItem(Save_Bag_Get(save), reward, 1, 4))) return ALREADY_AVAILABLE;
    if (kind == COURSE && (*(const u32 *)(NativeSavePokewalker(save) + 0x130) &
        (1u << reward))) return ALREADY_AVAILABLE;
    if (!has_room) return FULL;
    u32 *gift = Heap_Alloc(4, 260);
    if (!gift) return UNAVAILABLE;
    for (u32 word = 0; word < 65; ++word) gift[word] = 0;
    gift[0] = kind > SHINY ? kind : 1;
    if (kind == ITEM || kind == COURSE) gift[1] = reward;
    else if (kind != MANAPHY_EGG) {
        void *mon = (u8 *)gift + 8;
        u32 high = index + 1;
        u32 low = owner ^ (owner >> 16) ^ high ^ (kind == SHINY ? 0 : 16);
        u32 pid = (high << 16) | (low & 65535u);
        NativeCreateMon(mon, reward, entry->level, 32, 1, pid, 1, owner);
        u32 value = 1;
        SetMonData(mon, 110, &value);
        value = 16; /* Cherish Ball */
        SetMonData(mon, 155, &value);
        u32 move_set = entry->kind_and_moves >> 4;
        if (move_set) {
            const u16 *moves = gift_moves[move_set - 1];
            for (u32 slot = 0; slot < 4 && moves[slot]; ++slot) NativeGiftMove(mon, moves[slot], slot);
        }
    }
    int inserted = NativeInsertGift(mg, gift, 3);
    Heap_Free(gift);
    if (!inserted) return UNAVAILABLE;
    /* The native flag setter below updates this save chunk's CRC. */
    *(u16 *)(mg + 254) = EVENT_SIGNATURE | 0x8000u;
    NativeGiftFlagSet(mg, FIRST_FLAG + index);
    return QUEUED;
}
