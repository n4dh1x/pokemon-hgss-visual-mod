#include "camera.h"
#include "settings.h"
struct CameraAngle { u16 x, y, z, unused; };
extern void NativeCameraAngle(const struct CameraAngle *angle, void *camera);
extern void NativeCameraDistance(s32 distance, void *camera);
extern void NativeCameraProjection(u32 type, void *camera);
extern void NativeCameraDelete(void *camera);
extern int FieldMovementAllowed(void *field);
extern u32 NativeNormalMenuInhibitFlags(void *field);
extern u32 EnhancedUnsignedDivide(u32 numerator, u32 denominator);
struct CameraState {
    void *field, *manager, *camera;
    struct CameraAngle base_angle, applied_angle;
    s32 base_distance, applied_distance;
    u32 active, updates, restored, deferred, replaced, projection_pending;
};
struct CameraState gCameraState;
_Static_assert(sizeof(struct CameraState) == 60, "Camera diagnostic ABI");
static void *ptr(void *p, u32 n) { return *(void **)((u8 *)p + n); }
static u32 word(void *p, u32 n) { return *(u32 *)((u8 *)p + n); }
static struct CameraAngle angle(void *camera) { return *(struct CameraAngle *)((u8 *)camera + 60); }
static int same(struct CameraAngle a, struct CameraAngle b) {
    return a.x == b.x && a.y == b.y && a.z == b.z && a.unused == b.unused;
}
static int bounded(void *p, u32 size) { return (u32)p >= 0x02000000 && (u32)p <= 0x02400000 - size; }
static void forget(void) {
    gCameraState.field = gCameraState.manager = gCameraState.camera = 0;
    gCameraState.active = gCameraState.projection_pending = 0;
}
static void distance(s32 value, void *camera) {
    NativeCameraDistance(value, camera);
    if (*((u8 *)camera + 68) == 1) {
        /* Ortho width depends on distance. Refresh only the active projection;
         * another native camera may own global graphics during a cutscene. */
        if (*(void * volatile *)0x021D2204 == camera) {
            NativeCameraProjection(1, camera);
            gCameraState.projection_pending = 0;
        } else gCameraState.projection_pending = 1;
    }
}
void EnhancedCameraSuspend(void *field) {
    if (!gCameraState.active || gCameraState.field != field ||
        ptr(field, 0x24) != gCameraState.camera) return;
    void *camera = gCameraState.camera;
    /* Restore only parameters still owned by our last application. A native
     * script/controller may already have changed either component. */
    if (same(angle(camera), gCameraState.applied_angle) &&
        !same(gCameraState.base_angle, gCameraState.applied_angle))
        NativeCameraAngle(&gCameraState.base_angle, camera);
    if (word(camera, 56) == (u32)gCameraState.applied_distance &&
        gCameraState.base_distance != gCameraState.applied_distance)
        distance(gCameraState.base_distance, camera);
    gCameraState.active = 0;
    ++gCameraState.restored;
}
void EnhancedCameraForget(void *manager) {
    if (gCameraState.manager == manager) forget();
}
void EnhancedCameraDelete(void *camera) {
    if (gCameraState.camera == camera) forget();
    NativeCameraDelete(camera);
}
void EnhancedCameraUpdate(void *field) {
    void *camera = ptr(field, 0x24), *controller = ptr(field, 0x28);
    u32 owner;
    if (!bounded(camera, 104) || !bounded(controller, 52) ||
        !ptr(field, 0x3C) || !ptr(field, 0x44) || ptr(field, 0x10) ||
        *(void * volatile *)0x021D2204 != camera || word(controller, 0) != (u32)camera ||
        word(controller, 0x28) || !FieldMovementAllowed(field) ||
        (NativeNormalMenuInhibitFlags(field) & 4) || !EnhancedSettingsOwner(&owner)) {
        EnhancedCameraSuspend(field);
        ++gCameraState.deferred;
        return;
    }
    if (gCameraState.camera == camera && gCameraState.projection_pending) {
        NativeCameraProjection(*((u8 *)camera + 68), camera);
        gCameraState.projection_pending = 0;
    }
    u32 pitch = gEnhancedExtraOptions.camera_pitch, zoom = gEnhancedExtraOptions.camera_zoom;
    if (pitch > 5 || zoom > 3) { EnhancedCameraSuspend(field); return; }
    if (gCameraState.active && (gCameraState.field != field || gCameraState.camera != camera ||
        gCameraState.manager != ptr(field, 0x3C))) forget();
    if (gCameraState.active && (!same(angle(camera), gCameraState.applied_angle) ||
        word(camera, 56) != (u32)gCameraState.applied_distance)) {
        EnhancedCameraSuspend(field);
        ++gCameraState.replaced;
    }
    if (!gCameraState.active) {
        if (gCameraState.camera != camera) gCameraState.projection_pending = 0;
        gCameraState.field = field;
        gCameraState.manager = ptr(field, 0x3C);
        gCameraState.camera = camera;
        gCameraState.base_angle = angle(camera);
        gCameraState.base_distance = (s32)word(camera, 56);
    }
    if (!pitch && zoom == 1) { EnhancedCameraSuspend(field); return; }
    s32 base = gCameraState.base_distance;
    if (base <= 0 || base > 0x02000000) { EnhancedCameraSuspend(field); return; }
    struct CameraAngle selected = gCameraState.base_angle;
    static const u16 pitches[6] = {0, 59346, 58800, 58254, 57708, 57162};
    static const u32 zooms[4] = {90, 100, 110, 120};
    if (pitch) selected.x = pitches[pitch];
    s32 selected_distance = (s32)EnhancedUnsignedDivide((u32)base * 100, zooms[zoom]);
    int changed = 0;
    if (!same(angle(camera), selected)) { NativeCameraAngle(&selected, camera); changed = 1; }
    if (word(camera, 56) != (u32)selected_distance) { distance(selected_distance, camera); changed = 1; }
    gCameraState.applied_angle = selected;
    gCameraState.applied_distance = selected_distance;
    gCameraState.active = 1;
    if (changed) ++gCameraState.updates;
}
