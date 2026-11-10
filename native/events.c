#include "events.h"
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
_Static_assert(sizeof(gifts) / sizeof(gifts[0]) == 28, "Event catalogue flags");
struct EventState {void *save;u32 owner,frame,queued,denied;};
struct EventState gEventState;
static int flag(const u8 *mg,u32 index) {return !!(mg[index>>3]&(1u<<(index&7)));}
static void *owned(void *field,u32 *owner) {
 void *save=EnhancedSettingsSaveData();
 return field && save && *(void **)((u8 *)field+12)==save &&
  EnhancedSettingsOwner(owner) ? save : 0;
}
void EnhancedEventsTick(void *field) {
 u32 owner,now=*(volatile u32 *)0x021D1138;
 void *save=owned(field,&owner);
 if (!save || *(void **)((u8 *)field+0x10)) return;
 if (gEventState.save==save && gEventState.owner==owner && now-gEventState.frame<60) return;
 gEventState.save=save;gEventState.owner=owner;gEventState.frame=now;
 u8 *mg=NativeMysteryGift(save);
 if (!mg || (*(u16 *)(mg+254)&0x7FFFu)!=EVENT_SIGNATURE || !EnhancedRepelCanUse(field)) return;
 u32 i=0;
 while(i<sizeof(gifts)/sizeof(gifts[0]) && flag(mg,FIRST_FLAG+i)) ++i;
 if(i==sizeof(gifts)/sizeof(gifts[0])) return;
 /* Do not allocate or touch existing gifts when all native slots are busy. */
 u32 empty = 0, stone_queued = 0;
 for (u32 slot = 0; slot < 8; ++slot) {
     u8 *entry = mg + 256 + 260 * slot;
     u16 tag = *(u16 *)entry;
     if (!tag || tag >= 16) ++empty;
     if (tag == ITEM && *(u32 *)(entry + 4) == 536) stone_queued = 1;
 }
 if(!empty) return;
 u32 *gift=Heap_Alloc(4,260);
 if(!gift) {++gEventState.denied;return;}
 for(;i<sizeof(gifts)/sizeof(gifts[0]) && empty;++i) {
  if(flag(mg,FIRST_FLAG+i)) continue;
  const struct Gift *g=&gifts[i];
  for(u32 j=0;j<65;++j) gift[j]=0;
  u32 kind = g->kind_and_moves & 15;
  /* A second stone delivery would reinitialize its native event variable. */
  if (kind == ITEM && (stone_queued || FieldSystem_VarGet(field, 0x4083) ||
      Bag_HasItem(Save_Bag_Get(save), 536, 1, 4))) {
      NativeGiftFlagSet(mg, FIRST_FLAG + i);
      continue;
  }
  gift[0] = kind > SHINY ? kind : 1;
  if (kind == ITEM || kind == COURSE) gift[1] = g->species_or_reward;
  else if (kind != MANAPHY_EGG) {
   void *mon=(u8 *)gift+8;
   /* Distinct PIDs also distinguish the three Pikachu gifts in save managers. */
   u32 high = i + 1;
   u32 low = owner ^ (owner >> 16) ^ high ^ (kind == SHINY ? 0 : 16);
   u32 pid = (high << 16) | (low & 65535u);
   NativeCreateMon(mon,g->species_or_reward,g->level,32,1,pid,1,owner);
   u32 value=1;SetMonData(mon,110,&value);
   value=16;SetMonData(mon,155,&value); /* native Cherish Ball */
   u32 move_set = g->kind_and_moves >> 4;
   if (move_set) {
       const u16 *moves = gift_moves[move_set - 1];
       for (u32 slot = 0; slot < 4 && moves[slot]; ++slot) NativeGiftMove(mon, moves[slot], slot);
   }
  }
  if(!NativeInsertGift(mg,gift,3)) {++gEventState.denied;break;}
  NativeGiftFlagSet(mg,FIRST_FLAG+i);++gEventState.queued;--empty;
 }
 Heap_Free(gift);
}
int EnhancedEventsEnable(void *field) {
 u32 owner;void *save=owned(field,&owner);
 if(!save || !EnhancedRepelCanUse(field)) return 0;
 u8 *mg=NativeMysteryGift(save);
 if (!mg) return 0;
 u16 signature=*(u16 *)(mg+254)&0x7FFFu;
 if(signature!=EVENT_SIGNATURE) {
  /* Refuse a foreign use of this mod namespace rather than reinterpret or
   * clear another distribution's received flags. */
  if(signature || (*(u32 *)(mg+248)&0x0FFFFFFFu)) return 0;
  for(u32 i=0;i<15;++i) if(EVENT_SIGNATURE&(1u<<i)) NativeGiftFlagSet(mg,2032+i);
 }
 NativeGiftFlagSet(mg,2047); /* original Mystery Gift menu unlock */
 gEventState.save=0; /* fill after menu closes; never create a second field task */
 return 1;
}
