# Saved native camera angle and zoom

Press SELECT, then X twice for page 3. Camera angle offers Visual+, 34, 37, 40,
43 and 46 degrees. Camera zoom offers 90%, 100%, 110% and 120%; higher is closer.
Defaults are Visual+ and 100%, preserving the current map's original Visual+
parameters. Save and close applies all pages together. B/Cancel discards staged
changes. These controls adjust the native DS renderer and existing map geometry.

The custom view applies during normal field play. Opening a native task or menu
restores parameters still owned by the custom view, before the native task starts.
The custom view returns when free field input resumes. A busy native camera
controller, foreign active camera, unavailable renderer or changed trainer owner
defers application. Native changes to angle/distance become the new base after
the owned components are released; repeated updates do not compound zoom.

Pitch uses the original Camera_SetAnglePos path, retaining yaw/roll and the
current target. Zoom is a percentage of the current native base distance. Target,
up vector, history, tracking and map frustum remain under the original game.
Orthographic distance changes also rebuild the native projection; if another
camera owns global graphics, the projection refresh waits until the field camera
is active again. Camera deletion forgets the owned state before native freeing.

## Persistence and guarded integration

The version-1 256-byte journal remains unchanged. Slot 19/presence bit 4096 stores
pitch index 0..5; slot 20/bit 8192 stores zoom index 0..3. Missing fields ignore
legacy padding and default to Visual+/100%. Unknown later slots and reserved
bits survive. Readback must succeed before either runtime option changes.

The third page now has four options: World clock, Show clock, Camera angle and
Camera zoom. It skips two unused rows before Save/Cancel. The runtime auxiliary
structure is 40 bytes, menu state 116 bytes and camera diagnostics 60 bytes;
the fixed loader header remains 32 bytes. One checked overlay-1 call forwards
native camera deletion. Native camera math, angle/distance/projection functions,
constructor/controller bodies and static-camera pointer access are fingerprinted
independently in both USA baselines.

## Verification and limits

216 tests pass. Ten camera cases execute original native geometry/math, the
patched native field-camera deletion body, all pitch/zoom combinations, default
no-write behavior, non-accumulating updates, task handoff, native edits, controller
and ownership deferral. The orthographic case executes the original projection
routine with controlled division and projection-output APIs, checking scaled
bounds, restoration and foreign-camera deferral. Three journal/menu cases add
all 24 combinations, legacy padding, unknown-field retention, invalid bounds,
Cancel, failed writes and retry.

Both exact candidate ROMs reproduce the tested experiments and pass xdelta
round trips. Mac melonDS DS 1.3.1 shows HeartGold at 34/110% and SoulSilver at
46/90%, native walking into and out of Elm's Lab, party/menu handoff, native
saving and cold reload. Reset restores each map's Visual+ parameters. Cancel
preserves the whole cartridge save, and strict native party getters verify
unchanged identities/rewards. No new RAM fixtures are used.

Visual+ makes both tested outdoor profile 0 and lab profile 4 perspective views,
with matching base parameters. The indoor transition therefore verifies the
actual Visual+ perspective path. Runtime orthographic fields, wider maps and
culling, story/legendary cinematics, Surf/cycling, moving wilds under every view
and long-session acceptance remain pending. Source and instruction evidence is
not presented as complete gameplay coverage. SoulSilver uses HG-derived project
progress. These are experimental builds; the full enhancement goal is unfinished.
See [exact evidence](../enhancements/milestone-22-verification.json).
