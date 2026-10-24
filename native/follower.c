#include "settings.h"

extern void *NativeFollowerField(void *manager);
extern int NativeFollowerPermission(int species, u32 map);
extern void NativeFollowerRefresh(void *field);
extern int FieldMovementAllowed(void *field);
extern void *SaveArray_Party_Get(void *save);
extern int NativePartyAlive(void *party);

struct FollowerState {
    void *field, *manager;
    u32 known, hidden, removed, restored, blocked;
};
struct FollowerState gFollowerState;
_Static_assert(sizeof(struct FollowerState) == 28, "Follower diagnostic ABI");
static void *ptr(void *p, unsigned offset) { return *(void **)((u8 *)p + offset); }

/* These two native initialization paths already have the real manager's field.
 * Load the owned journal before either permission check, including cold boot. */
void *EnhancedFollowerField(void *manager) {
    void *field = NativeFollowerField(manager);
    EnhancedSettingsEnsure(field);
    return field;
}
int EnhancedFollowerPermission(int species, u32 map) {
    if (gEnhancedExtraOptions.hide_follower == 1) {
        ++gFollowerState.blocked;
        return 0;
    }
    return NativeFollowerPermission(species, map);
}

void EnhancedFollowerUpdate(void *field) {
    void *manager = ptr(field, 0x3C);
    u32 hidden = gEnhancedExtraOptions.hide_follower == 1;
    int previous = gFollowerState.known && gFollowerState.field == field &&
        gFollowerState.manager == manager;
    if (previous && gFollowerState.hidden == hidden) return;
    /* Native initialization has already applied the permission gate. Default On
     * must not invent an extra follower in a native forbidden/script context. */
    if (!previous && !hidden) goto settled;
    if (!manager || !ptr(field, 0x44) || !ptr(field, 0x40) ||
        !FieldMovementAllowed(field) || ptr(field, 0x10)) return;
    u8 *bytes = field;
    u32 avatar_state = *(u32 *)((u8 *)ptr(field, 0x40) + 0x18);
    if (avatar_state > 3) return;
    if (hidden) {
        if (bytes[0xFA]) {
            bytes[0xF9] = 1;
            NativeFollowerRefresh(field);
            if (!bytes[0xFA]) ++gFollowerState.removed;
        }
    } else if (!bytes[0xFA] && NativePartyAlive(SaveArray_Party_Get(ptr(field, 12)))) {
        bytes[0xF9] = 1;
        NativeFollowerRefresh(field);
        if (bytes[0xFA]) ++gFollowerState.restored;
    }
settled:
    gFollowerState.field = field;
    gFollowerState.manager = manager;
    gFollowerState.known = 1;
    gFollowerState.hidden = hidden;
}
