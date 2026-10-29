#include "settings.h"
#include "items.h"
extern const u8 gItemPocketTable[269];
extern void NativeItemName(void *string, u16 item, int heap);
extern void *Save_Bag_Get(void *save);
extern int Bag_HasItem(void *, u16, u16, int);
extern int NativeBagSpace(void *, u16, u16, int);
extern int NativeBagAdd(void *, u16, u16, int);
extern int EnhancedRepelCanUse(void *field);
extern void PlaySE(u16 sequence);
extern u8 AddTextPrinterParameterizedWithColor(struct Window *, int, void *, u32, u32, u32, u32, void *);
/* Native String ABI, also used by the original item-name message reader. */
struct ItemString { u16 capacity, size; u32 magic; u16 text[]; };
struct ItemUi { u32 row, result, gives, denied, last_item, last_quantity, ready; };
struct ItemUi gItemUi;
_Static_assert(sizeof(struct ItemUi) == 28, "Item giver diagnostic ABI");
static const u8 quantities[5] = {1,5,10,50,99};
int EnhancedItemValid(u32 item, u32 pocket, void *string) {
    if (!item || item > 536 || pocket > 7 ||
        ((gItemPocketTable[item >> 1] >> ((item & 1)*4)) & 15) != pocket) return 0;
    NativeItemName(string, item, 4);
    struct ItemString *name = string;
    return name->size && name->text[0] != 428 && name->text[0] != 0xFFFF;
}
void EnhancedItemStep(struct EnhancedExtraOptions *e, int direction, void *string) {
    u32 item = e->give_item;
    for (u32 tries = 0; tries < 536; ++tries) {
        item = direction < 0 ? (item <= 1 ? 536 : item - 1) : (item >= 536 ? 1 : item + 1);
        if (EnhancedItemValid(item, e->give_pocket, string)) { e->give_item = item; return; }
    }
    e->give_item = 0;
}
int EnhancedGiveItem(void *field, const struct EnhancedExtraOptions *e, void *string) {
    u32 owner; void *save = EnhancedSettingsSaveData();
    int result = 2;
    if (field && save && *(void **)((u8 *)field+12) == save &&
        EnhancedSettingsOwner(&owner) && EnhancedRepelCanUse(field)) {
        result = 5;
        if (e->give_count <= 4 && EnhancedItemValid(e->give_item,e->give_pocket,string)) {
            void *bag = Save_Bag_Get(save);
            u16 quantity = e->give_pocket == 7 ? 1 : quantities[e->give_count];
            if (e->give_pocket == 7 && Bag_HasItem(bag,e->give_item,1,4)) result = 3;
            else if (NativeBagSpace(bag,e->give_item,quantity,4) && NativeBagAdd(bag,e->give_item,quantity,4)) {
                result = 1; ++gItemUi.gives;
                gItemUi.last_item = e->give_item; gItemUi.last_quantity = quantity;
            } else result = 4;
        }
    }
    if (result != 1) ++gItemUi.denied;
    PlaySE(result == 1 ? 1521 : 1645);
    return result;
}
void EnhancedItemUiReset(void) { gItemUi.row = gItemUi.result = gItemUi.ready = 0; }
static void draw(struct Window *w, void *str, struct EnhancedExtraOptions *e) {
    static const char *const pockets[8] = {"Items","Medicine","Poke Balls","TMs and HMs","Berries","Mail","Battle items","Key items"};
    static const char *const counts[5] = {"1","5","10","50","99"};
    static const char *const messages[6] = {"Native Save keeps items","Item added. Save to keep.","Bag unavailable here","Key item already owned","No room for that amount","No valid item selected"};
    static const u8 ys[5] = {28,60,92,116,140};
    FillWindowPixelBuffer(w,15);
    EnhancedDrawText(w,str,"ITEM GIVER",8,2);
    EnhancedDrawText(w,str,"Pocket",16,28);
    EnhancedDrawText(w,str,pockets[e->give_pocket],96,28);
    EnhancedDrawText(w,str,"Item",16,60);
    if (e->give_item) {
        NativeItemName(str,e->give_item,4);
        AddTextPrinterParameterizedWithColor(w,0,str,80,60,0xFF,0x01020F,0);
    }
    EnhancedDrawText(w,str,"Quantity",16,92);
    EnhancedDrawText(w,str,counts[e->give_pocket == 7 ? 0 : e->give_count],172,92);
    EnhancedDrawText(w,str,"Give item",16,116);
    EnhancedDrawText(w,str,"Back",16,140);
    EnhancedDrawText(w,str,"-",2,ys[gItemUi.row]);
    EnhancedDrawText(w,str,messages[gItemUi.result],8,158);
    CopyWindowToVram(w);
}
int EnhancedItemUi(void *field, struct Window *w, void *string,
        struct EnhancedExtraOptions *e, u32 keys) {
    if (keys & 2) return 1;
    if (!(keys & 0xF3) && gItemUi.ready) return 0;
    if (keys & 0x40) gItemUi.row = gItemUi.row ? gItemUi.row-1 : 4;
    if (keys & 0x80) gItemUi.row = gItemUi.row == 4 ? 0 : gItemUi.row+1;
    if (keys & 0x31) {
        u32 row = gItemUi.row; int direction = keys & 0x20 ? -1 : 1;
        gItemUi.result = 0;
        if (!row) { e->give_pocket = (e->give_pocket + (direction < 0 ? 7 : 1)) & 7; e->give_item = 0; }
        else if (row == 1) EnhancedItemStep(e,direction,string);
        else if (row == 2 && e->give_pocket != 7) {
            u32 next = e->give_count + (direction < 0 ? 4 : 1);
            e->give_count = next >= 5 ? next-5 : next;
        }
        else if ((keys & 1) && row == 3) gItemUi.result = EnhancedGiveItem(field,e,string);
        else if ((keys & 1) && row == 4) return 1;
    }
    if (!EnhancedItemValid(e->give_item,e->give_pocket,string)) EnhancedItemStep(e,1,string);
    draw(w,string,e); gItemUi.ready = 1;
    return 0;
}
