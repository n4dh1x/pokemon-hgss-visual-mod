#include "quick_ball.h"
#include "ui.h"
extern const u8 gItemPocketTable[269];
extern void *NativeSavePC(void *save);
extern int Bag_TakeItem(void *bag, u16 item, u16 quantity, int heap);
extern int Party_GetCount(void *party);
extern u32 BattleSystem_GetBattleType(void *battle);
extern u32 NativeBattleSpecial(void *battle);
extern u32 NativeMaxBattlers(void *battle);
extern u32 NativeBattleOutcome(void *battle);
extern int NativeQuickCursor(void *input);
extern int NativeQuickTouchRect(const void *rectangles);
extern int NativePCFirstEmpty(void *storage);
extern void NativeQuickBag(void *battle, void *ctx, u32 battler);
extern void NativeBattleBufferClear(void *ctx, u32 battler);
extern void NativeSelectedBagItem(void *battle, u32 battler, u32 item);
extern void *String_New(u32 capacity, int heap);
extern void String_Delete(void *string);
extern void NativeItemName(void *string, u16 item, int heap);
extern void NativeQuickText(void *input, void *object, void *string, int font,
    u32 color, int palette, int resource, int x, int y, int center, void *display);
extern void NativeFontDelete(void *font);
extern void NativeCharFree(void *allocation);
extern void PlaySE(u16 sequence);
extern u32 EnhancedUnsignedDivide(u32 value,u32 divisor);
#define LAST_PRESENT 2097152u
struct QuickState {
    void *battle, *ctx, *input;
    u32 owner, selected, queued, last, saved, dirty, committing;
    u32 storage_frame, storage_full, storage_ready, ui_ball, ui_quantity;
    void *text[4];
    u32 requests, denied, throws, cycles, saves, save_failures;
};
struct QuickState gQuickBall;
_Static_assert(sizeof(struct QuickState)==100,"Quick-ball diagnostic ABI");
static u32 word(void *p, u32 at) { return *(u32 *)((u8 *)p+at); }
static void *ptr(void *p, u32 at) { return *(void **)((u8 *)p+at); }
static u32 frame(void) { return *(volatile u32 *)0x021D1138; }
static int ball(u32 item) {
    /* All named HGSS balls with native battle-use function 1; Park Ball is
     * battle-use 0. The original item resource is independently fingerprinted. */
    return item && item < 500 && ((gItemPocketTable[item>>1] >> ((item&1)*4))&15) == 2;
}
static u16 *slots(void) { return (u16 *)((u8 *)ptr(gQuickBall.battle,0x58)+1728); }
static u32 quantity(u32 item) {
    u16 *s=slots(); u32 total=0;
    for (u32 i=0;i<24;++i) if (s[i*2]==item) total+=s[i*2+1];
    return total;
}
void EnhancedQuickRestore(const struct EnhancedJournal *r, u32 owner) {
    u32 *p=(u32 *)&gQuickBall;
    for (u32 i=0;i<sizeof(gQuickBall)/4;++i) p[i]=0;
    gQuickBall.owner=owner;
    if (r && (r->reserved[0]&LAST_PRESENT) && ball(r->values[28]))
        gQuickBall.last=gQuickBall.saved=r->values[28];
}
void EnhancedQuickSnapshot(struct EnhancedJournal *r) {
    u32 last=gQuickBall.committing ? gQuickBall.last : gQuickBall.saved;
    if (last || (r->reserved[0]&LAST_PRESENT)) {
        r->values[28]=last; r->reserved[0]|=LAST_PRESENT;
    }
}
int EnhancedQuickNeedsSave(void *save) {
    u32 owner;
    return gQuickBall.dirty && save==EnhancedSettingsSaveData() &&
        EnhancedSettingsOwner(&owner) && owner==gQuickBall.owner;
}
void EnhancedQuickSaving(void *save) { gQuickBall.committing=EnhancedQuickNeedsSave(save); }
void EnhancedQuickSaved(int success) {
    if (gQuickBall.committing) {
        if (success) {gQuickBall.saved=gQuickBall.last;gQuickBall.dirty=0;++gQuickBall.saves;}
        else ++gQuickBall.save_failures;
    }
    gQuickBall.committing=0;
}
void EnhancedQuickBegin(void *battle, void *ctx) {
    gQuickBall.battle=battle;gQuickBall.ctx=ctx;gQuickBall.input=0;
    gQuickBall.queued=gQuickBall.storage_ready=0;
    for (u32 i=0;i<4;++i) gQuickBall.text[i]=0;
}
static int eligible(void *battle, int refresh) {
    u32 owner; void *ctx=gQuickBall.ctx, *save=EnhancedSettingsSaveData();
    if (!battle || battle!=gQuickBall.battle || !ctx || !save ||
        !EnhancedSettingsOwner(&owner) || owner!=gQuickBall.owner ||
        ptr(battle,0x30)!=ctx || !ptr(battle,0x58) || ptr(battle,0x64)!=NativeSavePC(save) ||
        (BattleSystem_GetBattleType(battle)&~0x100u) ||
        (NativeBattleSpecial(battle)&0x30) || NativeMaxBattlers(battle)!=2 || NativeBattleOutcome(battle) ||
        word(ctx,8)!=5 || !word(ctx,0x2D8C) || !word(ctx,0x2E4C) ||
        (word(ctx,0x2E80)&0x200400C0u) || (word(ctx,0x2E70)&0x01000000u)) return 0;
    u32 now=frame();
    if (refresh || !gQuickBall.storage_ready || now-gQuickBall.storage_frame>=60) {
        gQuickBall.storage_full=Party_GetCount(ptr(battle,0x68))==6 && NativePCFirstEmpty(ptr(battle,0x64))==18;
        gQuickBall.storage_frame=now;gQuickBall.storage_ready=1;
    }
    return !gQuickBall.storage_full;
}
u32 EnhancedQuickBallItem(void *battle) {
    if (!eligible(battle,0)) return 0;
    if (ball(gQuickBall.selected) && quantity(gQuickBall.selected)) return gQuickBall.selected;
    gQuickBall.selected=0;
    if (ball(gQuickBall.last) && quantity(gQuickBall.last)) return gQuickBall.last;
    u16 *s=slots();
    for (u32 i=0;i<24;++i) if (ball(s[i*2]) && s[i*2+1]) return s[i*2];
    return 0;
}
int EnhancedQuickCycle(void *battle, int direction) {
    u32 current=EnhancedQuickBallItem(battle), index=24;
    if (!current || !direction) return 0;
    u16 *s=slots();
    for (u32 i=0;i<24;++i) if (s[i*2]==current) {index=i;break;}
    if (index==24) return 0;
    for (u32 step=1;step<24;++step) {
        index=direction<0 ? (index ? index-1 : 23) : (index==23 ? 0 : index+1);
        u32 item=s[index*2];
        if (!ball(item) || !s[index*2+1]) continue;
        u32 first=0;while (first<index && s[first*2]!=item) ++first;
        if (first!=index || item==current) continue;
        gQuickBall.selected=item;++gQuickBall.cycles;return 1;
    }
    return 0;
}
static void *object(void *input,u32 index) {return (u8 *)input+0x4D0+(index+4)*20;}
static void erase(void *input) {
    for (u32 i=0;i<4;++i) {
        void *o=object(input,i);
        if (gQuickBall.text[i] && ptr(o,0)==gQuickBall.text[i]) {
            NativeFontDelete(ptr(o,0));NativeCharFree((u8 *)o+4);*(void **)o=0;
        }
        gQuickBall.text[i]=0;
    }
}
static void draw(void *input,u32 item) {
    if (gQuickBall.input!=input) {
        gQuickBall.input=input;for (u32 i=0;i<4;++i) gQuickBall.text[i]=0;
        gQuickBall.ui_ball=0;
    }
    u32 count=item ? quantity(item) : 0;
    if (item && item==gQuickBall.ui_ball && count==gQuickBall.ui_quantity) {
        u32 complete=1;
        for (u32 i=0;i<4;++i) if (!gQuickBall.text[i] || ptr(object(input,i),0)!=gQuickBall.text[i]) complete=0;
        if (complete) return;
    }
    erase(input);gQuickBall.ui_ball=item;gQuickBall.ui_quantity=count;
    if (!item) return;
    for (u32 i=0;i<4;++i) if (ptr(object(input,i),0)) return;
    void *string=String_New(64,5);
    if (!string) return;
    NativeItemName(string,item,5);
    struct Name {u16 capacity,size;u32 magic;u16 text[64];} *name=string;
    if (name->size<56) {
        name->text[name->size++]=478;name->text[name->size++]=348;
        u16 digits[10];u32 length=0;
        do {
            u32 next=EnhancedUnsignedDivide(count,10);
            digits[length++]=289+count-next*10;count=next;
        } while(count && length<10);
        while(length) name->text[name->size++]=digits[--length];
        name->text[name->size]=0xFFFF;
    }
    NativeQuickText(input,object(input,0),string,0,0x010200,2,20023,128,34,1,0);
    gQuickBall.text[0]=ptr(object(input,0),0);
    static const char *const labels[3]={"R throw  L/Y cycle","Prev","Next"};
    static const u8 x[3]={192,32,224}, y[3]={16,34,34};
    for (u32 i=0;i<3;++i) {
        EnhancedCopyText(string,labels[i]);
        NativeQuickText(input,object(input,i+1),string,0,0x010200,2,20023,x[i],y[i],1,0);
        gQuickBall.text[i+1]=ptr(object(input,i+1),0);
    }
    String_Delete(string);
}
int EnhancedQuickTouchRect(const void *rectangles) {
    /* The original FIGHT hitbox extends above its visible button. Reserve
     * only the displayed quick-ball strip, then let the original CheckTouch
     * call our cursor helper and run its normal feedback/cleanup callback. */
    void *input=gQuickBall.input;
    u16 *touch=(u16 *)0x021D116C;
    if (input && gQuickBall.text[0] && ptr(object(input,0),0)==gQuickBall.text[0] &&
        (*(signed char *)((u8 *)input+0x68B)>=1 && *(signed char *)((u8 *)input+0x68B)<=4) &&
        touch[2] && touch[1]>=24 && touch[1]<40 && touch[0]>=8 && touch[0]<248) return -1;
    return NativeQuickTouchRect(rectangles);
}
int EnhancedQuickCursor(void *input) {
    int menu=*(signed char *)((u8 *)input+0x68B);
    if (menu<1 || menu>4) return NativeQuickCursor(input);
    void *battle=ptr(input,0);u32 item=EnhancedQuickBallItem(battle);
    draw(input,item);
    u32 keys=*(volatile u32 *)0x021D1148;
    u16 *touch=(u16 *)0x021D116C;
    int area=touch[2] && touch[1]>=24 && touch[1]<40 && touch[0]>=8 && touch[0]<248;
    if ((keys&0x100) || (area && touch[0]>=56 && touch[0]<200)) {
        ++gQuickBall.requests;
        if (item) {gQuickBall.queued=item;erase(input);return 1;}
        ++gQuickBall.denied;PlaySE(1645);return -1;
    }
    int direction=0;
    if ((keys&0x200) || (area && touch[0]>=200)) direction=1;
    else if ((keys&0x800) || (area && touch[0]<56)) direction=-1;
    if (direction) {
        PlaySE(EnhancedQuickCycle(battle,direction) ? 1500 : 1645);
        draw(input,EnhancedQuickBallItem(battle));return -1;
    }
    return NativeQuickCursor(input);
}
void EnhancedQuickShowBag(void *battle,void *ctx,u32 battler) {
    u32 item=gQuickBall.queued;gQuickBall.queued=0;
    if (item && !battler && ctx==gQuickBall.ctx && eligible(battle,1) && ball(item) && quantity(item)) {
        NativeBattleBufferClear(ctx,battler);
        NativeSelectedBagItem(battle,battler,item|(2u<<16));return;
    }
    NativeQuickBag(battle,ctx,battler);
}
int EnhancedQuickTakeBall(void *bag,u16 item,u16 count,int heap) {
    int result=Bag_TakeItem(bag,item,count,heap);
    u32 owner;
    if (result && count==1 && ball(item) && gQuickBall.battle &&
        bag==ptr(gQuickBall.battle,0x58) && EnhancedSettingsOwner(&owner) && owner==gQuickBall.owner) {
        gQuickBall.selected=0;gQuickBall.last=item;gQuickBall.dirty=item!=gQuickBall.saved;++gQuickBall.throws;
    }
    return result;
}
