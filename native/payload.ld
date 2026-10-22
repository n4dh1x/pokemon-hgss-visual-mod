ENTRY(EnhancedEvolution)
SECTIONS {
    . = 0x01FF9000;
    .enhanced_config : { KEEP(*(.enhanced_config)) }
    ASSERT(SIZEOF(.enhanced_config) == 32, "Enhanced options ABI changed")
    . = 0x01FF9020;
    .trampoline : { KEEP(*(.evo_trampoline)) }
    ASSERT(SIZEOF(.trampoline) == 32, "Evolution trampoline ABI changed")
    . = 0x01FF9040;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss : { *(.bss .bss.* COMMON) }
    . = ALIGN(4);
    __enhanced_end = .;
    ASSERT(__enhanced_end <= 0x02000000, "Enhanced payload exceeds ITCM")
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment) *(.note*) *(.eh_frame*) }
}
GetMonData = 0x0206E541;
GetItemAttr = 0x02077D89;
LoadMonEvolutionTable = 0x020725C9;
OriginalFieldInput = 0x021E6AF5;
OriginalFieldControl = 0x0203E15D;
FieldMovementAllowed = 0x0203E13D;
OriginalStepEncounter = 0x02246C8D;
OriginalEncounterRoll = 0x02247569;
OriginalRoamerCheck = 0x02248361;
OriginalStartEncounter = 0x02050B09;
OriginalStartScript = 0x0203FE75;
OriginalObjectIterator = 0x0205EEF5;
Heap_FreeExplicit = 0x0201AB81;
SaveArray_Party_Get = 0x02074905;
Party_GetCount = 0x02074641;
Party_GetMonByIndex = 0x02074645;
MonIsShiny = 0x0207003D;
MapHeader_HasWildEncounters = 0x0203B325;
Save_VarsFlags_Get = 0x020503D1;
CheckPartner = 0x02066645;
CheckSafari = 0x02066861;
CheckContest = 0x02066871;
CheckPalPark = 0x020668A1;
GetMetatileBehavior = 0x02054919;
TerrainBlocked = 0x020548C1;
ObjectCollision = 0x02060BFD;
MovementBlocked = 0x020549F5;
MovementFinished = 0x02062199;
ClearMovementIfFinished = 0x020621C1;
SetHeldMovement = 0x0206214D;
LCRandom = 0x0201FD45;
CreateObject = 0x0205E1D1;
MapObject_Remove = 0x0205E3CD;
FollowMon_GetSpriteID = 0x02069D71;
FollowMon_SetObjectParams = 0x02069EE9;
SetPokemonHidden = 0x02069DC9;
BattleSetup_New = 0x020518D9;
BattleSetup_InitFromFieldSystem = 0x02051F01;
BattleSetup_Delete = 0x02051BF9;
BattleSetup_AddMonToParty = 0x02051C9D;
