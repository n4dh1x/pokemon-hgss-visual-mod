#include "settings.h"

extern u32 LCRandom(void);
extern u32 NativeNatureFromPid(u32 pid);
extern u32 NativeMonBaseStat(u32 species, u32 stat);
extern void NativeCreateMon(void *, int, int, int, int, u32, int, u32);

struct ShinyState {
    u32 calls, rolls, candidates, changes, failures;
    u32 original_pid, selected_pid, owner, species, kind;
};
struct ShinyState gShinyState;
_Static_assert(sizeof(struct ShinyState) == 40, "Shiny diagnostic ABI");

static int shiny(u32 pid, u32 owner) {
    return ((pid & 65535) ^ (pid >> 16) ^ (owner & 65535) ^ (owner >> 16)) < 8;
}
static u32 random_pid(void) {
    u32 lo = LCRandom();
    return lo | (LCRandom() << 16);
}
static u32 gender(u32 pid, u32 ratio) {
    if (!ratio) return 0;
    if (ratio == 254) return 1;
    if (ratio == 255) return 2;
    return (pid & 255) < ratio;
}
static u32 letter(u32 pid) {
    u32 value = ((pid >> 18) & 192) | ((pid >> 12) & 48) |
                ((pid >> 6) & 12) | (pid & 3);
    while (value >= 28) value -= 28;
    return value;
}
static int matches(u32 pid, u32 original, u32 kind, u32 nature, u32 ratio, u32 species) {
    if (kind && NativeNatureFromPid(pid) != nature) return 0;
    if (kind == 2 && gender(pid, ratio) != gender(original, ratio)) return 0;
    return kind != 2 || species != 201 || letter(pid) == letter(original);
}
u32 EnhancedShinySelect(u32 original, u32 owner, u32 species, u32 kind) {
    static const u16 rolls[6] = {1, 2, 8, 32, 128, 0};
    u32 setting = gEnhancedExtraOptions.shiny_odds;
    if (!setting || setting > 5 || kind > 2) return original;
    ++gShinyState.calls;
    ++gShinyState.rolls;
    gShinyState.original_pid = original;
    gShinyState.owner = owner;
    gShinyState.species = species;
    gShinyState.kind = kind;
    u32 selected = original;
    if (!shiny(original, owner)) {
        u32 nature = kind ? NativeNatureFromPid(original) : 0;
        u32 ratio = kind == 2 ? NativeMonBaseStat(species, 18) : 0;
        if (setting == 5) {
            /* Enumerate the entire shiny PID space from a random low half and
             * XOR offset. Finite even with a stuck RNG; native shiny check stays
             * <8. Nature/gender/explicit Unown-letter constraints are retained. */
            u32 base = LCRandom(), salt = LCRandom() & 7;
            for (u32 i = 0; i < 524288; ++i) {
                u32 lo = (base + (i >> 3)) & 65535;
                u32 hi = (owner & 65535) ^ (owner >> 16) ^ lo ^ ((salt + i) & 7);
                u32 candidate = lo | (hi << 16);
                ++gShinyState.candidates;
                if (matches(candidate, original, kind, nature, ratio, species)) {
                    selected = candidate;
                    break;
                }
            }
            if (selected == original) ++gShinyState.failures;
        } else {
            for (u32 i = 1; i < rolls[setting]; ++i) {
                do {
                    selected = random_pid();
                    ++gShinyState.candidates;
                } while (!matches(selected, original, kind, nature, ratio, species));
                ++gShinyState.rolls;
                if (shiny(selected, owner)) break;
            }
        }
    }
    if (selected != original) ++gShinyState.changes;
    gShinyState.selected_pid = selected;
    return selected;
}
static int enabled(u32 *owner) {
    u32 setting = gEnhancedExtraOptions.shiny_odds;
    return setting && setting <= 5 && EnhancedSettingsOwner(owner);
}
void EnhancedPlayerCreateMon(void *mon, int species, int level, int iv, int fixed, u32 pid, int ot_type, u32 ot_id) {
    u32 owner;
    if (!fixed && !ot_type && enabled(&owner)) {
        pid = EnhancedShinySelect(random_pid(), owner, (u32)species, 0);
        fixed = 1;
    }
    NativeCreateMon(mon, species, level, iv, fixed, pid, ot_type, ot_id);
}
static void wild(void *mon, int species, int level, int iv, int fixed, u32 pid, int ot_type, u32 ot_id, u32 kind) {
    u32 owner;
    if (fixed == 1 && !ot_type && enabled(&owner))
        pid = EnhancedShinySelect(pid, owner, (u32)species, kind);
    NativeCreateMon(mon, species, level, iv, fixed, pid, ot_type, ot_id);
}
void EnhancedNatureCreateMon(void *mon, int species, int level, int iv, int fixed, u32 pid, int ot_type, u32 ot_id) {
    wild(mon, species, level, iv, fixed, pid, ot_type, ot_id, 1);
}
void EnhancedGenderCreateMon(void *mon, int species, int level, int iv, int fixed, u32 pid, int ot_type, u32 ot_id) {
    wild(mon, species, level, iv, fixed, pid, ot_type, ot_id, 2);
}
