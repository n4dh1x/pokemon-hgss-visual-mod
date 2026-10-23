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
FlashLoadChunk = 0x0202877D;
FlashWriteChunk = 0x02028759;
Save_PlayerData_GetProfile = 0x02028E9D;
PlayerProfile_GetTrainerID = 0x02028F85;
Sys_SetSleepDisableFlag = 0x0201A4BD;
Sys_ClearSleepDisableFlag = 0x0201A4CD;
FieldSystem_CreateTask = 0x020504F1;
String_New = 0x02026355;
String_Delete = 0x02026381;
CopyU16ArrayToString = 0x020269A1;
AddWindowParameterized = 0x0201D40D;
FillWindowPixelBuffer = 0x0201D979;
CopyWindowToVram = 0x0201D579;
RemoveWindow = 0x0201D521;
LoadUserFrameGfx1 = 0x0200E3DD;
DrawFrameAndWindow1 = 0x0200E581;
ClearFrameAndWindow1 = 0x0200E5D5;
AddTextPrinterParameterizedWithColor = 0x020200FD;
FieldDrawMapName_Reset = 0x021EFACD;
Bag_TakeItem = 0x02078435;
Save_Roamers_Get = 0x0202D9C5;
RoamerSave_RepelNotInUse = 0x0202DB09;
Save_Bag_Get = 0x0207879D;
Bag_HasItem = 0x020784B1;
PlaySE = 0x0200604D;
FieldSystem_MapIsBattleTowerMultiPartnerSelectRoom = 0x02067585;
NativeNormalMenuInhibitFlags = 0x0203BE61;

NativeCaptureTask = 0x022465A9;
NativeExperienceTask = 0x02245899;
NativeCalcExperience = 0x0223E6A1;
BattleSystem_GetBattleType = 0x0223A7E1;
BattleSystem_GetParty = 0x0223A7F5;
Heap_Alloc = 0x0201AA8D;
Heap_Free = 0x0201AB0D;
SysTask_CreateOnMainQueue = 0x0200E321;
NativeBallAnimationActive = 0x02232F61;

BattleSystem_GetOpponentData = 0x0223A7E9;
GetMonBaseStat = 0x0206FBE9;
NativeScriptReadWord = 0x022454E9;
NativeScriptIncrement = 0x02245509;
NativePrintBattleMessage = 0x0223C495;
NativeUnsignedDivide = 0x020F2BA4;

NativePartySlotWithMove = 0x0204D3CD;
NativeFirstPartyMove = 0x020542E9;
ScriptReadHalfword = 0x0203FE2D;
GetVarPointer = 0x02040375;
FieldSystem_VarGet = 0x020403AD;
GetMonTMHMCompat = 0x0207224D;


NativeBagDrawContext = 0x021FEB85;
NativeBagSetCancel = 0x021FD789;
NativeBagHideCursor = 0x021FFF25;
NativeBagCancelContext = 0x021FB605;
NativeBagPrintMessage = 0x021FEF49;
NativeBagCreateYesNo = 0x021FF005;
NativeBagDestroyYesNo = 0x021FF059;
NativeYesNoInput = 0x020168F5;
NativeTextPrinterActive = 0x02020095;
NativeAppFade = 0x020880CD;
NativeFieldMoveFunction = 0x02067DF5;
NativeTaskField = 0x0205064D;
NativeTaskEnvironment = 0x02050651;
NativeItemUseTMHM = 0x02064E19;
NativeReopenBag = 0x0203E3FD;
NativeStartMenuExit = 0x0203C8F1;
NativeBagReturn = 0x0203CFC1;

NativeFlyReturn = 0x0203D759;


NativeSummaryInput = 0x02088B41;
NativeSummaryDrawStats = 0x0208D179;
NativeSummaryMon = 0x0208A521;
NativeSummaryNumber = 0x0208C87D;
NativeSummaryPrint = 0x0208C779;
GetBoxMonData = 0x0206E641;

NativeCreateMon = 0x0206DE39;
NativeNatureFromPid = 0x0206FE2D;
NativeMonBaseStat = 0x0206FBE9;

NativeMapObjectId = 0x0205F24D;

NativeFieldSparkle = 0x021FE66D;

NativeEncounterTile = 0x0205B995;
NativeSurfableTile = 0x0205B779;
