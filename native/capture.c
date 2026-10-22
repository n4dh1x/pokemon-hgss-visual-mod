#include "config.h"

extern void NativeCaptureTask(void *task, void *data);
extern void NativeExperienceTask(void *task, void *data);
extern int NativeCalcExperience(void *battle, void *ctx);
extern u32 BattleSystem_GetBattleType(void *battle);
extern void *BattleSystem_GetParty(void *battle, int battler);
extern void *Heap_Alloc(int heap, u32 bytes);
extern void Heap_Free(void *memory);
extern void *SysTask_CreateOnMainQueue(void (*callback)(void *, void *), void *data, u32 priority);
extern int NativeBallAnimationActive(void *ball, int animation);
extern int Party_GetCount(void *party);
extern void *Party_GetMonByIndex(void *party, int slot);
extern u32 GetMonData(void *mon, int field, void *destination);

struct CaptureExperienceState {
    void *parent, *ctx;
    u32 phase, completed_once, fainted, gained, shared, earn[2];
    u32 started, completed, failures, skipped, last_enemy;
};
struct CaptureExperienceState gCaptureExperience;
_Static_assert(sizeof(struct CaptureExperienceState) == 56, "Capture EXP diagnostic ABI");
static u32 word(void *p, unsigned n) { return *(u32 *)((u8 *)p + n); }
static void *ptr(void *p, unsigned n) { return *(void **)((u8 *)p + n); }
static void put(void *p, unsigned n, u32 v) { *(u32 *)((u8 *)p + n) = v; }

static void restore_context(void) {
    void *ctx = gCaptureExperience.ctx;
    *(void **)((u8 *)ctx + 0x178) = gCaptureExperience.parent;
    put(ctx, 0x74, gCaptureExperience.fainted);
    put(ctx, 0x9C, gCaptureExperience.gained);
    put(ctx, 0xA0, gCaptureExperience.shared);
    put(ctx, 0xA4, gCaptureExperience.earn[0]);
    put(ctx, 0xA8, gCaptureExperience.earn[1]);
}
void EnhancedCaptureExperienceChild(void *task, void *data) {
    /* This is a real separate native task and allocation. The native completion
     * path owns their destruction; never let it destroy the capture parent. */
    NativeExperienceTask(task, data);
    if (!ptr(gCaptureExperience.ctx, 0x178)) {
        restore_context();
        gCaptureExperience.phase = 2;
        ++gCaptureExperience.completed;
    }
}
static int eligible(void *battle, void *ctx, u32 enemy) {
    /* Normal wild/double/roamer only. Exclude tutorial and all special formats. */
    if (!gEnhancedOptions.capture_exp || (BattleSystem_GetBattleType(battle) & ~0x102u)) return 0;
    void *party = BattleSystem_GetParty(battle, 0);
    int count = Party_GetCount(party);
    if (count < 1 || count > 6) return 0;
    u32 mask = word(ctx, 0xA4 + ((enemy >> 1) & 1) * 4);
    for (int i = 0; i < count; ++i) {
        void *mon = Party_GetMonByIndex(party, i);
        if ((mask & (1u << i)) && GetMonData(mon, 5, 0) &&
            !GetMonData(mon, 76, 0) && GetMonData(mon, 163, 0)) return 1;
    }
    /* Avoid native EXP division by zero if no live participant remains. */
    return 0;
}
void EnhancedCaptureTask(void *task, void *data) {
    u32 state = word(data, 0x28);
    if (!state) {
        gCaptureExperience.parent = data;
        gCaptureExperience.ctx = ptr(data, 4);
        gCaptureExperience.phase = gCaptureExperience.completed_once = 0;
    }
    if (gCaptureExperience.parent == data && gCaptureExperience.phase == 1) return;
    /* Same point as native CHECK_MON_DATA: catch confirmed, text finished,
     * fade animation complete, final delay tick, before Dex/nickname/storage. */
    if (state == 10 && word(data, 0x34) == 1 &&
        !gCaptureExperience.completed_once && !NativeBallAnimationActive(ptr(data, 8), 7)) {
        void *battle = ptr(data, 0), *ctx = ptr(data, 4);
        u32 enemy = (((u8 *)ctx)[0x3108] & 2) ? 3 : 1;
        gCaptureExperience.parent = data;
        gCaptureExperience.ctx = ctx;
        gCaptureExperience.completed_once = 1;
        gCaptureExperience.last_enemy = enemy;
        if (eligible(battle, ctx, enemy)) {
            u32 *work = Heap_Alloc(5, 0x58);
            if (work) {
                for (int i = 0; i < 22; ++i) work[i] = 0;
                work[0] = (u32)battle; work[1] = (u32)ctx;
                gCaptureExperience.fainted = word(ctx, 0x74);
                gCaptureExperience.gained = word(ctx, 0x9C);
                gCaptureExperience.shared = word(ctx, 0xA0);
                gCaptureExperience.earn[0] = word(ctx, 0xA4);
                gCaptureExperience.earn[1] = word(ctx, 0xA8);
                put(ctx, 0x74, enemy);
                u32 script = word(ctx, 0xB4);
                put(ctx, 0xB4, 0);
                NativeCalcExperience(battle, ctx);
                put(ctx, 0xB4, script);
                *(void **)((u8 *)ctx + 0x178) = work;
                if (SysTask_CreateOnMainQueue(EnhancedCaptureExperienceChild, work, 0)) {
                    gCaptureExperience.phase = 1;
                    ++gCaptureExperience.started;
                    return;
                }
                restore_context();
                Heap_Free(work);
            }
            ++gCaptureExperience.failures;
        } else ++gCaptureExperience.skipped;
    }
    NativeCaptureTask(task, data);
}
