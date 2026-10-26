"""Selective world-clock routes; original RTC/calendar routines remain intact."""
from dataclasses import replace as rename
import struct
import ndspy.code
from .field import fingerprint,replace,thumb_call,OverlayPatch

# Verified native world-time consumers. Native RTC bodies are never replaced.
MAIN_CALLS = (
    (0x020555EA, 0x02014845, 'EnhancedClockDayByHour'),
    (0x020555FA, 0x0201485D, 'EnhancedClockWildByHour'),
    (0x02055F56, 0x0201481D, 'EnhancedClockDay'),
    (0x02054FAE, 0x02014805, 'EnhancedClockNight'),
    (0x02070F82, 0x02014805, 'EnhancedClockNight'),
    (0x02070F98, 0x02014805, 'EnhancedClockNight'),
    (0x02071096, 0x02014805, 'EnhancedClockNight'),
    (0x020710AE, 0x02014805, 'EnhancedClockNight'),
)
OVERLAY_CALLS = {
    1: [
        (0x021EA24C, 0x020147A5, 'EnhancedClockSeconds'),
        (0x021EA2AE, 0x020147A5, 'EnhancedClockSeconds'),
        (0x021EA6E2, 0x020147A5, 'EnhancedClockSeconds'),
        (0x021FD4FA, 0x0201481D, 'EnhancedClockDay'),
        (0x02204758, 0x0201481D, 'EnhancedClockDay'),
        (0x022047E0, 0x0201481D, 'EnhancedClockDay'),
        (0x021F43F2, 0x020273F1, 'EnhancedClockSave'),
    ],
    2: [
        (0x02246A8A, 0x0201481D, 'EnhancedClockDay'),
        (0x02246ADC, 0x0201481D, 'EnhancedClockDay'),
        (0x02247DC2, 0x02014831, 'EnhancedClockWild'),
    ],
    17: [
        (0x02202416, 0x02201611, 'EnhancedClockPlant'),
        (0x02201F0E, 0x022037C9, 'EnhancedClockBerry'),
        (0x02202598, 0x022037C9, 'EnhancedClockBerry'),
    ],
    101: [
        (0x021EA996, 0x02014831, 'EnhancedClockWild'),
    ],
}
MAIN_CONTEXTS = (
    (0x02014708, 0x174, 'ddae15a5653dfa307b234e9c816a71e1d3874e3d792ff20cd4c5466b83a481ce'),
    (0x020555E0, 0x20, '187ad5d0869ac26e05586bf0e44c0a660db2af298db0d26d6687c082366a4aac'),
    (0x02055618, 0xC, '337571a29058b18666409b00246a64df2d144e02a30141f11c2ec5951291a12e'),
    (0x02055F30, 0x40, '088afac0f66e6276e30591052604bdcaebeeee593fd11036ecb485cc7424c6c0'),
    (0x02054F90, 0x40, 'e61d2a8a7411d67e0f241891e5f2098764af33e43fc07aade11aefd7bf516387'),
    (0x02070E44, 0x40C, 'c0412f140414d44eec38bec4f5a85c41992719ffb959f45864381b6a93c178f3'),
    (0x0201D8C8, 0x1C, '3a01fd1477c80528d08efea0c3243f21a0b514f9ecf91e41d200521f46088d18'),
    (0x020504F0, 0x20, '9c1c6f1298a3b7bea9b8d246d314951f068db195749451f3d62752337a6964b9'),
    (0x020504C0, 0x30, 'e3112710225d29b77cedfb833204b4d2335c39347c56708a6fb9066bfd9ada3d'),
)
OVERLAY_CONTEXTS = (
    (17, 0x0220240E, 0x14, '26f8d95d15fa40a7bac43f2f476ed95f51647ad0e05c4546d0cc2e126310834f'),
    (1, 0x021EA244, 0x14, 'd68070f5c1b78d2f606f0bd0f4da74a5e0abed69e735db91bc0c465f5fe97c3c'),
    (1, 0x021EA2A6, 0x14, '5b7fa63ea306b6675951d3554be7a8927d0e182a2bc2b7eb1764ec4a7e6ceb26'),
    (1, 0x021EA6DA, 0x14, 'dd4c841e44b399644a4da32ac91eccd726367d09bf423d03cec12c970e1f7e8c'),
    (1, 0x021FD4F2, 0x14, '3d252f82edc51ba5563d561b13307bad406e757e0f4100dc4646edb6854cba60'),
    (1, 0x02204750, 0x14, 'a8c1684ec83fb5e077c89bcca13a742306521ae0399631274d48bae2fde0da14'),
    (1, 0x022047D8, 0x14, 'f16aa69e85ba6519cd0d60ec29d4dabffc591a749d65a7cb68f3ffffc3328c6f'),
    (1, 0x021F43EA, 0x14, '842fbf73ce2a8815675d73c26c013be3a57e32b9ed92e17cfa6ccf92f0b4c79b'),
    (2, 0x02246A82, 0x14, '3071006136c0c960f9948d9663dc51b9a7cc016e63262685111482fd184dfaa4'),
    (2, 0x02246AD4, 0x14, '04ef317429b6706552fb884eaf59f832d029244aba48d6ef881606867d982507'),
    (2, 0x02247DBA, 0x14, '1b523311291b7b460c801815cac025ab52f4ed378e4f2390b9afd63dde4c00d7'),
    (17, 0x02201F06, 0x14, 'bc707bdb2f852ae87adaadffe3da4e6f4c05953e4dc24b095458507fc7a71366'),
    (17, 0x02202590, 0x14, 'bb2fbfc50d45f175971a73c0985852af379d36375de477d2eb94abf78fe75d75'),
    (101, 0x021EA98E, 0x14, 'd78eae49e192ecfac32b80d656a597be013ab1f7bf62027a1a44f0c4ed5ad5ff'),
    (17, 0x022037C8, 0xB4, '06358faebfd02cd3d15ee395ad74e638dc0f20232ac41bf4a621fce2688558b7'),
)

def install_clock(rom,payload):
    arm=bytearray(rom.arm9);base=rom.arm9RamAddress;main=[]
    for a,n,digest in MAIN_CONTEXTS:fingerprint(arm,base,a,n,digest)
    for site,target,symbol in MAIN_CALLS:
        main.append(rename(replace(arm,base,site,thumb_call(site,target),
            thumb_call(site,payload.symbols[symbol]),symbol),feature='world_clock'))
    # Whole 12-byte native field-hour getter; a legal Thumb tail branch only
    # clobbers caller-saved r3. Its native-calendar fallback is retained in C.
    site=0x02055618
    original=bytes(arm[site-base:site-base+8])
    branch=bytes.fromhex('004b1847')+struct.pack('<I',payload.symbols['EnhancedClockFieldHour'])
    main.append(rename(replace(arm,base,site,original,branch,'EnhancedClockFieldHour'),feature='world_clock'))
    site=0x020504F0
    original=bytes(arm[site-base:site-base+8])
    branch=bytes.fromhex('004b1847')+struct.pack('<I',payload.symbols['EnhancedClockCreateTask'])
    main.append(rename(replace(arm,base,site,original,branch,'Close owned clock HUD before native task creation'),feature='clock_hud'))
    overlays=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid],set(OVERLAY_CALLS))
    for oid,a,n,digest in OVERLAY_CONTEXTS:fingerprint(overlays[oid].data,overlays[oid].ramAddress,a,n,digest)
    changes=[];table=bytearray(rom.arm9OverlayTable)
    for oid,calls in OVERLAY_CALLS.items():
        o=overlays[oid]
        for site,target,symbol in calls:
            patch=rename(replace(o.data,o.ramAddress,site,thumb_call(site,target),
                thumb_call(site,payload.symbols[symbol]),symbol),feature='world_clock')
            changes.append(OverlayPatch(oid,o.fileID,patch))
        rom.files[o.fileID]=o.save(compress=False)
        for at in range(0,len(table),32):
            if struct.unpack_from('<I',table,at)[0]==oid:
                table[at:at+32]=ndspy.code.saveOverlayTable({oid:o});break
        else:raise ValueError(f'Clock overlay descriptor {oid} is missing.')
    rom.arm9=bytes(arm);rom.arm9OverlayTable=bytes(table)
    return main,changes
